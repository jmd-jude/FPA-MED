# Case Discovery Feature Specification

## Problem Statement
With 100+ cases in the database, MDs need a way to find cases relevant to their current assignment without knowing specific case IDs or names.

## User Story
"As an MD, when I'm assigned a new evaluation, I want to find similar past cases so I can review precedents and approaches."

## Feature: "Find Relevant Cases"

### UI Placement
Add button above the case filter dropdown:
```
┌─────────────────────────────────────────┐
│  🔍 Find Similar Cases                  │ <- New button
└─────────────────────────────────────────┘
┌─────────────────────────────────────────┐
│  Filter by case: [All Cases ▼]         │ <- Existing dropdown
└─────────────────────────────────────────┘
```

### User Flow

**Step 1: Click "Find Similar Cases"**
- Modal/dialog appears with input field
- Placeholder: "Describe your current case (e.g., 'defendant with PTSD and substance abuse history')"

**Step 2: User enters description**
Example inputs:
- "Competency evaluation for schizophrenia patient"
- "Risk assessment for violent offense"
- "Defendant claims amnesia during crime"

**Step 3: System searches case metadata**
- Query runs against case summaries/key findings (NOT full documents)
- Returns top 3-5 most relevant cases ranked by similarity

**Step 4: Display results**
```
┌──────────────────────────────────────────────────────────┐
│ Relevant Cases Found:                                     │
│                                                           │
│ 1. State v. Rodriguez - Competency Restoration     89%   │
│    Schizophrenia, paranoid type | Not competent          │
│    Key: medication non-compliance, restoration success    │
│    [View Case] [Filter to This Case]                     │
│                                                           │
│ 2. State v. Anderson - Competency Evaluation       72%   │
│    Major depressive disorder | Competent                 │
│    Key: depression in remission, clear understanding     │
│    [View Case] [Filter to This Case]                     │
└──────────────────────────────────────────────────────────┘
```

**Step 5: User actions**
- **"Filter to This Case"**: Applies case filter, closes modal
- **"View Case"**: Shows full case metadata in modal
- Can select multiple cases to include in filter (future enhancement)

---

## Technical Implementation

### Backend Changes

#### New Model (models.py)
```python
class CaseSearchRequest(BaseModel):
    description: str

class CaseSearchResult(BaseModel):
    case_id: str
    title: str
    relevance_score: float
    summary: str
    key_findings: List[str]
    document_count: int
```

#### New Endpoint (main.py)
```python
@app.post("/search-cases", response_model=List[CaseSearchResult])
async def search_cases(request: CaseSearchRequest):
    """
    Find cases similar to user's description.
    Uses semantic search on case metadata/summaries.
    """
    results = rag_engine.search_cases(request.description, top_k=5)
    return results
```

#### RAG Engine Method (rag_engine.py)
```python
def search_cases(self, description: str, top_k: int = 5) -> List[CaseSearchResult]:
    """
    Search cases by semantic similarity to description.
    
    Strategy:
    1. Create embeddings for case summaries (from metadata.json)
    2. Compare user description embedding to case summaries
    3. Return top_k most similar cases
    
    Note: This searches CASE-level, not chunk-level
    """
    # Get embedding for user's description
    description_embedding = self.embed_model.get_text_embedding(description)
    
    # Query vector store for case-level matches
    # Filter by metadata to only get one chunk per case
    # Or: maintain separate case_summaries collection in ChromaDB
    
    # Return ranked results with metadata
```

#### Data Structure Consideration
**Option A**: Query existing chunks, deduplicate by case_id
- Pros: No new data structure needed
- Cons: Less precise, searches document content not summaries

**Option B**: Create separate case summaries collection in ChromaDB (RECOMMENDED)
- One entry per case with rich metadata
- Metadata includes: title, key_findings, diagnoses, outcomes, legal_questions
- Much faster, more accurate case-level search

### Frontend Changes

#### New Component (components/CaseDiscovery.tsx)
```typescript
interface CaseDiscoveryProps {
  onCaseSelect: (caseId: string) => void;
}

export function CaseDiscovery({ onCaseSelect }: CaseDiscoveryProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [description, setDescription] = useState('');
  const [results, setResults] = useState<CaseSearchResult[]>([]);
  const [isSearching, setIsSearching] = useState(false);

  const handleSearch = async () => {
    setIsSearching(true);
    const results = await searchCases(description);
    setResults(results);
    setIsSearching(false);
  };

  return (
    <>
      <button onClick={() => setIsOpen(true)}>
        🔍 Find Similar Cases
      </button>
      
      {isOpen && (
        <Modal>
          <input 
            placeholder="Describe your current case..."
            value={description}
            onChange={(e) => setDescription(e.target.value)}
          />
          <button onClick={handleSearch}>Search</button>
          
          {results.map(result => (
            <CaseResultCard 
              case={result}
              onSelect={() => {
                onCaseSelect(result.case_id);
                setIsOpen(false);
              }}
            />
          ))}
        </Modal>
      )}
    </>
  );
}
```

