import dynamic from 'next/dynamic';
import type { ResumeData } from '@/components/dashboard/resume-component';
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
import { translate } from '@/lib/i18n/server';
import { resolveLocale } from '@/lib/i18n/locale';
import { withLocalizedDefaultSections } from '@/lib/utils/section-helpers';

// Dynamic import prevents SSR crash from isomorphic-dompurify and
// other client-side dependencies in the Resume component tree
const Resume = dynamic(() => import('@/components/dashboard/resume-component'), {
  ssr: false,
  loading: () => <div style={{ background: 'white', minHeight: '297mm' }} />,
});

type PageProps = {
  params: Promise<{ id: string }>;
  searchParams?: Promise<{
    template?: string; pageSize?: string;
    marginTop?: string; marginBottom?: string; marginLeft?: string; marginRight?: string;
    sectionSpacing?: string; itemSpacing?: string; lineHeight?: string;
    fontSize?: string; headerScale?: string;
    headerFont?: string; bodyFont?: string;
    headerWeight?: string; bodyWeight?: string;
    compactMode?: string; showContactIcons?: string;
    accentColor?: string; maxPages?: string; lang?: string;
  }>;
};

function parseHeaderFont(v?: string): HeaderFontFamily {
  return v === 'serif' || v === 'sans-serif' || v === 'mono' ? v : DEFAULT_TEMPLATE_SETTINGS.fontSize.headerFont;
}
function parseBodyFont(v?: string): BodyFontFamily {
  return v === 'serif' || v === 'sans-serif' || v === 'mono' ? v : DEFAULT_TEMPLATE_SETTINGS.fontSize.bodyFont;
}
function parseAccentColor(v?: string): AccentColor {
  return v === 'blue' || v === 'green' || v === 'orange' || v === 'red' ? v : DEFAULT_TEMPLATE_SETTINGS.accentColor;
}
function parseFontWeight(v: string | undefined, def: number): 300|400|500|600|700 {
  if (!v) return def as 300|400|500|600|700;
  const n = parseInt(v, 10);
  return ([300,400,500,600,700] as const).includes(n as 300|400|500|600|700) ? n as 300|400|500|600|700 : def as 300|400|500|600|700;
}
function parseBool(v: string | undefined, def: boolean): boolean {
  return v === 'true' ? true : v === 'false' ? false : def;
}
function parseLevel(v: string | undefined, def: SpacingLevel): SpacingLevel {
  if (!v) return def;
  const n = parseInt(v, 10);
  return (n >= 1 && n <= 5) ? n as SpacingLevel : def;
}
function parseMargin(v: string | undefined, def: number): number {
  if (!v) return def;
  const n = parseInt(v, 10);
  return isNaN(n) ? def : Math.max(5, Math.min(25, n));
}
function parseTemplate(v?: string): TemplateType {
  const valid = ['swiss-single','swiss-two-column','modern','modern-two-column','latex','clean','vivid','nova','crisp','executive','timeline','sidebar-pro'] as const;
  return (valid as readonly string[]).includes(v ?? '') ? v as TemplateType : 'swiss-single';
}
function parsePageSize(v?: string): PageSize {
  return v === 'A4' || v === 'LETTER' ? v : 'A4';
}

async function fetchResumeData(id: string): Promise<ResumeData> {
  const backendUrl = process.env.BACKEND_ORIGIN || 'https://resume-matcher-6kv2.onrender.com';
  try {
    const res = await fetch(`${backendUrl}/api/v1/resumes?resume_id=${encodeURIComponent(id)}`, {
      cache: 'no-store',
      signal: AbortSignal.timeout(20000),
    });
    if (!res.ok) return {} as ResumeData;
    const payload = await res.json() as { data: { processed_resume?: ResumeData; raw_resume?: { content?: string } } };
    if (payload.data.processed_resume) return payload.data.processed_resume;
    if (payload.data.raw_resume?.content) {
      try { return JSON.parse(payload.data.raw_resume.content) as ResumeData; } catch { return {} as ResumeData; }
    }
    return {} as ResumeData;
  } catch { return {} as ResumeData; }
}

