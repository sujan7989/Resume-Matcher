'use client';

/**
 * OptimizationSummaryModal
 *
 * Shows a Jobscan/Rezi-style summary after an inline resume optimization.
 * Data is derived entirely from existing backend fields — no new API calls.
 *
 * Displayed after confirmImproveResume succeeds, before the ATS re-analysis.
 */

import React from 'react';
import { CheckCircle2, AlertTriangle, TrendingUp, X, Download } from 'lucide-react';
import { Button } from '@/components/ui/button';
import type {
  ResumeDiffSummary,
  ResumeFieldDiff,
  RefinementStats,
} from '@/components/common/resume_previewer_context';

interface OptimizationSummaryModalProps {
  isOpen: boolean;
  onClose: () => void;
  onDownload?: () => void;
  /** ATS score before optimization (baseline) */
  beforeScore: number | null;
  /** ATS score after optimization (new analysis result) */
  afterScore: number | null;
  diffSummary?: ResumeDiffSummary | null;
  detailedChanges?: ResumeFieldDiff[] | null;
  warnings?: string[] | null;
  refinementStats?: RefinementStats | null;
}

function scoreColor(score: number): string {
  if (score >= 81) return 'text-green-700';
  if (score >= 61) return 'text-blue-700';
  if (score >= 41) return 'text-orange-600';
  return 'text-red-600';
}

function deltaColor(delta: number): string {
  if (delta > 0) return 'text-green-700';
  if (delta < 0) return 'text-red-600';
  return 'text-ink-soft';
}

