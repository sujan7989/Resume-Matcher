'use client';

import { useEffect } from 'react';

/**
 * Silently pings the keep-alive endpoint every 4 minutes
 * to prevent Render free tier from spinning down.
 * Runs only in the browser, no UI rendered.
 */
export function KeepAlivePing() {
  useEffect(() => {
    const ping = () => {
      fetch('/api/keep-alive', { cache: 'no-store' }).catch(() => {});
    };
    // Ping immediately on load
    ping();
    // Then every 4 minutes (Render spins down after 15 min idle)
    const interval = setInterval(ping, 4 * 60 * 1000);
    return () => clearInterval(interval);
  }, []);

  return null;
}
