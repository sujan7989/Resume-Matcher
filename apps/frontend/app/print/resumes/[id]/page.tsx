'use client';

import { Suspense, useEffect, useState } from 'react';
import { useParams, useSearchParams } from 'next/navigation';
import Resume, { type ResumeData } from '@/components/dashboard/resume-component';
import {
  type TemplateType,
  type PageSize,
  type TemplateSettings,
  type SpacingLevel,
  type HeaderFontFamily,
  type BodyFontFamily,
  type AccentColor,
  DEFAULT_TEMPLATE_SETTINGS,
} from '@/lib/types/template-settings';

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
  if (!v) return def; const n = parseInt(v,10); return (n>=1&&n<=5)?n as SpacingLevel:def;
}
function pmg(v: string | null | undefined, def: number) {
  if (!v) return def; const n = parseInt(v,10); return isNaN(n)?def:Math.max(5,Math.min(25,n));
}
function ptpl(v?: string | null): TemplateType {
  const valid=['swiss-single','swiss-two-column','modern','modern-two-column','latex','clean','vivid','nova','crisp','executive','timeline','sidebar-pro'] as const;
  return (valid as readonly string[]).includes(v??'')?v as TemplateType:'swiss-single';
}
function pps(v?: string | null): PageSize { return v==='A4'||v==='LETTER'?v:'A4'; }

/** Inner component that uses useSearchParams — must be inside Suspense */
function PrintPageInner() {
  const params = useParams<{ id: string }>();
  const sp = useSearchParams();
  const [resumeData, setResumeData] = useState<ResumeData>({} as ResumeData);
  const [ready, setReady] = useState(false);
  const id = params?.id ?? '';

  useEffect(() => {
    if (!id) { setReady(true); return; }
    // Use Render backend directly — this page is rendered by Playwright on the server
    const backendUrl = 'https://resume-matcher-6kv2.onrender.com';
    fetch(`${backendUrl}/api/v1/resumes?resume_id=${encodeURIComponent(id)}`, { cache: 'no-store' })
      .then(r => r.json())
      .then(p => { setResumeData(p?.data?.processed_resume ?? {} as ResumeData); setReady(true); })
      .catch(() => { setResumeData({} as ResumeData); setReady(true); });
  }, [id]);

  const s: TemplateSettings = {
    template: ptpl(sp?.get('template')),
    pageSize: pps(sp?.get('pageSize')),
    margins: { top:pmg(sp?.get('marginTop'),DEFAULT_TEMPLATE_SETTINGS.margins.top), bottom:pmg(sp?.get('marginBottom'),DEFAULT_TEMPLATE_SETTINGS.margins.bottom), left:pmg(sp?.get('marginLeft'),DEFAULT_TEMPLATE_SETTINGS.margins.left), right:pmg(sp?.get('marginRight'),DEFAULT_TEMPLATE_SETTINGS.margins.right) },
    spacing: { section:plvl(sp?.get('sectionSpacing'),DEFAULT_TEMPLATE_SETTINGS.spacing.section), item:plvl(sp?.get('itemSpacing'),DEFAULT_TEMPLATE_SETTINGS.spacing.item), lineHeight:plvl(sp?.get('lineHeight'),DEFAULT_TEMPLATE_SETTINGS.spacing.lineHeight) },
    fontSize: { base:plvl(sp?.get('fontSize'),DEFAULT_TEMPLATE_SETTINGS.fontSize.base), headerScale:plvl(sp?.get('headerScale'),DEFAULT_TEMPLATE_SETTINGS.fontSize.headerScale), headerFont:ph(sp?.get('headerFont')), bodyFont:pb(sp?.get('bodyFont')), headerWeight:pfw(sp?.get('headerWeight'),DEFAULT_TEMPLATE_SETTINGS.fontSize.headerWeight), bodyWeight:pfw(sp?.get('bodyWeight'),DEFAULT_TEMPLATE_SETTINGS.fontSize.bodyWeight) },
    compactMode: pbool(sp?.get('compactMode'),DEFAULT_TEMPLATE_SETTINGS.compactMode),
    showContactIcons: pbool(sp?.get('showContactIcons'),DEFAULT_TEMPLATE_SETTINGS.showContactIcons),
    accentColor: pa(sp?.get('accentColor')),
    maxPages: (sp?.get('maxPages')==='2'?2:1) as 1|2,
  };

  const ps: TemplateSettings = {...s, margins:{top:0,bottom:0,left:0,right:0}};

  const css = `*,*::before,*::after{-webkit-font-smoothing:antialiased;-moz-osx-font-smoothing:grayscale;text-rendering:optimizeLegibility;box-sizing:border-box}@page{size:${s.pageSize==='A4'?'210mm 297mm':'215.9mm 279.4mm'};margin:${s.margins.top}mm ${s.margins.right}mm ${s.margins.bottom}mm ${s.margins.left}mm}html,body{margin:0;padding:0;width:100%;background:white;-webkit-print-color-adjust:exact;print-color-adjust:exact}.resume-print{width:100%;background:white;display:block}.resume-section:last-child{margin-bottom:0;padding-bottom:0}.resume-item:last-child{margin-bottom:0}`;

  if (!ready) return <div className="resume-print bg-white" style={{minHeight:'297mm'}} />;

  return (
    <div className="resume-print bg-white">
      <style dangerouslySetInnerHTML={{__html:css}} />
      <Resume resumeData={resumeData} template={s.template} settings={ps} />
    </div>
  );
}

/** Page export — wraps inner component in Suspense (required for useSearchParams in App Router) */
export default function PrintResumePage() {
  return (
    <Suspense fallback={<div className="resume-print bg-white" style={{minHeight:'297mm',background:'white'}} />}>
      <PrintPageInner />
    </Suspense>
  );
}
