'use client';

import React, { useState } from 'react';
import {
  ChevronDown,
  ChevronUp,
  CheckCircle2,
  XCircle,
  AlertCircle,
  CircleDot,
  Lightbulb,
  MessageSquare,
  Target,
  Award,
  TrendingUp,
} from 'lucide-react';
import { type ATSAnalysisResult } from '@/lib/api/ats';

interface ATSScorePanelProps {
  result: ATSAnalysisResult;
}

// ─── Helpers ──────────────────────────────────────────────────────────────────

function scoreColor(score: number): string {
  if (score >= 81) return 'text-green-700';
  if (score >= 61) return 'text-blue-700';
  if (score >= 41) return 'text-orange-600';
  return 'text-red-600';
}

function scoreBg(score: number): string {
  if (score >= 81) return 'bg-green-50 border-green-300';
  if (score >= 61) return 'bg-blue-50 border-blue-300';
  if (score >= 41) return 'bg-orange-50 border-orange-300';
  return 'bg-red-50 border-red-300';
}

function scoreBarColor(score: number): string {
  if (score >= 81) return 'bg-green-600';
  if (score >= 61) return 'bg-blue-600';
  if (score >= 41) return 'bg-orange-500';
  return 'bg-red-500';
}

function fitLevelBadge(level: string): string {
  switch (level) {
    case 'excellent':
      return 'bg-green-100 text-green-800 border-green-300';
    case 'good':
      return 'bg-blue-100 text-blue-800 border-blue-300';
    case 'moderate':
      return 'bg-orange-100 text-orange-800 border-orange-300';
    default:
      return 'bg-red-100 text-red-800 border-red-300';
  }
}

function importanceBadge(importance: string): string {
  switch (importance) {
    case 'critical':
      return 'bg-red-100 text-red-800 border-red-300';
    case 'important':
      return 'bg-orange-100 text-orange-800 border-orange-300';
    default:
      return 'bg-gray-100 text-gray-700 border-gray-300';
  }
}

function priorityBadge(priority: string): string {
  switch (priority) {
    case 'high':
      return 'bg-red-100 text-red-800 border-red-200';
    case 'medium':
      return 'bg-yellow-100 text-yellow-800 border-yellow-200';
    default:
      return 'bg-gray-100 text-gray-700 border-gray-200';
  }
}

function categoryBadge(category: string): string {
  switch (category) {
    case 'technical':
      return 'bg-blue-100 text-blue-800 border-blue-200';
    case 'behavioral':
      return 'bg-purple-100 text-purple-800 border-purple-200';
    case 'situational':
      return 'bg-teal-100 text-teal-800 border-teal-200';
    default:
      return 'bg-gray-100 text-gray-700 border-gray-200';
  }
}

// ─── Collapsible Section ──────────────────────────────────────────────────────

