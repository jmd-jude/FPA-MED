"""Document ingestion script for loading case files into ChromaDB."""

import os
import sys
import argparse
import logging
from pathlib import Path
from typing import List

from rag_engine import RAGEngine
from config import DATA_DIR
from case_schema import validate_case_directory

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description='Ingest forensic psychiatry case documents into the RAG system.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python ingest.py                    # Ingest all cases, skip duplicates
  python ingest.py --case case_003    # Ingest only case_003
  python ingest.py --force            # Re-ingest all cases
  python ingest.py --clear            # Clear database, then ingest all
  python ingest.py --case case_003 --force  # Force re-ingest case_003
        """
    )

    parser.add_argument(
        '--case',
        type=str,
        help='Ingest only the specified case (e.g., case_003)',
        metavar='CASE_ID'
    )

    parser.add_argument(
        '--force',
        action='store_true',
        help='Force re-ingestion of cases even if already ingested'
    )

    parser.add_argument(
        '--clear',
        action='store_true',
        help='Clear all documents from vector store before ingesting'
    )

    parser.add_argument(
        '--validate-only',
        action='store_true',
        help='Only validate case directories without ingesting'
    )

    return parser.parse_args()


def get_case_directories(data_path: Path, case_filter: str = None) -> List[Path]:
    """
    Get list of case directories to process.

    Args:
        data_path: Path to data directory
        case_filter: Optional case_id to filter by

    Returns:
        List of case directory paths
    """
    if case_filter:
        # Process only specified case
        case_dir = data_path / case_filter
        if not case_dir.exists():
            logger.error(f"Case directory not found: {case_dir}")
            return []
        if not case_dir.is_dir():
            logger.error(f"Path is not a directory: {case_dir}")
            return []
        return [case_dir]
    else:
        # Process all case directories
        return [d for d in data_path.iterdir() if d.is_dir()]


def validate_cases(case_dirs: List[Path]) -> List[Path]:
    """
    Validate case directories and return list of valid cases.

    Args:
        case_dirs: List of case directory paths

    Returns:
        List of valid case directory paths
    """
    valid_cases = []

    for case_dir in case_dirs:
        case_id = case_dir.name
        logger.info(f"Validating case: {case_id}")

        is_valid, errors = validate_case_directory(case_dir, case_id)

        if is_valid:
            logger.info(f"  ✓ Valid case structure")
            valid_cases.append(case_dir)
        else:
            logger.error(f"  ✗ Validation failed:")
            for error in errors:
                logger.error(f"    - {error}")

    return valid_cases


def ingest_cases(rag_engine: RAGEngine, case_dirs: List[Path], force_reingest: bool = False):
    """
    Ingest case documents into the RAG system.

    Args:
        rag_engine: Initialized RAG engine
        case_dirs: List of case directory paths
        force_reingest: Whether to force re-ingestion
    """
    total_ingested = 0
    total_skipped = 0
    successful_cases = 0
    failed_cases = 0

    for case_dir in case_dirs:
        case_id = case_dir.name
        logger.info(f"Processing case: {case_id}")

        # Check for documents
        documents = (
            list(case_dir.glob('*.txt')) +
            list(case_dir.glob('*.pdf')) +
            list(case_dir.glob('*.docx'))
        )
        # Exclude metadata.json from document count
        documents = [d for d in documents if d.name != 'metadata.json']

        if not documents:
            logger.warning(f"  No documents found in {case_id}, skipping...")
            continue

        logger.info(f"  Found {len(documents)} documents")

        try:
            # Ingest documents
            result = rag_engine.ingest_documents(
                case_dir=str(case_dir),
                case_id=case_id,
                force_reingest=force_reingest,
            )

            ingested = result.get('ingested', 0)
            skipped = result.get('skipped', 0)

            total_ingested += ingested
            total_skipped += skipped

            if ingested > 0:
                logger.info(f"  ✓ Ingested {ingested} documents")
            if skipped > 0:
                logger.info(f"  ⊘ Skipped {skipped} documents (already ingested)")

            successful_cases += 1

        except Exception as e:
            logger.error(f"  ✗ Error ingesting documents from {case_id}: {str(e)}")
            failed_cases += 1
            continue

    # Print summary
    logger.info("=" * 70)
    logger.info("INGESTION COMPLETE")
    logger.info("-" * 70)
    logger.info(f"Cases processed:        {successful_cases + failed_cases}")
    logger.info(f"  Successful:           {successful_cases}")
    logger.info(f"  Failed:               {failed_cases}")
    logger.info(f"Documents ingested:     {total_ingested}")
    logger.info(f"Documents skipped:      {total_skipped}")
    logger.info(f"Total chunks in vector store: {rag_engine.get_document_count()}")
    logger.info("=" * 70)


def main():
    """Main ingestion function."""
    args = parse_arguments()

    logger.info("Starting document ingestion...")
    logger.info(f"Data directory: {DATA_DIR}")

    # Check if data directory exists
    data_path = Path(DATA_DIR)
    if not data_path.exists():
        logger.error(f"Data directory not found: {DATA_DIR}")
        sys.exit(1)

    # Get list of case directories
    case_dirs = get_case_directories(data_path, args.case)

    if not case_dirs:
        logger.warning(f"No case directories found")
        sys.exit(0)

    logger.info(f"Found {len(case_dirs)} case directory(s)")

    # Validate cases
    logger.info("")
    logger.info("=" * 70)
    logger.info("VALIDATING CASES")
    logger.info("=" * 70)
    valid_cases = validate_cases(case_dirs)

    if not valid_cases:
        logger.error("No valid cases found. Please fix validation errors.")
        sys.exit(1)

    logger.info(f"\n{len(valid_cases)} of {len(case_dirs)} cases are valid")

    # Stop here if validate-only mode
    if args.validate_only:
        logger.info("Validation complete (--validate-only flag set)")
        sys.exit(0)

    # Initialize RAG engine
    logger.info("")
    logger.info("=" * 70)
    logger.info("INITIALIZING RAG ENGINE")
    logger.info("=" * 70)
    rag_engine = RAGEngine()
    rag_engine.initialize()
    logger.info("RAG engine initialized")

    # Clear database if requested
    if args.clear:
        logger.info("")
        logger.info("=" * 70)
        logger.info("CLEARING VECTOR STORE")
        logger.info("=" * 70)
        logger.warning("This will delete all documents from the vector store!")
        success = rag_engine.clear_all_documents()
        if success:
            logger.info("Vector store cleared successfully")
        else:
            logger.error("Failed to clear vector store")
            sys.exit(1)

    # Ingest cases
    logger.info("")
    logger.info("=" * 70)
    logger.info("INGESTING DOCUMENTS")
    logger.info("=" * 70)
    if args.force:
        logger.info("Force re-ingestion enabled (will re-ingest all documents)")

    ingest_cases(rag_engine, valid_cases, force_reingest=args.force)


if __name__ == "__main__":
    main()