#### API Client (lib/api.ts)
```typescript
export async function searchCases(description: string): Promise<CaseSearchResult[]> {
  const response = await fetch('/api/search-cases', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ description })
  });
  return response.json();
}
```

#### Integration (app/page.tsx or ChatInterface.tsx)
```typescript
// Add CaseDiscovery component above CaseSelector
<CaseDiscovery onCaseSelect={(caseId) => setSelectedCase(caseId)} />
<CaseSelector 
  cases={cases} 
  selectedCase={selectedCase}
  onCaseChange={setSelectedCase}
/>
```

---

## Data Preparation

### Enhanced metadata.json
Add searchable summary to each case:

```json
{
  "case_id": "case_002",
  "title": "State v. Rodriguez - Competency Restoration",
  "summary": "Defendant with schizophrenia, paranoid type, found not competent due to active psychosis. History of medication non-compliance. Good prognosis for restoration with treatment. Follow-up showed significant improvement after 3 weeks on risperidone.",
  "key_findings": [
    "Not competent to stand trial at initial evaluation",
    "Schizophrenia, paranoid type, acute phase",
    "Medication non-compliance pattern",
    "Good prognosis for restoration (4-6 months)",
    "Significant improvement after 3 weeks treatment"
  ],
  "diagnoses": ["Schizophrenia, Paranoid Type", "Medication Non-Compliance"],
  "legal_question": "Competency to stand trial",
  "outcome": "Not competent, competency restoration recommended"
}
```

### Ingestion Script Update
Modify `ingest.py` to:
1. Load metadata.json for each case
2. Create case summary embeddings
3. Store in separate ChromaDB collection: `case_summaries`
4. Link to main chunks collection via case_id

---

## Why This Works

### Solves Real Problem
- MDs don't know case IDs when starting new evaluations
- Semantic search finds conceptually similar cases
- Works even if terminology differs ("PTSD" vs "trauma-related disorder")

### Scalable
- Searching 100 case summaries is faster than 10,000 document chunks
- Case-level results are more actionable than chunk-level
- Can add filters later (date range, court, evaluator, outcome)

### Low Hanging Fruit
- Uses existing RAG infrastructure
- Just adds new collection and endpoint
- UI is simple modal/dialog pattern

---

## Future Enhancements

### Multi-Case Filter
Allow selecting multiple cases from discovery results:
- "Show me all cases with schizophrenia AND violence risk"
- Filter dropdown becomes multi-select

### Case Similarity Scores
Show WHY cases are similar:
- "Matched on: diagnosis, legal question, medication issues"
- Highlight matching key findings

### Save Searches
- "Save this search for future reference"
- Build case collections: "My competency restoration cases"

### Export Case Comparisons
- Generate comparison table across selected cases
- Side-by-side diagnosis, outcomes, recommendations

---

## Implementation Checklist

**Backend** (45 min):
- [ ] Add case summary to metadata.json for existing cases
- [ ] Create CaseSearchRequest/Result models
- [ ] Add /search-cases endpoint
- [ ] Implement search_cases() in RAG engine
- [ ] Update ingest.py to create case_summaries collection

**Frontend** (45 min):
- [ ] Create CaseDiscovery component with modal
- [ ] Create CaseResultCard component
- [ ] Add searchCases() to API client
- [ ] Add API route proxy
- [ ] Integrate into main chat interface

**Testing** (15 min):
- [ ] Test search with various descriptions
- [ ] Verify case filtering works after selection
- [ ] Check relevance scores make sense

**Total Estimated Time**: 1.5-2 hours

---

## Success Metrics

Demo should show:
1. MD describes new case: "psychotic defendant, competency question"
2. System finds Rodriguez case (89% match) and Anderson case (lower %)
3. MD selects Rodriguez case
4. Case filter applied automatically
5. MD can now ask specific questions about Rodriguez

This demonstrates: **Discovery → Focus → Deep Dive** workflow that mirrors real MD behavior.