function Section({
  title,
  icon,
  defaultOpen = true,
  children,
}: {
  title: string;
  icon: React.ReactNode;
  defaultOpen?: boolean;
  children: React.ReactNode;
}) {
  const [open, setOpen] = useState(defaultOpen);
  return (
    <div className="border-2 border-black bg-white">
      <button
        type="button"
        className="w-full flex items-center justify-between px-4 py-3 font-mono text-sm font-bold uppercase tracking-wider bg-background hover:bg-secondary transition-colors"
        onClick={() => setOpen((o) => !o)}
        aria-expanded={open}
      >
        <span className="flex items-center gap-2">
          {icon}
          {title}
        </span>
        {open ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
      </button>
      {open && <div className="p-4">{children}</div>}
    </div>
  );
}

// ─── Score Bar ─────────────────────────────────────────────────────────────────

function ScoreBar({ label, score }: { label: string; score: number }) {
  return (
    <div className="flex items-center gap-3">
      <span className="font-mono text-xs text-ink-soft w-40 shrink-0 truncate" title={label}>
        {label}
      </span>
      <div className="flex-1 bg-gray-200 h-2 rounded-sm overflow-hidden">
        <div
          className={`h-full rounded-sm transition-all ${scoreBarColor(score)}`}
          style={{ width: `${score}%` }}
        />
      </div>
      <span className={`font-mono text-xs font-bold w-8 text-right ${scoreColor(score)}`}>
        {score}
      </span>
    </div>
  );
}

// ─── Circular Score ───────────────────────────────────────────────────────────

function CircularScore({ score }: { score: number }) {
  const radius = 52;
  const circumference = 2 * Math.PI * radius;
  const filled = (score / 100) * circumference;

  const strokeColor =
    score >= 81
      ? '#15803d'
      : score >= 61
        ? '#1d4ed8'
        : score >= 41
          ? '#ea580c'
          : '#dc2626';

  return (
    <div className="flex flex-col items-center gap-2">
      <svg width="128" height="128" viewBox="0 0 128 128" className="-rotate-90">
        <circle cx="64" cy="64" r={radius} fill="none" stroke="#e5e7eb" strokeWidth="12" />
        <circle
          cx="64"
          cy="64"
          r={radius}
          fill="none"
          stroke={strokeColor}
          strokeWidth="12"
          strokeDasharray={`${filled} ${circumference - filled}`}
          strokeLinecap="round"
        />
      </svg>
      <div className="absolute flex flex-col items-center justify-center" style={{ marginTop: '-96px' }}>
        <span className={`font-mono text-4xl font-bold ${scoreColor(score)}`}>{score}</span>
        <span className="font-mono text-xs text-ink-soft uppercase tracking-wider">/100</span>
      </div>
    </div>
  );
}

// ─── Main Component ────────────────────────────────────────────────────────────

export function ATSScorePanel({ result }: ATSScorePanelProps) {
  const { ats_score, keyword_analysis, skill_gap, resume_quality, interview_questions, tailoring_recommendations, job_fit_verdict } = result;

  const [expandedSkills, setExpandedSkills] = useState<Set<number>>(new Set());
  const [expandedQuestions, setExpandedQuestions] = useState<Set<number>>(new Set());

  const toggleSkill = (i: number) =>
    setExpandedSkills((s) => {
      const next = new Set(s);
      next.has(i) ? next.delete(i) : next.add(i);
      return next;
    });

  const toggleQuestion = (i: number) =>
    setExpandedQuestions((s) => {
      const next = new Set(s);
      next.has(i) ? next.delete(i) : next.add(i);
      return next;
    });

  return (
    <div className="space-y-4">
      {/* ── Job Fit Verdict ─────────────────────────────────────────────────── */}
      <div className={`border-2 p-4 ${scoreBg(ats_score.overall)}`}>
        <div className="flex items-start justify-between gap-4 flex-wrap">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-2">
              <Award className="w-5 h-5 shrink-0" />
              <span className="font-mono text-sm font-bold uppercase tracking-wider">Job Fit Verdict</span>
              <span
                className={`ml-2 inline-block px-2 py-0.5 text-xs font-mono font-bold uppercase border rounded-sm ${fitLevelBadge(job_fit_verdict.fit_level)}`}
              >
                {job_fit_verdict.fit_level}
              </span>
            </div>
            <p className="text-sm text-ink-soft leading-relaxed">{job_fit_verdict.summary}</p>
            <div className="mt-3 grid grid-cols-1 sm:grid-cols-2 gap-2">
              <div className="flex gap-2 text-sm">
                <CheckCircle2 className="w-4 h-4 text-green-600 shrink-0 mt-0.5" />
                <span className="text-ink-soft">
                  <strong className="text-ink-primary">Strength:</strong> {job_fit_verdict.biggest_strength}
                </span>
              </div>
              <div className="flex gap-2 text-sm">
                <AlertCircle className="w-4 h-4 text-orange-500 shrink-0 mt-0.5" />
                <span className="text-ink-soft">
                  <strong className="text-ink-primary">Gap:</strong> {job_fit_verdict.biggest_gap}
                </span>
              </div>
            </div>
          </div>

          {/* Circular Score */}
          <div className="relative flex items-center justify-center" style={{ width: 128, height: 128 }}>
            <CircularScore score={ats_score.overall} />
            <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
              <span className={`font-mono text-4xl font-bold leading-none ${scoreColor(ats_score.overall)}`}>
                {ats_score.overall}
              </span>
              <span className="font-mono text-[10px] text-ink-soft uppercase tracking-wider">/100</span>
            </div>
          </div>
        </div>
      </div>

      {/* ── Score Breakdown ──────────────────────────────────────────────────── */}
      <Section title="Score Breakdown" icon={<TrendingUp className="w-4 h-4" />}>
        <div className="space-y-3">
          <ScoreBar label="Keyword Match (35%)" score={ats_score.breakdown.keyword_match} />
          <ScoreBar label="Skills Alignment (30%)" score={ats_score.breakdown.skills_alignment} />
          <ScoreBar label="Experience Relevance (20%)" score={ats_score.breakdown.experience_relevance} />
          <ScoreBar label="Education Fit (10%)" score={ats_score.breakdown.education_fit} />
          <ScoreBar label="Resume Completeness (5%)" score={ats_score.breakdown.resume_completeness} />
        </div>
        {ats_score.score_explanation && (
          <p className="mt-4 text-sm text-ink-soft italic border-t border-gray-200 pt-3">
            {ats_score.score_explanation}
          </p>
        )}
      </Section>

      {/* ── Keyword Analysis ─────────────────────────────────────────────────── */}
      <Section title={`Keywords (${keyword_analysis.matched_count}/${keyword_analysis.total_jd_keywords} matched)`} icon={<Target className="w-4 h-4" />}>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          {/* Matched */}
          <div>
            <div className="flex items-center gap-1 mb-2">
              <CheckCircle2 className="w-4 h-4 text-green-600" />
              <span className="font-mono text-xs font-bold uppercase text-green-700">
                Matched ({keyword_analysis.matched_keywords.length})
              </span>
            </div>
            <div className="flex flex-wrap gap-1.5">
              {keyword_analysis.matched_keywords.map((kw, i) => (
                <span
                  key={i}
                  className={`inline-flex items-center gap-1 px-2 py-0.5 text-xs font-mono border rounded-sm ${importanceBadge(kw.importance)}`}
                  title={`Found in: ${kw.found_in}`}
                >
                  {kw.keyword}
                </span>
              ))}
              {keyword_analysis.matched_keywords.length === 0 && (
                <span className="text-sm text-ink-soft italic">No matched keywords</span>
              )}
            </div>
          </div>

          {/* Missing */}
          <div>
            <div className="flex items-center gap-1 mb-2">
              <XCircle className="w-4 h-4 text-red-500" />
              <span className="font-mono text-xs font-bold uppercase text-red-700">
                Missing ({keyword_analysis.missing_keywords.length})
              </span>
            </div>
            <div className="flex flex-wrap gap-1.5">
              {keyword_analysis.missing_keywords.map((kw, i) => (
                <span
                  key={i}
                  className={`inline-flex items-center gap-1 px-2 py-0.5 text-xs font-mono border rounded-sm cursor-help ${importanceBadge(kw.importance)}`}
                  title={kw.suggestion}
                >
                  {kw.keyword}
                </span>
              ))}
              {keyword_analysis.missing_keywords.length === 0 && (
                <span className="text-sm text-green-700 italic">All keywords matched!</span>
              )}
            </div>
          </div>
        </div>

        <div className="mt-3 pt-3 border-t border-gray-200 flex items-center gap-2">
          <div className={`h-2 flex-1 rounded-sm bg-gray-200 overflow-hidden`}>
            <div
              className={`h-full rounded-sm ${scoreBarColor(Math.round(keyword_analysis.match_percentage))}`}
              style={{ width: `${keyword_analysis.match_percentage}%` }}
            />
          </div>
          <span className="font-mono text-xs font-bold text-ink-soft">
            {Math.round(keyword_analysis.match_percentage)}% match
          </span>
        </div>
      </Section>

      {/* ── Skill Gap ────────────────────────────────────────────────────────── */}
      <Section title="Skill Gap Analysis" icon={<CircleDot className="w-4 h-4" />} defaultOpen={false}>
        {/* Strong Matches */}
        {skill_gap.strong_matches.length > 0 && (
          <div className="mb-4">
            <div className="flex items-center gap-1 mb-2">
              <span className="text-green-600 text-sm font-bold">🟢 Strong Matches</span>
            </div>
            <div className="flex flex-wrap gap-1.5">
              {skill_gap.strong_matches.map((s, i) => (
                <span key={i} className="px-2 py-0.5 text-xs font-mono bg-green-100 text-green-800 border border-green-300 rounded-sm">
                  {s}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Partial Matches */}
        {skill_gap.partial_match.length > 0 && (
          <div className="mb-4">
            <div className="flex items-center gap-1 mb-2">
              <span className="text-yellow-700 text-sm font-bold">🟡 Partial Matches ({skill_gap.partial_match.length})</span>
            </div>
            <div className="space-y-2">
              {skill_gap.partial_match.map((s, i) => (
                <div key={i} className="border border-yellow-200 bg-yellow-50 p-3 text-sm">
                  <div className="font-semibold text-yellow-800">{s.skill}</div>
                  <div className="mt-1 text-xs text-yellow-700 grid grid-cols-2 gap-x-4">
                    <span><strong>You have:</strong> {s.resume_has}</span>
                    <span><strong>Needed:</strong> {s.jd_needs}</span>
                  </div>
                  {s.gap && (
                    <div className="mt-1 text-xs text-yellow-600 italic">{s.gap}</div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Critical Missing */}
        {skill_gap.critical_missing.length > 0 && (
          <div>
            <div className="flex items-center gap-1 mb-2">
              <span className="text-red-700 text-sm font-bold">🔴 Critical Missing ({skill_gap.critical_missing.length})</span>
            </div>
            <div className="space-y-2">
              {skill_gap.critical_missing.map((s, i) => (
                <div key={i} className="border border-red-200 bg-red-50 p-3 text-sm">
                  <button
                    type="button"
                    className="w-full flex items-center justify-between text-left"
                    onClick={() => toggleSkill(i)}
                  >
                    <span className="font-semibold text-red-800">{s.skill}</span>
                    {expandedSkills.has(i) ? (
                      <ChevronUp className="w-3 h-3 text-red-600 shrink-0" />
                    ) : (
                      <ChevronDown className="w-3 h-3 text-red-600 shrink-0" />
                    )}
                  </button>
                  {expandedSkills.has(i) && (
                    <div className="mt-2 space-y-1 text-xs text-red-700">
                      {s.context && <p><strong>Why it matters:</strong> {s.context}</p>}
                      {s.how_to_address && (
                        <p className="mt-1">
                          <strong>How to address:</strong> {s.how_to_address}
                        </p>
                      )}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {skill_gap.critical_missing.length === 0 && skill_gap.partial_match.length === 0 && skill_gap.strong_matches.length === 0 && (
          <p className="text-sm text-ink-soft italic">No skill gap data available.</p>
        )}
      </Section>

      {/* ── Resume Quality ───────────────────────────────────────────────────── */}
      <Section title={`Resume Quality (${resume_quality.completeness_score}/100)`} icon={<CheckCircle2 className="w-4 h-4" />} defaultOpen={false}>
        {/* Completeness bar */}
        <div className="mb-4">
          <ScoreBar label="Completeness" score={resume_quality.completeness_score} />
        </div>

        {/* Bullet quality */}
        <div className="mb-4 grid grid-cols-2 gap-2 text-xs">
          <div className={`px-3 py-2 border rounded-sm font-mono ${resume_quality.bullet_quality.has_action_verbs ? 'bg-green-50 border-green-300 text-green-800' : 'bg-red-50 border-red-300 text-red-700'}`}>
            {resume_quality.bullet_quality.has_action_verbs ? '✓' : '✗'} Action Verbs
          </div>
          <div className={`px-3 py-2 border rounded-sm font-mono ${resume_quality.bullet_quality.has_metrics ? 'bg-green-50 border-green-300 text-green-800' : 'bg-red-50 border-red-300 text-red-700'}`}>
            {resume_quality.bullet_quality.has_metrics ? '✓' : '✗'} Metrics/Numbers
          </div>
          <div className="px-3 py-2 border border-gray-200 bg-gray-50 text-gray-700 font-mono rounded-sm">
            Bullet Strength: {resume_quality.bullet_quality.average_bullet_strength}
          </div>
          {resume_quality.bullet_quality.weak_bullets_count > 0 && (
            <div className="px-3 py-2 border border-orange-200 bg-orange-50 text-orange-700 font-mono rounded-sm">
              {resume_quality.bullet_quality.weak_bullets_count} weak bullets
            </div>
          )}
        </div>

        {/* Strengths */}
        {resume_quality.strengths.length > 0 && (
          <div className="mb-4">
            <div className="font-mono text-xs font-bold uppercase text-green-700 mb-2">Strengths</div>
            <ul className="space-y-1">
              {resume_quality.strengths.map((s, i) => (
                <li key={i} className="flex gap-2 text-sm text-ink-soft">
                  <CheckCircle2 className="w-4 h-4 text-green-500 shrink-0 mt-0.5" />
                  {s}
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Issues */}
        {resume_quality.issues.length > 0 && (
          <div>
            <div className="font-mono text-xs font-bold uppercase text-red-700 mb-2">Issues to Fix</div>
            <div className="space-y-2">
              {resume_quality.issues.map((issue, i) => (
                <div key={i} className="border border-orange-200 bg-orange-50 p-3 text-sm">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="font-mono text-xs px-1.5 py-0.5 bg-orange-200 text-orange-800 rounded-sm uppercase">
                      {issue.category.replace(/_/g, ' ')}
                    </span>
                  </div>
                  <p className="text-orange-800">{issue.description}</p>
                  {issue.fix && (
                    <p className="mt-1 text-xs text-orange-600 flex gap-1">
                      <Lightbulb className="w-3 h-3 shrink-0 mt-0.5" />
                      {issue.fix}
                    </p>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}
      </Section>

      {/* ── Tailoring Recommendations ─────────────────────────────────────────── */}
      <Section title="Tailoring Recommendations" icon={<Lightbulb className="w-4 h-4" />} defaultOpen={false}>
        {tailoring_recommendations.length === 0 ? (
          <p className="text-sm text-ink-soft italic">No recommendations available.</p>
        ) : (
          <div className="space-y-3">
            {[...tailoring_recommendations]
              .sort((a, b) => {
                const order = { high: 0, medium: 1, low: 2 };
                return (order[a.priority as keyof typeof order] ?? 2) - (order[b.priority as keyof typeof order] ?? 2);
              })
              .map((rec, i) => (
                <div key={i} className="border border-gray-200 p-3 text-sm">
                  <div className="flex items-center gap-2 mb-2 flex-wrap">
                    <span className={`inline-block px-2 py-0.5 text-xs font-mono font-bold uppercase border rounded-sm ${priorityBadge(rec.priority)}`}>
                      {rec.priority}
                    </span>
                    <span className="font-mono text-xs text-ink-soft uppercase tracking-wide border border-gray-200 px-1.5 py-0.5 rounded-sm bg-gray-50">
                      {rec.section}
                    </span>
                  </div>
                  <p className="text-ink-soft">{rec.recommendation}</p>
                  {rec.example && (
                    <div className="mt-2 bg-gray-50 border-l-4 border-blue-400 pl-3 py-1.5 text-xs text-blue-800 italic">
                      Example: {rec.example}
                    </div>
                  )}
                </div>
              ))}
          </div>
        )}
      </Section>

      {/* ── Interview Questions ──────────────────────────────────────────────── */}
      <Section title={`Interview Questions (${interview_questions.length})`} icon={<MessageSquare className="w-4 h-4" />} defaultOpen={false}>
        {interview_questions.length === 0 ? (
          <p className="text-sm text-ink-soft italic">No interview questions available.</p>
        ) : (
          <div className="space-y-3">
            {interview_questions.map((q, i) => (
              <div key={i} className="border-2 border-black p-3 text-sm">
                <button
                  type="button"
                  className="w-full flex items-start justify-between text-left gap-3"
                  onClick={() => toggleQuestion(i)}
                  aria-expanded={expandedQuestions.has(i)}
                >
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1 flex-wrap">
                      <span className={`inline-block px-2 py-0.5 text-xs font-mono font-bold uppercase border rounded-sm ${categoryBadge(q.category)}`}>
                        {q.category.replace(/_/g, ' ')}
                      </span>
                    </div>
                    <p className="font-semibold text-ink-primary leading-snug">{q.question}</p>
                  </div>
                  <div className="shrink-0 mt-1">
                    {expandedQuestions.has(i) ? (
                      <ChevronUp className="w-4 h-4 text-ink-soft" />
                    ) : (
                      <ChevronDown className="w-4 h-4 text-ink-soft" />
                    )}
                  </div>
                </button>

                {expandedQuestions.has(i) && (
                  <div className="mt-3 pt-3 border-t border-gray-200 space-y-2">
                    {q.why_asked && (
                      <div className="text-xs text-ink-soft">
                        <strong className="text-ink-primary">Why they ask this:</strong> {q.why_asked}
                      </div>
                    )}
                    {q.tip && (
                      <div className="text-xs bg-blue-50 border border-blue-200 p-2 text-blue-800">
                        <div className="flex gap-1">
                          <Lightbulb className="w-3 h-3 shrink-0 mt-0.5 text-blue-600" />
                          <span><strong>Answer tip:</strong> {q.tip}</span>
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </Section>
    </div>
  );
}
