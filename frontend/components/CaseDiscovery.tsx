/**
 * Case Discovery component - finds similar cases based on user description
 */

'use client';

import { useState } from 'react';
import type { CaseSearchResult } from '@/lib/types';
import { searchCases } from '@/lib/api';

interface CaseDiscoveryProps {
  onCaseSelect: (caseId: string) => void;
}

export default function CaseDiscovery({ onCaseSelect }: CaseDiscoveryProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [description, setDescription] = useState('');
  const [results, setResults] = useState<CaseSearchResult[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSearch = async () => {
    if (!description.trim()) {
      setError('Please enter a case description');
      return;
    }

    setError(null);
    setIsSearching(true);

    try {
      const searchResults = await searchCases(description);
      setResults(searchResults);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Search failed');
    } finally {
      setIsSearching(false);
    }
  };

  const handleSelectCase = (caseId: string) => {
    onCaseSelect(caseId);
    setIsOpen(false);
    setDescription('');
    setResults([]);
    setError(null);
  };

  const handleClose = () => {
    setIsOpen(false);
    setDescription('');
    setResults([]);
    setError(null);
  };

  return (
    <>
      <button
        onClick={() => setIsOpen(true)}
        className="w-full px-4 py-3 bg-blue-50 hover:bg-blue-100 text-blue-700 rounded-lg border border-blue-200 transition-colors flex items-center justify-center gap-2"
      >
        <span>🔍</span>
        <span className="font-medium">Find Similar Cases</span>
      </button>

      {isOpen && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-3xl w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6">
              <div className="flex justify-between items-center mb-4">
                <h2 className="text-2xl font-bold text-gray-900">Find Similar Cases</h2>
                <button
                  onClick={handleClose}
                  className="text-gray-400 hover:text-gray-600 text-2xl"
                >
                  ×
                </button>
              </div>

              <p className="text-gray-600 mb-4">
                Describe your current case to find similar past cases
              </p>

              <div className="mb-4">
                <textarea
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="e.g., 'Competency evaluation for schizophrenia patient' or 'Risk assessment for violent offense'"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
                  rows={3}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' && e.ctrlKey) {
                      handleSearch();
                    }
                  }}
                />
              </div>

              {error && (
                <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
                  {error}
                </div>
              )}

              <button
                onClick={handleSearch}
                disabled={isSearching}
                className="w-full px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-300 text-white rounded-lg font-medium transition-colors"
              >
                {isSearching ? 'Searching...' : 'Search Cases'}
              </button>

              {results.length > 0 && (
                <div className="mt-6">
                  <h3 className="text-lg font-semibold text-gray-900 mb-3">
                    Relevant Cases Found:
                  </h3>

                  <div className="space-y-4">
                    {results.map((result, index) => (
                      <div
                        key={result.case_id}
                        className="border border-gray-200 rounded-lg p-4 hover:border-blue-300 transition-colors"
                      >
                        <div className="flex justify-between items-start mb-2">
                          <div className="flex-1">
                            <div className="flex items-center gap-2 mb-1">
                              <span className="text-sm font-semibold text-gray-500">
                                {index + 1}.
                              </span>
                              <h4 className="font-semibold text-gray-900">
                                {result.title}
                              </h4>
                            </div>
                            <div className="flex items-center gap-2 text-sm text-gray-600 mb-2">
                              <span className="px-2 py-1 bg-green-100 text-green-800 rounded font-medium">
                                {result.relevance_score}% match
                              </span>
                              <span>•</span>
                              <span>{result.document_count} documents</span>
                            </div>
                          </div>
                        </div>

                        {result.summary && (
                          <p className="text-sm text-gray-700 mb-3">
                            {result.summary}
                          </p>
                        )}

                        {result.key_findings && result.key_findings.length > 0 && (
                          <div className="mb-3">
                            <p className="text-xs font-semibold text-gray-600 mb-1">
                              Key Findings:
                            </p>
                            <ul className="text-sm text-gray-700 space-y-1">
                              {result.key_findings.map((finding, i) => (
                                <li key={i} className="flex items-start gap-2">
                                  <span className="text-gray-400">•</span>
                                  <span>{finding}</span>
                                </li>
                              ))}
                            </ul>
                          </div>
                        )}

                        <button
                          onClick={() => handleSelectCase(result.case_id)}
                          className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded text-sm font-medium transition-colors"
                        >
                          Filter to This Case
                        </button>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {!isSearching && results.length === 0 && description && (
                <div className="mt-6 p-4 bg-gray-50 rounded-lg text-center text-gray-600">
                  Enter a description and click Search to find similar cases
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </>
  );
}
