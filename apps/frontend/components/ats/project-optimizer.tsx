'use client';

import React, { useState } from 'react';
import { Loader2, CheckCircle2, XCircle, RefreshCw, ChevronDown, ChevronUp, Plus, ArrowRight } from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
  analyzeProjects,
  replaceProject,
  type ProjectRelevance,
  type ReplacementProject,
} from '@/lib/api/ats';
import type { Project } from '@/components/dashboard/resume-component';

interface ProjectOptimizerProps {
  resumeId: string;
  jobId: string;
  /** Current projects on the resume */
  projects: Project[];
  /** Called when user confirms changes — receives the updated projects array */
  onApply: (updatedProjects: Project[]) => void;
}

type Step = 'idle' | 'analyzing' | 'results' | 'replacing' | 'preview';

interface PendingReplacement {
  projectIndex: number;        // index in the original projects array
  generated: ReplacementProject | null;
  generating: boolean;
  error: string | null;
  accepted: boolean | null;    // null=pending, true=accepted, false=rejected
}

function scoreColor(score: number) {
  if (score >= 80) return 'text-green-700';
  if (score >= 60) return 'text-blue-600';
  if (score >= 40) return 'text-orange-500';
  return 'text-red-600';
}

function scoreBg(score: number) {
  if (score >= 80) return 'bg-green-50 border-green-300';
  if (score >= 60) return 'bg-blue-50 border-blue-300';
  if (score >= 40) return 'bg-orange-50 border-orange-300';
  return 'bg-red-50 border-red-300';
}

function scoreBar(score: number) {
  if (score >= 80) return 'bg-green-500';
  if (score >= 60) return 'bg-blue-500';
  if (score >= 40) return 'bg-orange-400';
  return 'bg-red-500';
}

