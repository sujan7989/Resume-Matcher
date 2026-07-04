import { apiPost } from './client';

export interface ATSAnalysisResult {
  ats_score: {
    overall: number;
    breakdown: {
      keyword_match: number;
      skills_alignment: number;
      experience_relevance: number;
      education_fit: number;
      resume_completeness: number;
    };
    score_explanation: string;
  };
  keyword_analysis: {
    matched_keywords: Array<{ keyword: string; importance: string; found_in: string }>;
    missing_keywords: Array<{ keyword: string; importance: string; suggestion: string }>;
    total_jd_keywords: number;
    matched_count: number;
    match_percentage: number;
  };
  skill_gap: {
    critical_missing: Array<{ skill: string; context: string; how_to_address: string }>;
    partial_match: Array<{ skill: string; resume_has: string; jd_needs: string; gap: string }>;
    strong_matches: string[];
  };
  resume_quality: {
    completeness_score: number;
    issues: Array<{ category: string; description: string; fix: string }>;
    strengths: string[];
    bullet_quality: {
      has_action_verbs: boolean;
      has_metrics: boolean;
      average_bullet_strength: string;
      weak_bullets_count: number;
    };
  };
  interview_questions: Array<{
    question: string;
    category: string;
    why_asked: string;
    tip: string;
  }>;
  tailoring_recommendations: Array<{
    priority: string;
    section: string;
    recommendation: string;
    example: string;
  }>;
  job_fit_verdict: {
    fit_level: string;
    summary: string;
    biggest_strength: string;
    biggest_gap: string;
  };
  resume_id: string;
  job_id: string;
  analyzed_at: string;
}

export async function analyzeATSMatch(resumeId: string, jobId: string): Promise<ATSAnalysisResult> {
  const res = await apiPost('/ats/analyze', { resume_id: resumeId, job_id: jobId });
  if (!res.ok) {
    const text = await res.text().catch(() => '');
    throw new Error(`ATS analysis failed (${res.status}): ${text}`);
  }
  const payload = await res.json();
  return payload.data;
}

export interface SuggestedProject {
  name: string;
  role: string;
  years?: string;
  description: string[];
  rationale: string;
}

export async function suggestProject(resumeId: string, jobId: string): Promise<SuggestedProject> {
  const res = await apiPost('/ats/suggest-project', { resume_id: resumeId, job_id: jobId });
  if (!res.ok) {
    const text = await res.text().catch(() => '');
    throw new Error(`Failed to suggest project (${res.status}): ${text}`);
  }
  const payload = await res.json();
  return payload.project;
}

// ── Project Optimizer ─────────────────────────────────────────────────────────

export interface ProjectRelevance {
  index: number;
  name: string;
  relevance_score: number;
  verdict: 'keep' | 'replace';
  reason: string;
  jd_skills_matched: string[];
  jd_skills_missing: string[];
}

export interface AnalyzeProjectsResult {
  projects: ProjectRelevance[];
  summary: string;
}

export async function analyzeProjects(
  resumeId: string,
  jobId: string
): Promise<AnalyzeProjectsResult> {
  const res = await apiPost('/ats/analyze-projects', {
    resume_id: resumeId,
    job_id: jobId,
  });
  if (!res.ok) {
    const text = await res.text().catch(() => '');
    throw new Error(`Failed to analyze projects (${res.status}): ${text}`);
  }
  const payload = await res.json();
  return { projects: payload.projects, summary: payload.summary };
}

export interface ReplacementProject {
  id?: number;
  name: string;
  role: string;
  years?: string;
  description: string[];
  rationale: string;
}

export async function replaceProject(
  resumeId: string,
  jobId: string,
  projectIndex: number,
  replaceReason: string
): Promise<ReplacementProject> {
  const res = await apiPost('/ats/replace-project', {
    resume_id: resumeId,
    job_id: jobId,
    project_index: projectIndex,
    replace_reason: replaceReason,
  });
  if (!res.ok) {
    const text = await res.text().catch(() => '');
    throw new Error(`Failed to replace project (${res.status}): ${text}`);
  }
  const payload = await res.json();
  return payload.project;
}
