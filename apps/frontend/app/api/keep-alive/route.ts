/**
 * Keep-alive endpoint that pings the Render backend every 10 minutes
 * to prevent the free tier from spinning down.
 * Triggered by Vercel Cron: vercel.json
 *
 * Always returns 200 so browser/cron callers don't see console errors.
 * Backend unreachable is expected during cold-start — that's the whole point.
 */
export async function GET() {
  const backendUrl = process.env.BACKEND_ORIGIN;

  // No BACKEND_ORIGIN configured (local dev) — return OK immediately.
  if (!backendUrl || backendUrl.includes('127.0.0.1') || backendUrl.includes('localhost')) {
    return Response.json({ status: 'skipped', reason: 'local env', timestamp: new Date().toISOString() });
  }

  try {
    const res = await fetch(`${backendUrl}/api/v1/health`, {
      cache: 'no-store',
      signal: AbortSignal.timeout(10000),
    });
    const data = await res.json().catch(() => ({}));
    return Response.json({ status: 'ok', backend: data, timestamp: new Date().toISOString() });
  } catch (e) {
    // Backend unreachable / cold — still return 200 so the browser doesn't log a red error.
    // The ping itself IS the wake-up call; a timeout here is expected on first request.
    return Response.json({ status: 'unreachable', message: String(e), timestamp: new Date().toISOString() });
  }
}
