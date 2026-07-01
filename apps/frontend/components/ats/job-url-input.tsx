'use client';

import React, { useState } from 'react';
import { Loader2, Link } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { extractJobFromUrl } from '@/lib/api/jobs';

interface JobUrlInputProps {
  onExtracted: (content: string) => void;
}

/**
 * Fetch a job posting from a URL and extract its text content.
 * Supports LinkedIn, Indeed, Glassdoor, and any public job posting URL.
 */
export function JobUrlInput({ onExtracted }: JobUrlInputProps) {
  const [url, setUrl] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  const handleFetch = async () => {
    const trimmed = url.trim();
    if (!trimmed.startsWith('http')) {
      setError('Please enter a valid URL starting with http:// or https://');
      return;
    }
    setError(null);
    setSuccess(false);
    setLoading(true);
    try {
      const result = await extractJobFromUrl(trimmed);
      onExtracted(result.text);
      setSuccess(true);
      setUrl('');
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : 'Could not extract job description. Try copying and pasting the text directly.'
      );
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') handleFetch();
  };

  return (
    <div className="space-y-2">
      <div className="flex gap-2">
        <div className="flex-1 flex items-center gap-2 border-2 border-black bg-background px-3">
          <Link className="w-3 h-3 text-ink-soft shrink-0" />
          <input
            type="url"
            className="flex-1 py-2 text-xs font-mono bg-transparent focus:outline-none placeholder:text-ink-soft"
            placeholder="https://linkedin.com/jobs/... or any job URL"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={loading}
          />
        </div>
        <Button size="sm" onClick={handleFetch} disabled={loading || !url.trim()}>
          {loading ? <Loader2 className="w-3 h-3 animate-spin" /> : 'Fetch'}
        </Button>
      </div>
      {error && <p className="text-xs text-red-700 font-mono">{error}</p>}
      {success && (
        <p className="text-xs text-green-700 font-mono">
          ✓ Job description extracted. Run ATS Analysis below.
        </p>
      )}
    </div>
  );
}
