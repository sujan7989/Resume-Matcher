/**
 * Long-running proxy for LLM-heavy endpoints (resume improve, ATS analysis).
 * Uses /llm-proxy/* instead of /api/proxy/* to avoid being intercepted by
 * the /api/:path* rewrite rule in next.config.ts.
 *
 * Vercel Hobby plan: 60s max function duration.
 * stepfun-ai/step-3.5-flash full improve takes ~17s — well within limit.
 *
 * /llm-proxy/v1/resumes/improve/preview
 *   → BACKEND_ORIGIN/api/v1/resumes/improve/preview
 */

export const maxDuration = 60;
export const dynamic = 'force-dynamic';

const BACKEND_ORIGIN =
  process.env.BACKEND_ORIGIN || 'https://resume-matcher-6kv2.onrender.com';

export async function POST(
  request: Request,
  context: { params: Promise<{ path: string[] }> }
): Promise<Response> {
  const { path } = await context.params;
  const targetUrl = `${BACKEND_ORIGIN}/api/${path.join('/')}`;

  const body = await request.arrayBuffer();
  const headers = new Headers();
  const ct = request.headers.get('content-type');
  if (ct) headers.set('content-type', ct);

  try {
    const upstream = await fetch(targetUrl, {
      method: 'POST',
      headers,
      body,
    });
    const responseBody = await upstream.arrayBuffer();
    const resHeaders = new Headers();
    const rct = upstream.headers.get('content-type');
    if (rct) resHeaders.set('content-type', rct);
    return new Response(responseBody, { status: upstream.status, headers: resHeaders });
  } catch (e) {
    console.error('[llm-proxy] error:', String(e));
    return new Response(
      JSON.stringify({ detail: `LLM proxy error: ${String(e)}` }),
      { status: 502, headers: { 'content-type': 'application/json' } }
    );
  }
}
