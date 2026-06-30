'use client';

import React, { useState } from 'react';
import { Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { uploadJobDescriptions } from '@/lib/api/resume';

interface ManualJDInputProps {
  resumeId: string;
  onJobSaved: (jobId: string, content: string) => void;
}

/**
 * Allows the user to paste a job description manually when no job
 * is automatically linked to the resume. Saves the JD via the
 * existing jobs/upload endpoint and returns the job_id.
 */
export function ManualJDInput({ resumeId, onJobSaved }: ManualJDInputProps) {
  const [text, setText] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSave = async () => {
    const trimmed = text.trim();
    if (trimmed.length < 50) {
      setError('Please paste at least 50 characters of a job description.');
      return;
    }
    setError(null);
    setLoading(true);
    try {
      const jobId = await uploadJobDescriptions([trimmed], resumeId);
      onJobSaved(jobId, trimmed);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save job description.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-2">
      <textarea
        className="w-full h-32 text-xs font-mono p-3 border-2 border-black bg-background resize-none focus:outline-none focus:ring-1 focus:ring-blue-700"
        placeholder="Paste the job description here to run ATS analysis..."
        value={text}
        onChange={(e) => setText(e.target.value)}
        disabled={loading}
      />
      {error && (
        <p className="text-xs text-red-700 font-mono">{error}</p>
      )}
      <Button
        size="sm"
        onClick={handleSave}
        disabled={loading || text.trim().length < 50}
        className="w-full"
      >
        {loading ? (
          <>
            <Loader2 className="w-3 h-3 animate-spin" />
            Saving JD...
          </>
        ) : (
          'Save Job Description & Analyze'
        )}
      </Button>
    </div>
  );
}
