/**
 * Keep-alive endpoint that pings the Render backend every 10 minutes
 * to prevent the free tier from spinning down.
 * Triggered by Vercel Cron: vercel.json
 */
export async function GET() {
  const backendUrl = process.env.BACKEND_ORIGIN || 'http://127.0.0.1:8000';
  try {
    const res = await fetch(`${backendUrl}/api/v1/health`, {
      cache: 'no-store',
      signal: AbortSignal.timeout(10000),
    });
    const data = await res.json();
    return Response.json({ status: 'ok', backend: data, timestamp: new Date().toISOString() });
  } catch (e) {
    return Response.json({ status: 'error', message: String(e) }, { status: 500 });
  }
}
