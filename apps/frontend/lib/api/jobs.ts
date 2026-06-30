import { apiPost } from './client';

export interface ExtractFromUrlResult {
  url: string;
  text: string;
  char_count: number;
}

/**
 * Fetch a job posting URL and extract the job description text.
 * Returns up to 5000 characters of job-relevant content.
 */
export async function extractJobFromUrl(url: string): Promise<ExtractFromUrlResult> {
  const res = await apiPost('/jobs/extract-from-url', { url });
  if (!res.ok) {
    const text = await res.text().catch(() => '');
    throw new Error(`Failed to extract job from URL (${res.status}): ${text}`);
  }
  return res.json();
}