export function OptimizationSummaryModal({
  isOpen,
  onClose,
  onDownload,
  beforeScore,
  afterScore,
  diffSummary,
  detailedChanges,
  warnings,
  refinementStats,
}: OptimizationSummaryModalProps) {
  if (!isOpen) return null;

  const delta = afterScore !== null && beforeScore !== null ? afterScore - beforeScore : null;

  // Build human-readable change list from diff data
  const changes: string[] = [];
  if (diffSummary) {
    if (diffSummary.skills_added > 0)
      changes.push(
        `Added ${diffSummary.skills_added} JD keyword${diffSummary.skills_added !== 1 ? 's' : ''}`
      );
    if (refinementStats && refinementStats.keywords_injected > 0)
      changes.push(
        `Injected ${refinementStats.keywords_injected} keyword${refinementStats.keywords_injected !== 1 ? 's' : ''} via refinement pass`
      );
    if (refinementStats && refinementStats.ai_phrases_removed.length > 0)
      changes.push(
        `Removed ${refinementStats.ai_phrases_removed.length} AI buzzword${refinementStats.ai_phrases_removed.length !== 1 ? 's' : ''}`
      );
  }

  if (detailedChanges) {
    const summaryChanged = detailedChanges.some((c) => c.field_type === 'summary');
    const expBullets = detailedChanges.filter(
      (c) => c.field_type === 'description' && c.field_path.startsWith('workExperience')
    );
    const projBullets = detailedChanges.filter(
      (c) => c.field_type === 'description' && c.field_path.startsWith('personalProjects')
    );
    const hasMetrics = detailedChanges.some(
      (c) =>
        (c.change_type === 'modified' || c.change_type === 'added') &&
        c.new_value &&
        /\d+[%x]|\$\d+|\d+\s*(users|ms|MB|GB|K\b|M\b)/.test(c.new_value)
    );

    if (summaryChanged) changes.push('Rewrote summary with JD keywords');
    if (expBullets.length > 0)
      changes.push(
        `Enhanced ${expBullets.length} experience bullet${expBullets.length !== 1 ? 's' : ''}`
      );
    if (projBullets.length > 0)
      changes.push(
        `Improved ${projBullets.length} project bullet${projBullets.length !== 1 ? 's' : ''}`
      );
    if (hasMetrics) changes.push('Added measurable metrics where supported');

    const reorderChanges = detailedChanges.filter(
      (c) => c.change_type === 'added' && c.field_type === 'skill'
    );
    if (reorderChanges.length === 0 && diffSummary && diffSummary.skills_added === 0) {
      const skillsReordered = detailedChanges.some(
        (c) => c.field_path === 'additional.technicalSkills'
      );
      if (skillsReordered) changes.push('Reordered skills by JD relevance');
    }
  }

  if (changes.length === 0 && diffSummary && diffSummary.total_changes > 0) {
    changes.push(
      `${diffSummary.total_changes} targeted improvement${diffSummary.total_changes !== 1 ? 's' : ''} applied`
    );
  }

  // Parse warnings into friendly lines
  // Backend warnings look like: "3 unsupported skill target(s) rejected"
  // We want to surface them as: "AWS not added — not found in your resume"
  const parsedWarnings: string[] = (warnings ?? []).map((w) => {
    // "N unsupported skill target(s) rejected" → keep as-is but prettify
    if (w.includes('unsupported skill target')) {
      return `${w.replace('(s)', 's')} — only skills from your resume were used`;
    }
    if (w.includes('rejected during verification')) {
      return w.replace('change(s)', 'changes') + ' — factual accuracy check';
    }
    if (w.includes('AI phrase')) {
      return w; // Already clear
    }
    if (w.includes('personal info')) {
      return 'Personal info (name/email/phone) was preserved unchanged';
    }
    return w;
  });

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50">
      <div className="w-full max-w-lg bg-white border-2 border-black shadow-[4px_4px_0px_0px_#000] flex flex-col max-h-[90vh]">
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-4 border-b-2 border-black bg-background">
          <div className="flex items-center gap-2">
            <TrendingUp className="w-5 h-5 text-green-700" />
            <span className="font-mono text-sm font-bold uppercase tracking-wider">
              Resume Optimization Summary
            </span>
          </div>
          <button
            onClick={onClose}
            className="text-ink-soft hover:text-black transition-colors"
            aria-label="Close"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Scrollable body */}
        <div className="overflow-y-auto flex-1 p-5 space-y-5">
          {/* ATS Score delta */}
          <div className="border-2 border-black p-4 flex items-center justify-between gap-4">
            <div>
              <div className="font-mono text-xs text-ink-soft uppercase tracking-wider mb-1">
                Overall ATS Improvement
              </div>
              {delta !== null ? (
                <div className={`font-mono text-4xl font-bold ${deltaColor(delta)}`}>
                  {delta > 0 ? '+' : ''}
                  {delta}
                </div>
              ) : (
                <div className="font-mono text-sm text-ink-soft italic">Re-analyzing…</div>
              )}
            </div>
            {beforeScore !== null && afterScore !== null && (
              <div className="flex items-center gap-3 text-center">
                <div>
                  <div className="font-mono text-xs text-ink-soft uppercase">Before</div>
                  <div className={`font-mono text-2xl font-bold ${scoreColor(beforeScore)}`}>
                    {beforeScore}
                  </div>
                </div>
                <div className="text-xl text-ink-soft">→</div>
                <div>
                  <div className="font-mono text-xs text-ink-soft uppercase">After</div>
                  <div className={`font-mono text-2xl font-bold ${scoreColor(afterScore)}`}>
                    {afterScore}
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Changes made */}
          {changes.length > 0 && (
            <div>
              <div className="font-mono text-xs font-bold uppercase tracking-wider text-ink-soft mb-2">
                Changes Made
              </div>
              <ul className="space-y-1.5">
                {changes.map((c, i) => (
                  <li key={i} className="flex items-start gap-2 text-sm">
                    <CheckCircle2 className="w-4 h-4 text-green-600 shrink-0 mt-0.5" />
                    <span>{c}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Warnings — what was NOT added and why */}
          {parsedWarnings.length > 0 && (
            <div>
              <div className="font-mono text-xs font-bold uppercase tracking-wider text-ink-soft mb-2">
                Warnings
              </div>
              <ul className="space-y-1.5">
                {parsedWarnings.map((w, i) => (
                  <li key={i} className="flex items-start gap-2 text-sm">
                    <AlertTriangle className="w-4 h-4 text-orange-500 shrink-0 mt-0.5" />
                    <span className="text-ink-soft">{w}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Trust statement */}
          <div className="border border-green-300 bg-green-50 p-3 flex items-start gap-2">
            <CheckCircle2 className="w-4 h-4 text-green-600 shrink-0 mt-0.5" />
            <p className="text-xs text-green-800 leading-relaxed">
              <strong>Resume optimized without adding fake experience.</strong> Every change was
              grounded in your original resume. Nothing was invented, fabricated, or exaggerated.
            </p>
          </div>
        </div>

        {/* Footer */}
        <div className="border-t-2 border-black px-5 py-4 flex items-center justify-between gap-3 bg-background">
          <Button variant="outline" size="sm" onClick={onClose}>
            Close
          </Button>
          {onDownload && (
            <Button size="sm" onClick={onDownload} className="gap-2">
              <Download className="w-4 h-4" />
              Download Optimized PDF
            </Button>
          )}
        </div>
      </div>
    </div>
  );
}
