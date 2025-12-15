/**
 * Chat interface component - main component that orchestrates the chat UI
 */

'use client';

import { useState, useEffect } from 'react';
import type { Message, Case } from '@/lib/types';
import { queryDocuments, getCases } from '@/lib/api';
import MessageList from './MessageList';
import QueryInput from './QueryInput';
import CaseSelector from './CaseSelector';
import CaseDiscovery from './CaseDiscovery';
import LoadingSpinner from './LoadingSpinner';

export default function ChatInterface() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [cases, setCases] = useState<Case[]>([]);
  const [selectedCase, setSelectedCase] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Load cases on mount
  useEffect(() => {
    const loadCases = async () => {
      try {
        const response = await getCases();
        setCases(response.cases);
      } catch (err) {
        console.error('Failed to load cases:', err);
      }
    };

    loadCases();
  }, []);

  const handleSubmit = async (query: string) => {
    setError(null);

    // Add user message
    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: query,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setIsLoading(true);

    try {
      // Query the backend
      const response = await queryDocuments({
        query,
        case_id: selectedCase || undefined,
      });

      // Add assistant message
      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: response.answer,
        sources: response.sources,
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');

      // Add error message
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: `Sorry, I encountered an error: ${err instanceof Error ? err.message : 'Unknown error'}`,
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const clearConversation = () => {
    setMessages([]);
    setSelectedCase(null);
  };

  return (
    <div className="flex flex-col h-screen max-w-6xl mx-auto p-4">
      <div className="mb-4">
        <div className="flex items-center justify-between mb-2">
          <h1 className="text-3xl font-bold text-gray-900">
            Forensic Psychiatry Document Assistant
          </h1>
          <button
            onClick={clearConversation}
            className="px-4 py-2 text-sm bg-gray-200 hover:bg-gray-300 rounded"
          >
            Clear Conversation
          </button>
        </div>
        <p className="text-gray-600">
          Ask questions about case documents and get AI-powered answers with source citations
        </p>
      </div>

      <div className="mb-3">
        <CaseDiscovery onCaseSelect={setSelectedCase} />
      </div>

      <CaseSelector
        cases={cases}
        selectedCase={selectedCase}
        onSelectCase={setSelectedCase}
      />

      {error && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
          {error}
        </div>
      )}

      <div className="flex-1 overflow-y-auto mb-4 bg-gray-50 rounded-lg p-4">
        <MessageList messages={messages} />
      </div>

      {isLoading && <LoadingSpinner />}

      <div className="border-t pt-4">
        <QueryInput onSubmit={handleSubmit} isLoading={isLoading} />
      </div>
    </div>
  );
}
