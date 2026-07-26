/**
 * Long-running API proxy for endpoints that need > 30s (resume improve, ATS analysis).
 * Next.js API routes on Vercel Pro have up to 300s; on Hobby plan up to 60s.
 * This is still better than the rewrite proxy which has a hard ~30s limit.
 *
 * Routes handled: /api/proxy/* → BACKEND_ORIGIN/api/*
 */

export const maxDuration = 60; // Vercel Hobby plan max (60s)
export const dynamic = 'force-dynamic';

const BACKEND_ORIGIN =
  process.env.BACKEND_ORIGIN || 'https://resume-matcher-6kv2.onrender.com';

export async function POST(
  request: Request,
  { params }: { params: Promise<{ path: string[] }> }
): Promise<Response> {
  const { path } = await params;
  const backendPath = path.join('/');
  const targetUrl = `${BACKEND_ORIGIN}/api/${backendPath}`;

  const body = await request.arrayBuffer();
  const headers = new Headers();

  // Forward content-type
  const contentType = request.headers.get('content-type');
  if (contentType) headers.set('content-type', contentType);

  try {
    const upstream = await fetch(targetUrl, {
      method: 'POST',
      headers,
      body,
      // @ts-expect-error — Node.js fetch duplex option
      duplex: 'half',
    });

    const responseBody = await upstream.arrayBuffer();
    const responseHeaders = new Headers();
    const ct = upstream.headers.get('content-type');
    if (ct) responseHeaders.set('content-type', ct);

    return new Response(responseBody, {
      status: upstream.status,
      headers: responseHeaders,
    });
  } catch (e) {
    console.error('[proxy] upstream error:', e);
    return new Response(
      JSON.stringify({ detail: `Proxy error: ${String(e)}` }),
      { status: 502, headers: { 'content-type': 'application/json' } }
    );
  }
}

export async function GET(
  request: Request,
  { params }: { params: Promise<{ path: string[] }> }
): Promise<Response> {
  const { path } = await params;
  const backendPath = path.join('/');
  const url = new URL(request.url);
  const targetUrl = `${BACKEND_ORIGIN}/api/${backendPath}${url.search}`;

  try {
    const upstream = await fetch(targetUrl, { method: 'GET' });
    const responseBody = await upstream.arrayBuffer();
    const responseHeaders = new Headers();
    const ct = upstream.headers.get('content-type');
    if (ct) responseHeaders.set('content-type', ct);

    return new Response(responseBody, {
      status: upstream.status,
      headers: responseHeaders,
    });
  } catch (e) {
    return new Response(
      JSON.stringify({ detail: `Proxy error: ${String(e)}` }),
      { status: 502, headers: { 'content-type': 'application/json' } }
    );
  }
}
