"""RAG Engine using LlamaIndex and ChromaDB."""

import os
import json
from typing import List, Optional, Dict, Any
from pathlib import Path

from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, Settings, StorageContext
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.llms.anthropic import Anthropic
from llama_index.llms.anthropic import utils as anthropic_utils
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.core.schema import TextNode
import chromadb

# Monkey-patch to support newer Claude models
_original_contextsize = anthropic_utils.anthropic_modelname_to_contextsize

def _patched_contextsize(modelname: str) -> int:
    """Patched version that supports newer Claude models."""
    if modelname.startswith("claude-sonnet-4"):
        return 200000  # Claude Sonnet 4 context window
    if modelname.startswith("claude-opus-4"):
        return 200000  # Claude Opus 4 context window
    return _original_contextsize(modelname)

# Patch in both the utils module and anywhere it's imported
anthropic_utils.anthropic_modelname_to_contextsize = _patched_contextsize
# Also patch in the base module where it's actually called
from llama_index.llms.anthropic import base as anthropic_base
anthropic_base.anthropic_modelname_to_contextsize = _patched_contextsize

from config import (
    ANTHROPIC_API_KEY,
    ANTHROPIC_MODEL,
    OPENAI_API_KEY,
    EMBEDDING_MODEL,
    CHROMA_PERSIST_DIR,
    LLM_TEMPERATURE,
    LLM_MAX_TOKENS,
    TOP_K_RETRIEVAL,
    DATA_DIR,
)
from models import Source, Case, CaseSearchResult


