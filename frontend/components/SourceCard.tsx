/**
 * Source card component - displays document source with snippet
 */

import type { Source } from '@/lib/types';

interface SourceCardProps {
  source: Source;
  index: number;
}

export default function SourceCard({ source, index }: SourceCardProps) {
  return (
    <div className="bg-gray-50 border border-gray-200 rounded-lg p-3 text-sm">
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          <span className="inline-flex items-center justify-center w-6 h-6 rounded-full bg-blue-100 text-blue-700 text-xs font-medium">
            {index + 1}
          </span>
          <span className="font-medium text-gray-700">{source.doc_id}</span>
        </div>
        <span className="text-xs text-gray-500">
          Score: {(source.relevance_score * 100).toFixed(0)}%
        </span>
      </div>
      <p className="text-gray-600 text-xs leading-relaxed">{source.snippet}</p>
    </div>
  );
}