export default async function PrintResumePage({ params, searchParams }: PageProps) {
  const { id } = await params;
  const sp = searchParams ? await searchParams : undefined;

  const resumeData = await fetchResumeData(id);
  const locale = resolveLocale(sp?.lang);
  const t = (key: string, p?: Record<string, string | number>) => translate(locale, key, p);
  const localizedData = withLocalizedDefaultSections(resumeData, t);

  const settings: TemplateSettings = {
    template: parseTemplate(sp?.template),
    pageSize: parsePageSize(sp?.pageSize),
    margins: {
      top: parseMargin(sp?.marginTop, DEFAULT_TEMPLATE_SETTINGS.margins.top),
      bottom: parseMargin(sp?.marginBottom, DEFAULT_TEMPLATE_SETTINGS.margins.bottom),
      left: parseMargin(sp?.marginLeft, DEFAULT_TEMPLATE_SETTINGS.margins.left),
      right: parseMargin(sp?.marginRight, DEFAULT_TEMPLATE_SETTINGS.margins.right),
    },
    spacing: {
      section: parseLevel(sp?.sectionSpacing, DEFAULT_TEMPLATE_SETTINGS.spacing.section),
      item: parseLevel(sp?.itemSpacing, DEFAULT_TEMPLATE_SETTINGS.spacing.item),
      lineHeight: parseLevel(sp?.lineHeight, DEFAULT_TEMPLATE_SETTINGS.spacing.lineHeight),
    },
    fontSize: {
      base: parseLevel(sp?.fontSize, DEFAULT_TEMPLATE_SETTINGS.fontSize.base),
      headerScale: parseLevel(sp?.headerScale, DEFAULT_TEMPLATE_SETTINGS.fontSize.headerScale),
      headerFont: parseHeaderFont(sp?.headerFont),
      bodyFont: parseBodyFont(sp?.bodyFont),
      headerWeight: parseFontWeight(sp?.headerWeight, DEFAULT_TEMPLATE_SETTINGS.fontSize.headerWeight),
      bodyWeight: parseFontWeight(sp?.bodyWeight, DEFAULT_TEMPLATE_SETTINGS.fontSize.bodyWeight),
    },
    compactMode: parseBool(sp?.compactMode, DEFAULT_TEMPLATE_SETTINGS.compactMode),
    showContactIcons: parseBool(sp?.showContactIcons, DEFAULT_TEMPLATE_SETTINGS.showContactIcons),
    accentColor: parseAccentColor(sp?.accentColor),
    maxPages: (sp?.maxPages === '2' ? 2 : 1) as 1 | 2,
  };

  const printSettings: TemplateSettings = { ...settings, margins: { top: 0, bottom: 0, left: 0, right: 0 } };

  const pageCSS = `*,*::before,*::after{-webkit-font-smoothing:antialiased;-moz-osx-font-smoothing:grayscale;text-rendering:optimizeLegibility;box-sizing:border-box}@page{size:${settings.pageSize==='A4'?'210mm 297mm':'215.9mm 279.4mm'};margin:${settings.margins.top}mm ${settings.margins.right}mm ${settings.margins.bottom}mm ${settings.margins.left}mm}html,body{margin:0;padding:0;width:100%;background:white;-webkit-print-color-adjust:exact;print-color-adjust:exact}.resume-print{width:100%;background:white;display:block}.resume-section:last-child{margin-bottom:0;padding-bottom:0}.resume-item:last-child{margin-bottom:0}`;

  const additionalSectionLabels = {
    technicalSkills: t('resume.additionalLabels.technicalSkills'),
    languages: t('resume.additionalLabels.languages'),
    certifications: t('resume.additionalLabels.certifications'),
    awards: t('resume.additionalLabels.awards'),
  };
  const sectionHeadings = {
    summary: t('resume.sections.summary'),
    experience: t('resume.sections.experience'),
    education: t('resume.sections.education'),
    projects: t('resume.sections.projects'),
    certifications: t('resume.sections.certifications'),
    skills: t('resume.sections.skillsOnly'),
    languages: t('resume.sections.languages'),
    awards: t('resume.sections.awards'),
    links: t('resume.sections.links'),
  };
  const fallbackLabels = { name: t('resume.defaults.name') };

  return (
    <div className="resume-print bg-white">
      <style dangerouslySetInnerHTML={{ __html: pageCSS }} />
      <Resume
        resumeData={localizedData}
        template={settings.template}
        settings={printSettings}
        additionalSectionLabels={additionalSectionLabels}
        sectionHeadings={sectionHeadings}
        fallbackLabels={fallbackLabels}
      />
    </div>
  );
}
