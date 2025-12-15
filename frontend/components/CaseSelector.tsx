/**
 * Case selector dropdown component
 */

'use client';

import type { Case } from '@/lib/types';

interface CaseSelectorProps {
  cases: Case[];
  selectedCase: string | null;
  onSelectCase: (caseId: string | null) => void;
}

export default function CaseSelector({ cases, selectedCase, onSelectCase }: CaseSelectorProps) {
  return (
    <div className="mb-4">
      <label htmlFor="case-select" className="block text-sm font-medium text-gray-700 mb-2">
        Filter by case:
      </label>
      <select
        id="case-select"
        value={selectedCase || ''}
        onChange={(e) => onSelectCase(e.target.value || null)}
        className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
      >
        <option value="">All Cases</option>
        {cases.map((c) => (
          <option key={c.case_id} value={c.case_id}>
            {c.title} ({c.document_count} docs)
          </option>
        ))}
      </select>
    </div>
  );
}