class RAGEngine:
    """RAG Engine for document retrieval and query processing."""

    def __init__(self):
        """Initialize the RAG engine."""
        self.index = None
        self.query_engine = None
        self.chroma_client = None
        self.chroma_collection = None
        self._initialized = False

    def initialize(self):
        """Initialize LlamaIndex components and load existing index."""
        if self._initialized:
            return

        # Configure LlamaIndex settings
        Settings.llm = Anthropic(
            model=ANTHROPIC_MODEL,
            api_key=ANTHROPIC_API_KEY,
            temperature=LLM_TEMPERATURE,
            max_tokens=LLM_MAX_TOKENS,
        )
        Settings.embed_model = OpenAIEmbedding(
            model=EMBEDDING_MODEL,
            api_key=OPENAI_API_KEY,
        )

        # Initialize ChromaDB
        self.chroma_client = chromadb.PersistentClient(path=CHROMA_PERSIST_DIR)
        self.chroma_collection = self.chroma_client.get_or_create_collection(
            "forensic_cases"
        )

        # Create vector store
        vector_store = ChromaVectorStore(chroma_collection=self.chroma_collection)
        storage_context = StorageContext.from_defaults(vector_store=vector_store)

        # Create or load index
        try:
            # Try to load existing index from vector store
            self.index = VectorStoreIndex.from_vector_store(
                vector_store=vector_store,
            )
        except Exception:
            # If no documents exist, create empty index
            self.index = VectorStoreIndex(
                nodes=[],
                storage_context=storage_context,
            )

        # Create query engine
        self.query_engine = self.index.as_query_engine(
            similarity_top_k=TOP_K_RETRIEVAL,
        )

        self._initialized = True

    def query(self, query_text: str, case_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Query the RAG system.

        Args:
            query_text: The user's query
            case_id: Optional case ID to filter results

        Returns:
            Dictionary with answer, sources, and metadata
        """
        if not self._initialized:
            raise RuntimeError("RAG engine not initialized. Call initialize() first.")

        # Create query engine with optional filtering
        if case_id:
            from llama_index.core.vector_stores import MetadataFilters, ExactMatchFilter

            filters = MetadataFilters(
                filters=[ExactMatchFilter(key="case_id", value=case_id)]
            )
            query_engine = self.index.as_query_engine(
                similarity_top_k=TOP_K_RETRIEVAL,
                filters=filters,
            )
        else:
            query_engine = self.query_engine

        # Execute query
        import time
        start_time = time.time()
        response = query_engine.query(query_text)
        processing_time_ms = int((time.time() - start_time) * 1000)

        # Extract sources
        sources = []
        if hasattr(response, 'source_nodes'):
            for node in response.source_nodes:
                source = Source(
                    doc_id=node.metadata.get('file_name', 'unknown'),
                    snippet=node.text[:200] + "..." if len(node.text) > 200 else node.text,
                    relevance_score=node.score if hasattr(node, 'score') else 0.0,
                )
                sources.append(source)

        return {
            "answer": str(response),
            "sources": sources,
            "metadata": {
                "total_chunks_retrieved": len(sources),
                "processing_time_ms": processing_time_ms,
            }
        }

    def get_cases(self) -> List[Case]:
        """
        Get list of all available cases.

        Returns:
            List of Case objects
        """
        cases = []
        data_path = Path(DATA_DIR)

        if not data_path.exists():
            return cases

        # Iterate through case directories
        for case_dir in data_path.iterdir():
            if not case_dir.is_dir():
                continue

            # Try to load metadata.json
            metadata_file = case_dir / "metadata.json"
            if metadata_file.exists():
                try:
                    with open(metadata_file, 'r') as f:
                        metadata = json.load(f)

                    case = Case(
                        case_id=metadata.get('case_id', case_dir.name),
                        title=metadata.get('title', case_dir.name),
                        date=metadata.get('date', 'Unknown'),
                        document_count=len(metadata.get('documents', [])),
                    )
                    cases.append(case)
                except Exception as e:
                    # If metadata parsing fails, create basic case info
                    doc_count = len(list(case_dir.glob('*.*'))) - 1  # Exclude metadata.json
                    case = Case(
                        case_id=case_dir.name,
                        title=case_dir.name,
                        date='Unknown',
                        document_count=max(0, doc_count),
                    )
                    cases.append(case)
            else:
                # No metadata file, create basic case info
                doc_count = len(list(case_dir.glob('*.*')))
                case = Case(
                    case_id=case_dir.name,
                    title=case_dir.name,
                    date='Unknown',
                    document_count=doc_count,
                )
                cases.append(case)

        return cases

    def get_document_count(self) -> int:
        """Get the total number of documents in the vector store."""
        if not self._initialized or not self.chroma_collection:
            return 0

        try:
            return self.chroma_collection.count()
        except Exception:
            return 0

    def search_cases(self, description: str, top_k: int = 5) -> List[CaseSearchResult]:
        """
        Search cases by semantic similarity to description.

        Args:
            description: User's description of the case they're looking for
            top_k: Number of top results to return

        Returns:
            List of CaseSearchResult objects ranked by relevance
        """
        if not self._initialized:
            raise RuntimeError("RAG engine not initialized. Call initialize() first.")

        # Get embedding for user's description
        description_embedding = Settings.embed_model.get_text_embedding(description)

        # Query the vector store for similar chunks
        # We'll retrieve more chunks than needed to ensure we have enough cases
        query_results = self.chroma_collection.query(
            query_embeddings=[description_embedding],
            n_results=min(50, self.chroma_collection.count()),  # Get more results for deduplication
            include=['metadatas', 'documents', 'distances']
        )

        # Deduplicate by case_id and aggregate scores
        case_scores = {}
        case_texts = {}

        if query_results['ids'] and len(query_results['ids']) > 0:
            for i, metadata in enumerate(query_results['metadatas'][0]):
                case_id = metadata.get('case_id')
                if not case_id:
                    continue

                # Distance to similarity score (lower distance = higher similarity)
                # ChromaDB uses L2 distance, convert to similarity score (0-1)
                distance = query_results['distances'][0][i]
                similarity = 1.0 / (1.0 + distance)

                # Keep the highest similarity score for each case
                if case_id not in case_scores or similarity > case_scores[case_id]:
                    case_scores[case_id] = similarity
                    case_texts[case_id] = query_results['documents'][0][i]

        # Get case metadata for top scoring cases
        results = []
        sorted_cases = sorted(case_scores.items(), key=lambda x: x[1], reverse=True)[:top_k]

        data_path = Path(DATA_DIR)
        for case_id, score in sorted_cases:
            case_dir = data_path / case_id
            metadata_file = case_dir / "metadata.json"

            # Default values
            title = case_id
            summary = case_texts.get(case_id, "")[:300]  # Use chunk text as summary
            key_findings = []
            doc_count = 0

            # Try to load metadata
            if metadata_file.exists():
                try:
                    with open(metadata_file, 'r') as f:
                        metadata = json.load(f)

                    title = metadata.get('title', case_id)
                    summary = metadata.get('summary', summary)
                    key_findings = metadata.get('key_findings', [])
                    doc_count = len(metadata.get('documents', []))
                except Exception as e:
                    print(f"Error loading metadata for {case_id}: {e}")

            # Count documents if not in metadata
            if doc_count == 0 and case_dir.exists():
                doc_count = len(list(case_dir.glob('*.*'))) - 1  # Exclude metadata.json
                doc_count = max(0, doc_count)

            result = CaseSearchResult(
                case_id=case_id,
                title=title,
                relevance_score=round(score * 100, 1),  # Convert to percentage
                summary=summary,
                key_findings=key_findings[:5],  # Limit to 5 key findings
                document_count=doc_count,
            )
            results.append(result)

        return results

    def ingest_documents(self, case_dir: str, case_id: str,
                         metadata: Optional[Dict[str, Any]] = None,
                         force_reingest: bool = False):
        """
        Ingest documents from a case directory with duplicate detection.

        Args:
            case_dir: Path to the case directory
            case_id: Case identifier
            metadata: Optional metadata to attach to documents
            force_reingest: If True, re-ingest even if already ingested

        Returns:
            Dict with 'ingested' and 'skipped' counts
        """
        if not self._initialized:
            raise RuntimeError("RAG engine not initialized. Call initialize() first.")

        # Load or create manifest file for tracking ingested documents
        manifest_path = Path(case_dir).parent.parent / '.ingestion_manifest.json'
        manifest = {}
        if manifest_path.exists():
            try:
                with open(manifest_path, 'r') as f:
                    manifest = json.load(f)
            except Exception as e:
                print(f"Warning: Could not load manifest file: {e}")

        # Load documents from directory
        documents = SimpleDirectoryReader(
            input_dir=case_dir,
            required_exts=['.txt', '.pdf', '.docx'],
            recursive=False,
        ).load_data()

        ingested_count = 0
        skipped_count = 0

        for doc in documents:
            # Generate unique identifier for this document
            file_name = doc.metadata.get('file_name', 'unknown')
            doc_key = f"{case_id}_{file_name}"

            # Check if already ingested
            if doc_key in manifest and not force_reingest:
                print(f"  Skipping {file_name} (already ingested)")
                skipped_count += 1
                continue

            # Add metadata
            doc.metadata['case_id'] = case_id
            if metadata:
                doc.metadata.update(metadata)

            # Add document to index
            self.index.insert(doc)

            # Update manifest
            manifest[doc_key] = {
                'case_id': case_id,
                'file_name': file_name,
                'ingested_at': str(Path(case_dir))
            }

            ingested_count += 1
            print(f"  Ingested {file_name}")

        # Save updated manifest
        try:
            manifest_path.parent.mkdir(parents=True, exist_ok=True)
            with open(manifest_path, 'w') as f:
                json.dump(manifest, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save manifest file: {e}")

        return {'ingested': ingested_count, 'skipped': skipped_count}

    def clear_all_documents(self):
        """Clear all documents from the vector store."""
        if not self._initialized:
            raise RuntimeError("RAG engine not initialized.")

        try:
            # Delete the collection
            self.chroma_client.delete_collection("forensic_cases")

            # Recreate empty collection
            self.chroma_collection = self.chroma_client.create_collection(
                "forensic_cases"
            )

            # Create vector store and index
            from llama_index.vector_stores.chroma import ChromaVectorStore
            from llama_index.core import StorageContext

            vector_store = ChromaVectorStore(chroma_collection=self.chroma_collection)
            storage_context = StorageContext.from_defaults(vector_store=vector_store)

            self.index = VectorStoreIndex(
                nodes=[],
                storage_context=storage_context,
            )
            self.query_engine = self.index.as_query_engine(
                similarity_top_k=TOP_K_RETRIEVAL,
            )

            # Also clear the manifest file
            manifest_path = Path(DATA_DIR) / '.ingestion_manifest.json'
            if manifest_path.exists():
                manifest_path.unlink()

            print("Successfully cleared all documents from vector store")
            return True
        except Exception as e:
            print(f"Error clearing documents: {e}")
            return False

    def clear_case_documents(self, case_id: str):
        """
        Clear all documents for a specific case.

        Note: This is a simplified version that clears the manifest entry.
        For full removal, a complete re-ingestion after clearing is recommended.
        """
        if not self._initialized:
            raise RuntimeError("RAG engine not initialized.")

        try:
            # Remove from manifest
            manifest_path = Path(DATA_DIR) / '.ingestion_manifest.json'
            if manifest_path.exists():
                with open(manifest_path, 'r') as f:
                    manifest = json.load(f)

                # Remove entries for this case
                keys_to_remove = [k for k in manifest.keys() if k.startswith(f"{case_id}_")]
                for key in keys_to_remove:
                    del manifest[key]

                # Save updated manifest
                with open(manifest_path, 'w') as f:
                    json.dump(manifest, f, indent=2)

                print(f"Cleared {len(keys_to_remove)} document entries for {case_id} from manifest")
                print("Note: For complete removal, run: python ingest.py --clear && python ingest.py")
                return len(keys_to_remove)
            else:
                print("No manifest file found")
                return 0
        except Exception as e:
            print(f"Error clearing case {case_id}: {e}")
            return 0
