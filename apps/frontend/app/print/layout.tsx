/**
 * Print layout — intentionally minimal.
 * The root app/layout.tsx already wraps everything in <html><body>.
 * We must NOT add another <html> or <body> here — nested html tags
 * cause React hydration errors and Next.js 500s.
 */
export default function PrintLayout({ children }: { children: React.ReactNode }) {
  return <>{children}</>;
}
