'use client';

// Force dynamic rendering — disables static pre-rendering that causes
// the Resume component tree to crash during build-time SSR
export const dynamic = 'force-dynamic';

import { Suspense, useEffect, useState } from 'react';
import { useParams, useSearchParams } from 'next/navigation';
import { type TemplateSettings, DEFAULT_TEMPLATE_SETTINGS } from '@/lib/types/template-settings';
import type { TemplateType, PageSize, SpacingLevel, HeaderFontFamily, BodyFontFamily, AccentColor } from '@/lib/types/template-settings';

// Lazy import Resume to avoid SSR of the component tree
// eslint-disable-next-line @typescript-eslint/no-explicit-any
let ResumeComponent: any = null;

function ph(v?: string | null): HeaderFontFamily {
  return v === 'serif' || v === 'sans-serif' || v === 'mono' ? v : DEFAULT_TEMPLATE_SETTINGS.fontSize.headerFont;
}
function pb(v?: string | null): BodyFontFamily {
  return v === 'serif' || v === 'sans-serif' || v === 'mono' ? v : DEFAULT_TEMPLATE_SETTINGS.fontSize.bodyFont;
}
function pa(v?: string | null): AccentColor {
  return v === 'blue' || v === 'green' || v === 'orange' || v === 'red' ? v : DEFAULT_TEMPLATE_SETTINGS.accentColor;
}
function pfw(v: string | null | undefined, def: number): 300|400|500|600|700 {
  if (!v) return def as 300|400|500|600|700;
  const n = parseInt(v, 10);
  return ([300,400,500,600,700] as number[]).includes(n) ? n as 300|400|500|600|700 : def as 300|400|500|600|700;
}
function pbool(v: string | null | undefined, def: boolean) { return v === 'true' ? true : v === 'false' ? false : def; }
function plvl(v: string | null | undefined, def: SpacingLevel): SpacingLevel {
  if (!v) return def; const n = parseInt(v, 10); return (n >= 1 && n <= 5) ? n as SpacingLevel : def;
}
function pmg(v: string | null | undefined, def: number) {
  if (!v) return def; const n = parseInt(v, 10); return isNaN(n) ? def : Math.max(5, Math.min(25, n));
}
function ptpl(v?: string | null): TemplateType {
  const valid = ['swiss-single','swiss-two-column','modern','modern-two-column','latex','clean','vivid','nova','crisp','executive','timeline','sidebar-pro'] as const;
  return (valid as readonly string[]).includes(v ?? '') ? v as TemplateType : 'swiss-single';
}
function pps(v?: string | null): PageSize { return v === 'A4' || v === 'LETTER' ? v : 'A4'; }

function PrintPageInner() {
  const params = useParams<{ id: string }>();
  const sp = useSearchParams();
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const [resumeData, setResumeData] = useState<any>({});
  const [ready, setReady] = useState(false);
  const [ResumeLoaded, setResumeLoaded] = useState(false);
  const id = params?.id ?? '';

  // Load Resume component client-side only
  useEffect(() => {
    import('@/components/dashboard/resume-component').then((mod) => {
      ResumeComponent = mod.default;
      setResumeLoaded(true);
    });
  }, []);

  useEffect(() => {
    if (!id) { setReady(true); return; }
    const backendUrl = 'https://resume-matcher-6kv2.onrender.com';
    fetch(`${backendUrl}/api/v1/resumes?resume_id=${encodeURIComponent(id)}`, { cache: 'no-store' })
      .then(r => r.json())
      .then(p => { setResumeData(p?.data?.processed_resume ?? {}); setReady(true); })
      .catch(() => { setResumeData({}); setReady(true); });
  }, [id]);

  const D = DEFAULT_TEMPLATE_SETTINGS;
  const s: TemplateSettings = {
    template: ptpl(sp?.get('template')),
    pageSize: pps(sp?.get('pageSize')),
    margins: { top: pmg(sp?.get('marginTop'), D.margins.top), bottom: pmg(sp?.get('marginBottom'), D.margins.bottom), left: pmg(sp?.get('marginLeft'), D.margins.left), right: pmg(sp?.get('marginRight'), D.margins.right) },
    spacing: { section: plvl(sp?.get('sectionSpacing'), D.spacing.section), item: plvl(sp?.get('itemSpacing'), D.spacing.item), lineHeight: plvl(sp?.get('lineHeight'), D.spacing.lineHeight) },
    fontSize: { base: plvl(sp?.get('fontSize'), D.fontSize.base), headerScale: plvl(sp?.get('headerScale'), D.fontSize.headerScale), headerFont: ph(sp?.get('headerFont')), bodyFont: pb(sp?.get('bodyFont')), headerWeight: pfw(sp?.get('headerWeight'), D.fontSize.headerWeight), bodyWeight: pfw(sp?.get('bodyWeight'), D.fontSize.bodyWeight) },
    compactMode: pbool(sp?.get('compactMode'), D.compactMode),
    showContactIcons: pbool(sp?.get('showContactIcons'), D.showContactIcons),
    accentColor: pa(sp?.get('accentColor')),
    maxPages: (sp?.get('maxPages') === '2' ? 2 : 1) as 1 | 2,
  };
  const ps: TemplateSettings = { ...s, margins: { top: 0, bottom: 0, left: 0, right: 0 } };
  const css = `*,*::before,*::after{-webkit-font-smoothing:antialiased;-moz-osx-font-smoothing:grayscale;text-rendering:optimizeLegibility;box-sizing:border-box}@page{size:${s.pageSize === 'A4' ? '210mm 297mm' : '215.9mm 279.4mm'};margin:${s.margins.top}mm ${s.margins.right}mm ${s.margins.bottom}mm ${s.margins.left}mm}html,body{margin:0;padding:0;width:100%;background:white;-webkit-print-color-adjust:exact;print-color-adjust:exact}.resume-print{width:100%;background:white;display:block}.resume-section:last-child{margin-bottom:0;padding-bottom:0}.resume-item:last-child{margin-bottom:0}`;

  if (!ready || !ResumeLoaded || !ResumeComponent) {
    return <div className="resume-print bg-white" style={{ minHeight: '297mm', background: 'white' }} />;
  }

  return (
    <div className="resume-print bg-white">
      <style dangerouslySetInnerHTML={{ __html: css }} />
      <ResumeComponent resumeData={resumeData} template={s.template} settings={ps} />
    </div>
  );
}

export default function PrintResumePage() {
  return (
    <Suspense fallback={<div className="resume-print bg-white" style={{ minHeight: '297mm', background: 'white' }} />}>
      <PrintPageInner />
    </Suspense>
  );
}