export function ProjectOptimizer({ resumeId, jobId, projects, onApply }: ProjectOptimizerProps) {
  const [step, setStep] = useState<Step>('idle');
  const [analysis, setAnalysis] = useState<ProjectRelevance[]>([]);
  const [summary, setSummary] = useState('');
  const [error, setError] = useState<string | null>(null);

  // Which projects user selected to replace (up to 3)
  const [selectedToReplace, setSelectedToReplace] = useState<Set<number>>(new Set());

  // Replacement state per project index
  const [replacements, setReplacements] = useState<Map<number, PendingReplacement>>(new Map());

  const [expandedIdx, setExpandedIdx] = useState<number | null>(null);

  // ── Step 1: Analyze ────────────────────────────────────────────────────────
  const handleAnalyze = async () => {
    setStep('analyzing');
    setError(null);
    setSelectedToReplace(new Set());
    setReplacements(new Map());
    try {
      const result = await analyzeProjects(resumeId, jobId);
      const autoSelect = new Set<number>(
        result.projects
          .filter(p => p.verdict === 'replace')
          .slice(0, 3)
          .map(p => p.index)
      );
      setAnalysis(result.projects);
      setSummary(result.summary);
      setSelectedToReplace(autoSelect);
      setStep('results');
    } catch (err) {
      const raw = err instanceof Error ? err.message : 'Analysis failed.';
      let msg = raw;
      if (raw.toLowerCase().includes('rate limit') || raw.toLowerCase().includes('ratelimit') || raw.includes('429')) {
        msg = 'Rate limit reached. Wait 30–60 seconds and try again.';
      } else if (raw.includes('404')) {
        msg = 'Feature not yet deployed on the server. Please wait a minute and refresh.';
      } else if (raw.length > 120) {
        msg = 'Analysis failed. Please try again.';
      }
      setError(msg);
      setStep('idle');
    }
  };

  // ── Step 2: Toggle selection ───────────────────────────────────────────────
  const toggleSelect = (idx: number) => {
    setSelectedToReplace(prev => {
      const next = new Set(prev);
      if (next.has(idx)) {
        next.delete(idx);
      } else {
        if (next.size >= 3) return prev; // max 3
        next.add(idx);
      }
      return next;
    });
  };

  // ── Step 3: Generate replacements ─────────────────────────────────────────
  const handleGenerateReplacements = async () => {
    if (selectedToReplace.size === 0) return;
    setStep('replacing');

    // Initialize replacement slots
    const initMap = new Map<number, PendingReplacement>();
    selectedToReplace.forEach(idx => {
      initMap.set(idx, { projectIndex: idx, generated: null, generating: true, error: null, accepted: null });
    });
    setReplacements(new Map(initMap));

    // Generate all in parallel
    const tasks = Array.from(selectedToReplace).map(async (idx) => {
      const relevanceItem = analysis.find(a => a.index === idx);
      const reason = relevanceItem?.reason ?? 'Low relevance to job description';
      try {
        const generated = await replaceProject(resumeId, jobId, idx, reason);
        setReplacements(prev => {
          const next = new Map(prev);
          next.set(idx, { projectIndex: idx, generated, generating: false, error: null, accepted: null });
          return next;
        });
      } catch (err) {
        const raw = err instanceof Error ? err.message : 'Generation failed';
        const msg = (raw.toLowerCase().includes('rate limit') || raw.includes('429'))
          ? 'Rate limit — wait 30s and retry'
          : raw.length > 120 ? 'Generation failed. Retry.' : raw;
        setReplacements(prev => {
          const next = new Map(prev);
          next.set(idx, {
            projectIndex: idx,
            generated: null,
            generating: false,
            error: msg,
            accepted: null,
          });
          return next;
        });
      }
    });

    await Promise.all(tasks);
    setStep('preview');
  };

  // ── Regenerate one project ─────────────────────────────────────────────────
  const handleRegenerate = async (idx: number) => {
    const relevanceItem = analysis.find(a => a.index === idx);
    const reason = relevanceItem?.reason ?? 'Low relevance to job description';
    setReplacements(prev => {
      const next = new Map(prev);
      const existing = next.get(idx);
      if (existing) next.set(idx, { ...existing, generating: true, error: null, generated: null, accepted: null });
      return next;
    });
    try {
      const generated = await replaceProject(resumeId, jobId, idx, reason);
      setReplacements(prev => {
        const next = new Map(prev);
        next.set(idx, { projectIndex: idx, generated, generating: false, error: null, accepted: null });
        return next;
      });
    } catch (err) {
      const raw2 = err instanceof Error ? err.message : 'Generation failed';
      const msg2 = (raw2.toLowerCase().includes('rate limit') || raw2.includes('429'))
        ? 'Rate limit — wait 30s and retry'
        : raw2.length > 120 ? 'Generation failed. Retry.' : raw2;
      setReplacements(prev => {
        const next = new Map(prev);
        next.set(idx, {
          projectIndex: idx, generated: null, generating: false,
          error: msg2, accepted: null,
        });
        return next;
      });
    }
  };

  // ── Accept/Reject individual ──────────────────────────────────────────────
  const handleAccept = (idx: number) => {
    setReplacements(prev => {
      const next = new Map(prev);
      const r = next.get(idx);
      if (r) next.set(idx, { ...r, accepted: true });
      return next;
    });
  };

  const handleReject = (idx: number) => {
    setReplacements(prev => {
      const next = new Map(prev);
      const r = next.get(idx);
      if (r) next.set(idx, { ...r, accepted: false });
      return next;
    });
  };

  // ── Apply all accepted changes ─────────────────────────────────────────────
  const handleApplyAll = () => {
    const updated = [...projects];
    replacements.forEach((r, idx) => {
      if (r.accepted === true && r.generated) {
        const orig = projects[idx];
        updated[idx] = {
          id: orig?.id ?? idx + 1,
          name: r.generated.name,
          role: r.generated.role,
          years: r.generated.years ?? orig?.years ?? '',
          description: r.generated.description,
          github: orig?.github,
          website: orig?.website,
        };
      }
    });
    onApply(updated);
    setStep('idle');
    setAnalysis([]);
    setSelectedToReplace(new Set());
    setReplacements(new Map());
  };

  const acceptedCount = Array.from(replacements.values()).filter(r => r.accepted === true).length;
  const allDecided = Array.from(replacements.values()).every(
    r => r.accepted !== null || r.generating
  );

  // ── No projects case ───────────────────────────────────────────────────────
  if (projects.length === 0) {
    return (
      <div className="border-2 border-black bg-white">
        <div className="px-4 py-3 border-b-2 border-black bg-background">
          <h3 className="font-mono text-xs font-bold uppercase tracking-wider flex items-center gap-2">
            <span className="w-2 h-2 bg-purple-600 inline-block" />
            Project Optimizer
          </h3>
        </div>
        <div className="p-4 space-y-3">
          <p className="font-mono text-xs text-ink-soft">
            No projects on resume yet. Generate a JD-tailored project to add.
          </p>
          <Button
            className="w-full"
            size="sm"
            onClick={async () => {
              setStep('analyzing');
              setError(null);
              try {
                // Treat as "add one new project" — call suggest-project
                const { suggestProject } = await import('@/lib/api/ats');
                const proj = await suggestProject(resumeId, jobId);
                setReplacements(new Map([[
                  -1,
                  { projectIndex: -1, generated: proj as ReplacementProject, generating: false, error: null, accepted: null }
                ]]));
                setStep('preview');
              } catch (err) {
                setError(err instanceof Error ? err.message : 'Failed');
                setStep('idle');
              }
            }}
            disabled={step === 'analyzing'}
          >
            {step === 'analyzing' ? (
              <><Loader2 className="w-3 h-3 animate-spin" /> Generating...</>
            ) : (
              <><Plus className="w-3 h-3" /> Generate JD-Tailored Project</>
            )}
          </Button>
          {error && <p className="text-xs text-red-600 font-mono">{error}</p>}

          {/* Preview the generated project for the "add" case */}
          {step === 'preview' && replacements.size > 0 && (() => {
            const r = replacements.get(-1);
            if (!r || !r.generated) return null;
            return (
              <div className="border-2 border-black p-3 space-y-2 bg-white">
                <div className="font-mono text-xs font-bold uppercase text-ink-soft">Generated Project</div>
                <div className="font-semibold">{r.generated.name}</div>
                {r.generated.role && <div className="text-xs text-ink-soft">{r.generated.role}</div>}
                <ul className="list-disc list-inside text-xs space-y-1">
                  {r.generated.description.map((d, i) => <li key={i}>{d}</li>)}
                </ul>
                {r.generated.rationale && (
                  <div className="bg-blue-50 border border-blue-200 p-2 text-xs text-blue-800">
                    <strong>Why:</strong> {r.generated.rationale}
                  </div>
                )}
                <div className="flex gap-2 pt-1">
                  <Button size="sm" variant="outline" onClick={() => { setStep('idle'); setReplacements(new Map()); }} className="rounded-none border-black flex-1">
                    Cancel
                  </Button>
                  <Button size="sm" variant="success" onClick={() => {
                    if (r.generated) {
                      onApply([...projects, {
                        id: 1,
                        name: r.generated.name,
                        role: r.generated.role,
                        years: r.generated.years ?? '',
                        description: r.generated.description,
                      }]);
                    }
                    setStep('idle');
                    setReplacements(new Map());
                  }} className="rounded-none flex-1">
                    Add to Resume
                  </Button>
                </div>
              </div>
            );
          })()}
        </div>
      </div>
    );
  }

  // ── Main optimizer UI ──────────────────────────────────────────────────────
  return (
    <div className="border-2 border-black bg-white">
      {/* Header */}
      <div className="px-4 py-3 border-b-2 border-black bg-background flex items-center justify-between">
        <h3 className="font-mono text-xs font-bold uppercase tracking-wider flex items-center gap-2">
          <span className="w-2 h-2 bg-purple-600 inline-block" />
          Project Optimizer
        </h3>
        {step !== 'idle' && (
          <button
            onClick={() => { setStep('idle'); setAnalysis([]); setSelectedToReplace(new Set()); setReplacements(new Map()); }}
            className="font-mono text-xs text-ink-soft hover:text-black"
          >
            ✕ Reset
          </button>
        )}
      </div>

      <div className="p-4 space-y-4">
        {/* Idle state */}
        {step === 'idle' && (
          <>
            <p className="font-mono text-xs text-ink-soft leading-relaxed">
              Checks each project&apos;s relevance to the JD. Low-scoring projects (priority to replace) are highlighted so you can generate JD-tailored replacements. Max 3 changes.
            </p>
            <p className="font-mono text-xs text-steel-grey">
              Projects on resume: <strong>{projects.length}</strong>
            </p>
            <Button className="w-full" size="sm" onClick={handleAnalyze}>
              <ArrowRight className="w-3 h-3" /> Analyze Projects vs JD
            </Button>
            {error && <p className="text-xs text-red-600 font-mono">{error}</p>}
          </>
        )}

        {/* Analyzing */}
        {step === 'analyzing' && (
          <div className="flex flex-col items-center gap-3 py-4">
            <Loader2 className="w-6 h-6 animate-spin text-purple-600" />
            <p className="font-mono text-xs text-ink-soft uppercase tracking-wide">
              Scoring projects against JD...
            </p>
          </div>
        )}

        {/* Results — show ranked list */}
        {(step === 'results') && (
          <>
            {summary && (
              <p className="font-mono text-xs text-ink-soft bg-secondary border border-steel-grey p-2 leading-relaxed">
                {summary}
              </p>
            )}

            <div className="space-y-2">
              {/* Sort: lowest score first so worst is at top */}
              {[...analysis].sort((a, b) => a.relevance_score - b.relevance_score).map((item) => {
                const isSelected = selectedToReplace.has(item.index);
                const isExpanded = expandedIdx === item.index;
                return (
                  <div
                    key={item.index}
                    className={`border-2 ${isSelected ? 'border-purple-600' : 'border-black'} bg-white`}
                  >
                    <div className="p-3">
                      <div className="flex items-start gap-3">
                        {/* Score badge */}
                        <div className={`shrink-0 w-10 h-10 flex flex-col items-center justify-center border ${scoreBg(item.relevance_score)}`}>
                          <span className={`font-mono text-sm font-bold leading-none ${scoreColor(item.relevance_score)}`}>
                            {item.relevance_score}
                          </span>
                          <span className="font-mono text-[8px] text-ink-soft uppercase">/100</span>
                        </div>

                        {/* Info */}
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center justify-between gap-2">
                            <span className="font-semibold text-sm truncate">{item.name}</span>
                            <span className={`shrink-0 text-[10px] font-mono font-bold uppercase px-1.5 py-0.5 border ${item.verdict === 'keep' ? 'bg-green-50 border-green-300 text-green-700' : 'bg-red-50 border-red-300 text-red-600'}`}>
                              {item.verdict === 'keep' ? '✓ Keep' : '⚠ Replace'}
                            </span>
                          </div>
                          {/* Score bar */}
                          <div className="mt-1.5 h-1.5 bg-gray-200 rounded-sm overflow-hidden">
                            <div className={`h-full rounded-sm ${scoreBar(item.relevance_score)}`} style={{ width: `${item.relevance_score}%` }} />
                          </div>
                          <p className="mt-1 text-xs text-ink-soft leading-snug">{item.reason}</p>

                          {/* Expand details */}
                          <button
                            type="button"
                            className="mt-1 flex items-center gap-1 text-xs text-blue-600 hover:text-blue-800 font-mono"
                            onClick={() => setExpandedIdx(isExpanded ? null : item.index)}
                          >
                            {isExpanded ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
                            {isExpanded ? 'Less' : 'Details'}
                          </button>

                          {isExpanded && (
                            <div className="mt-2 space-y-1 text-xs">
                              {item.jd_skills_matched.length > 0 && (
                                <div className="flex flex-wrap gap-1">
                                  <span className="text-green-700 font-bold">Matched:</span>
                                  {item.jd_skills_matched.map((s, i) => (
                                    <span key={i} className="bg-green-100 text-green-800 border border-green-300 px-1.5 py-0.5 rounded-sm font-mono">{s}</span>
                                  ))}
                                </div>
                              )}
                              {item.jd_skills_missing.length > 0 && (
                                <div className="flex flex-wrap gap-1">
                                  <span className="text-red-600 font-bold">Missing:</span>
                                  {item.jd_skills_missing.map((s, i) => (
                                    <span key={i} className="bg-red-100 text-red-800 border border-red-300 px-1.5 py-0.5 rounded-sm font-mono">{s}</span>
                                  ))}
                                </div>
                              )}
                            </div>
                          )}
                        </div>

                        {/* Select checkbox */}
                        <button
                          type="button"
                          onClick={() => toggleSelect(item.index)}
                          disabled={!isSelected && selectedToReplace.size >= 3}
                          className={`shrink-0 w-5 h-5 border-2 flex items-center justify-center transition-all ${
                            isSelected
                              ? 'bg-purple-600 border-purple-600 text-white'
                              : selectedToReplace.size >= 3
                                ? 'border-steel-grey opacity-40 cursor-not-allowed'
                                : 'border-black hover:border-purple-600'
                          }`}
                          title={isSelected ? 'Deselect' : 'Select to replace'}
                        >
                          {isSelected && <span className="text-[10px] leading-none">✓</span>}
                        </button>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>

            <div className="border-t border-steel-grey pt-3 space-y-2">
              <p className="font-mono text-xs text-ink-soft">
                Selected to replace: <strong className="text-purple-700">{selectedToReplace.size}</strong> / 3 max
              </p>
              <Button
                className="w-full"
                size="sm"
                onClick={handleGenerateReplacements}
                disabled={selectedToReplace.size === 0}
              >
                Generate {selectedToReplace.size} Replacement{selectedToReplace.size !== 1 ? 's' : ''} →
              </Button>
            </div>
          </>
        )}

        {/* Replacing / Preview */}
        {(step === 'replacing' || step === 'preview') && (
          <div className="space-y-4">
            <p className="font-mono text-xs text-ink-soft">
              {step === 'replacing' ? 'Generating tailored replacements...' : 'Review each replacement. Accept or reject before applying.'}
            </p>

            {Array.from(replacements.entries()).map(([idx, r]) => {
              const orig = projects[idx];
              const analysisItem = analysis.find(a => a.index === idx);
              return (
                <div key={idx} className={`border-2 ${r.accepted === true ? 'border-green-600' : r.accepted === false ? 'border-steel-grey opacity-60' : 'border-black'} bg-white`}>
                  <div className="px-3 py-2 border-b border-steel-grey bg-secondary flex items-center justify-between">
                    <div>
                      <span className="font-mono text-xs font-bold uppercase">Replacing:</span>
                      <span className="ml-2 text-xs text-ink-soft">{orig?.name ?? `Project #${idx + 1}`}</span>
                      {analysisItem && (
                        <span className={`ml-2 font-mono text-xs font-bold ${scoreColor(analysisItem.relevance_score)}`}>
                          (score: {analysisItem.relevance_score})
                        </span>
                      )}
                    </div>
                    {r.accepted === true && <span className="text-xs font-mono font-bold text-green-700">✓ Accepted</span>}
                    {r.accepted === false && <span className="text-xs font-mono text-steel-grey">✗ Rejected</span>}
                  </div>

                  <div className="p-3">
                    {r.generating && (
                      <div className="flex items-center gap-2 py-2">
                        <Loader2 className="w-4 h-4 animate-spin text-purple-600" />
                        <span className="font-mono text-xs text-ink-soft">Generating...</span>
                      </div>
                    )}

                    {r.error && (
                      <div className="text-xs text-red-600 font-mono bg-red-50 border border-red-200 p-2">
                        {r.error}
                        <Button size="sm" variant="outline" onClick={() => handleRegenerate(idx)} className="ml-2 h-5 text-xs rounded-none border-red-400">
                          Retry
                        </Button>
                      </div>
                    )}

                    {r.generated && !r.generating && (
                      <div className="space-y-2">
                        <div>
                          <span className="font-mono text-[10px] uppercase text-ink-soft">New Project</span>
                          <div className="font-semibold text-sm mt-0.5">{r.generated.name}</div>
                          {r.generated.role && <div className="text-xs text-ink-soft">{r.generated.role} {r.generated.years && `· ${r.generated.years}`}</div>}
                        </div>
                        <ul className="space-y-1">
                          {r.generated.description.map((d, i) => (
                            <li key={i} className="text-xs flex gap-1.5">
                              <span className="shrink-0 text-ink-soft">•</span>
                              <span>{d}</span>
                            </li>
                          ))}
                        </ul>
                        {r.generated.rationale && (
                          <div className="bg-purple-50 border border-purple-200 p-2 text-xs text-purple-800">
                            <strong>Why this replaces it:</strong> {r.generated.rationale}
                          </div>
                        )}

                        {r.accepted === null && (
                          <div className="flex gap-2 pt-1">
                            <Button size="sm" variant="outline" onClick={() => handleRegenerate(idx)} className="rounded-none border-black h-7 text-xs flex-none">
                              <RefreshCw className="w-3 h-3" />
                            </Button>
                            <Button size="sm" variant="outline" onClick={() => handleReject(idx)} className="rounded-none border-black h-7 text-xs flex-1 text-red-600 hover:bg-red-50">
                              <XCircle className="w-3 h-3" /> Reject
                            </Button>
                            <Button size="sm" onClick={() => handleAccept(idx)} className="rounded-none h-7 text-xs flex-1 bg-green-700 hover:bg-green-800 text-white">
                              <CheckCircle2 className="w-3 h-3" /> Accept
                            </Button>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              );
            })}

            {step === 'preview' && allDecided && acceptedCount > 0 && (
              <div className="border-t border-steel-grey pt-3 space-y-2">
                <p className="font-mono text-xs text-ink-soft">
                  <strong className="text-green-700">{acceptedCount}</strong> replacement{acceptedCount !== 1 ? 's' : ''} accepted. Apply to resume?
                </p>
                <Button className="w-full" size="sm" variant="success" onClick={handleApplyAll}>
                  Apply {acceptedCount} Change{acceptedCount !== 1 ? 's' : ''} to Resume
                </Button>
              </div>
            )}
            {step === 'preview' && allDecided && acceptedCount === 0 && (
              <div className="border-t border-steel-grey pt-3">
                <p className="font-mono text-xs text-ink-soft mb-2">All rejected. Go back to re-select?</p>
                <Button variant="outline" size="sm" className="w-full rounded-none border-black" onClick={() => { setStep('results'); setReplacements(new Map()); }}>
                  ← Back to Selection
                </Button>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
