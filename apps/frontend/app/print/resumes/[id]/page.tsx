'use client';

import { useEffect, useState } from 'react';
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

function parseHeaderFont(v?: string | null): HeaderFontFamily {
  return v === 'serif' || v === 'sans-serif' || v === 'mono' ? v : DEFAULT_TEMPLATE_SETTINGS.fontSize.headerFont;
}
function parseBodyFont(v?: string | null): BodyFontFamily {
  return v === 'serif' || v === 'sans-serif' || v === 'mono' ? v : DEFAULT_TEMPLATE_SETTINGS.fontSize.bodyFont;
}
function parseAccentColor(v?: string | null): AccentColor {
  return v === 'blue' || v === 'green' || v === 'orange' || v === 'red' ? v : DEFAULT_TEMPLATE_SETTINGS.accentColor;
}
function parseFontWeight(v: string | null | undefined, def: number): 300|400|500|600|700 {
  if (!v) return def as 300|400|500|600|700;
  const n = parseInt(v, 10);
  const valid: number[] = [300, 400, 500, 600, 700];
  return valid.includes(n) ? n as 300|400|500|600|700 : def as 300|400|500|600|700;
}
function parseBool(v: string | null | undefined, def: boolean): boolean {
  return v === 'true' ? true : v === 'false' ? false : def;
}
function parseLevel(v: string | null | undefined, def: SpacingLevel): SpacingLevel {
  if (!v) return def;
  const n = parseInt(v, 10);
  return (n >= 1 && n <= 5) ? n as SpacingLevel : def;
}
function parseMargin(v: string | null | undefined, def: number): number {
  if (!v) return def;
  const n = parseInt(v, 10);
  return isNaN(n) ? def : Math.max(5, Math.min(25, n));
}
function parseTemplate(v?: string | null): TemplateType {
  const valid = ['swiss-single','swiss-two-column','modern','modern-two-column','latex','clean','vivid','nova','crisp','executive','timeline','sidebar-pro'] as const;
  return (valid as readonly string[]).includes(v ?? '') ? v as TemplateType : 'swiss-single';
}
function parsePageSize(v?: string | null): PageSize {
  return v === 'A4' || v === 'LETTER' ? v : 'A4';
}

export default function PrintResumePage() {
  const params = useParams<{ id: string }>();
  const sp = useSearchParams();
  const [resumeData, setResumeData] = useState<ResumeData>({} as ResumeData);
  const [ready, setReady] = useState(false);

  const id = params?.id ?? '';

  useEffect(() => {
    if (!id) return;
    const backendUrl = process.env.NEXT_PUBLIC_API_URL === '/' || !process.env.NEXT_PUBLIC_API_URL
      ? 'https://resume-matcher-6kv2.onrender.com'
      : process.env.NEXT_PUBLIC_API_URL;
    const url = `${backendUrl}/api/v1/resumes?resume_id=${encodeURIComponent(id)}`;
    fetch(url, { cache: 'no-store' })
      .then((r) => r.json())
      .then((payload) => {
        const data = payload?.data?.processed_resume ?? {};
        setResumeData(data);
        setReady(true);
      })
      .catch(() => { setResumeData({} as ResumeData); setReady(true); });
  }, [id]);

  const settings: TemplateSettings = {
    template: parseTemplate(sp?.get('template')),
    pageSize: parsePageSize(sp?.get('pageSize')),
    margins: {
      top: parseMargin(sp?.get('marginTop'), DEFAULT_TEMPLATE_SETTINGS.margins.top),
      bottom: parseMargin(sp?.get('marginBottom'), DEFAULT_TEMPLATE_SETTINGS.margins.bottom),
      left: parseMargin(sp?.get('marginLeft'), DEFAULT_TEMPLATE_SETTINGS.margins.left),
      right: parseMargin(sp?.get('marginRight'), DEFAULT_TEMPLATE_SETTINGS.margins.right),
    },
    spacing: {
      section: parseLevel(sp?.get('sectionSpacing'), DEFAULT_TEMPLATE_SETTINGS.spacing.section),
      item: parseLevel(sp?.get('itemSpacing'), DEFAULT_TEMPLATE_SETTINGS.spacing.item),
      lineHeight: parseLevel(sp?.get('lineHeight'), DEFAULT_TEMPLATE_SETTINGS.spacing.lineHeight),
    },
    fontSize: {
      base: parseLevel(sp?.get('fontSize'), DEFAULT_TEMPLATE_SETTINGS.fontSize.base),
      headerScale: parseLevel(sp?.get('headerScale'), DEFAULT_TEMPLATE_SETTINGS.fontSize.headerScale),
      headerFont: parseHeaderFont(sp?.get('headerFont')),
      bodyFont: parseBodyFont(sp?.get('bodyFont')),
      headerWeight: parseFontWeight(sp?.get('headerWeight'), DEFAULT_TEMPLATE_SETTINGS.fontSize.headerWeight),
      bodyWeight: parseFontWeight(sp?.get('bodyWeight'), DEFAULT_TEMPLATE_SETTINGS.fontSize.bodyWeight),
    },
    compactMode: parseBool(sp?.get('compactMode'), DEFAULT_TEMPLATE_SETTINGS.compactMode),
    showContactIcons: parseBool(sp?.get('showContactIcons'), DEFAULT_TEMPLATE_SETTINGS.showContactIcons),
    accentColor: parseAccentColor(sp?.get('accentColor')),
    maxPages: (sp?.get('maxPages') === '2' ? 2 : 1) as 1 | 2,
  };

  const printSettings: TemplateSettings = { ...settings, margins: { top: 0, bottom: 0, left: 0, right: 0 } };

  const pageCSS = `*,*::before,*::after{-webkit-font-smoothing:antialiased;-moz-osx-font-smoothing:grayscale;text-rendering:optimizeLegibility;box-sizing:border-box}@page{size:${settings.pageSize==='A4'?'210mm 297mm':'215.9mm 279.4mm'};margin:${settings.margins.top}mm ${settings.margins.right}mm ${settings.margins.bottom}mm ${settings.margins.left}mm}html,body{margin:0;padding:0;width:100%;background:white;-webkit-print-color-adjust:exact;print-color-adjust:exact}.resume-print{width:100%;background:white;display:block}.resume-section:last-child{margin-bottom:0;padding-bottom:0}.resume-item:last-child{margin-bottom:0}`;

  if (!ready) {
    return <div className="resume-print bg-white" style={{ minHeight: '297mm' }} />;
  }

  return (
    <div className="resume-print bg-white">
      <style dangerouslySetInnerHTML={{ __html: pageCSS }} />
      <Resume
        resumeData={resumeData}
        template={settings.template}
        settings={printSettings}
      />
    </div>
  );
}
