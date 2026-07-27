/**
 * Long-running proxy for the resume improve/preview endpoint.
 * Uses /improve-proxy instead of /api/* to avoid the backend rewrite.
 * Vercel Hobby plan: 60s max. stepfun-ai/step-3.5-flash takes ~17s.
 *
 * POST /improve-proxy  →  BACKEND/api/v1/resumes/improve/preview
 * POST /improve-proxy?endpoint=...  →  BACKEND/api/v1/resumes/{endpoint}
 */

export const maxDuration = 60;
export const dynamic = 'force-dynamic';

const BACKEND = process.env.BACKEND_ORIGIN || 'https://resume-matcher-6kv2.onrender.com';

export async function POST(request: Request): Promise<Response> {
  const url = new URL(request.url);
  // Default to improve/preview; allow override via ?endpoint= for confirm etc.
  const endpoint = url.searchParams.get('endpoint') || 'resumes/improve/preview';
  const targetUrl = `${BACKEND}/api/v1/${endpoint}`;

  const body = await request.arrayBuffer();
  const headers = new Headers();
  const ct = request.headers.get('content-type');
  if (ct) headers.set('content-type', ct);

  try {
    const upstream = await fetch(targetUrl, { method: 'POST', headers, body });
    const resBody = await upstream.arrayBuffer();
    const resHeaders = new Headers();
    const rct = upstream.headers.get('content-type');
    if (rct) resHeaders.set('content-type', rct);
    return new Response(resBody, { status: upstream.status, headers: resHeaders });
  } catch (e) {
    console.error('[improve-proxy] error targeting', targetUrl, String(e));
    return new Response(
      JSON.stringify({ detail: `Proxy error: ${String(e)}` }),
      { status: 502, headers: { 'content-type': 'application/json' } }
    );
  }
}
