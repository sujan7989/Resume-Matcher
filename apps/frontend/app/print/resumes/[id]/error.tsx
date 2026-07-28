'use client';

/**
 * Error boundary for print/resumes/[id] page.
 * Returns a minimal white page so Playwright PDF still renders
 * something rather than showing a Next.js error page.
 */
export default function PrintResumeError() {
  return (
    <div style={{ background: 'white', padding: '40px', fontFamily: 'Arial, sans-serif' }}>
      <p style={{ color: '#888', fontSize: '12px' }}>
        Resume could not be loaded for PDF generation.
      </p>
    </div>
  );
}
