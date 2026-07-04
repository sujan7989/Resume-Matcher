import Resume, { ResumeData } from '@/components/dashboard/resume-component';
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
import { API_BASE } from '@/lib/api/client';
import { translate } from '@/lib/i18n/server';
import { resolveLocale } from '@/lib/i18n/locale';
import { withLocalizedDefaultSections } from '@/lib/utils/section-helpers';

type PageProps = {
  params: Promise<{ id: string }>;
  searchParams?: Promise<{
    template?: string;
    pageSize?: string;
    marginTop?: string;
    marginBottom?: string;
    marginLeft?: string;
    marginRight?: string;
    sectionSpacing?: string;
    itemSpacing?: string;
    lineHeight?: string;
    fontSize?: string;
    headerScale?: string;
    headerFont?: string;
    bodyFont?: string;
    headerWeight?: string;
    bodyWeight?: string;
    compactMode?: string;
    showContactIcons?: string;
    accentColor?: string;
    maxPages?: string;
    lang?: string;
  }>;
};

/**
 * Parse header font family
 */
function parseHeaderFont(value: string | undefined): HeaderFontFamily {
  if (value === 'serif' || value === 'sans-serif' || value === 'mono') {
    return value;
  }
  return DEFAULT_TEMPLATE_SETTINGS.fontSize.headerFont;
}

/**
 * Parse body font family
 */
function parseBodyFont(value: string | undefined): BodyFontFamily {
  if (value === 'serif' || value === 'sans-serif' || value === 'mono') {
    return value;
  }
  return DEFAULT_TEMPLATE_SETTINGS.fontSize.bodyFont;
}

/**
 * Parse accent color
 */
function parseAccentColor(value: string | undefined): AccentColor {
  if (value === 'blue' || value === 'green' || value === 'orange' || value === 'red') {
    return value;
  }
  return DEFAULT_TEMPLATE_SETTINGS.accentColor;
}

/**
 * Parse font weight, clamped to valid values
 */
function parseFontWeight(
  value: string | undefined,
  defaultValue: number
): 300 | 400 | 500 | 600 | 700 {
  if (!value) return defaultValue as 300 | 400 | 500 | 600 | 700;
  const num = parseInt(value, 10);
  const valid = [300, 400, 500, 600, 700];
  if (isNaN(num) || !valid.includes(num)) return defaultValue as 300 | 400 | 500 | 600 | 700;
  return num as 300 | 400 | 500 | 600 | 700;
}

/**
 * Parse boolean from string
 */
function parseBoolean(value: string | undefined, defaultValue: boolean): boolean {
  if (value === 'true') return true;
  if (value === 'false') return false;
  return defaultValue;
}

async function fetchResumeData(id: string): Promise<ResumeData> {
  // SSR context: must use Render backend URL directly, not localhost
  const backendUrl = process.env.BACKEND_ORIGIN || 'https://resume-matcher-gw36.onrender.com';
  const res = await fetch(`${backendUrl}/api/v1/resumes?resume_id=${encodeURIComponent(id)}`, {
    cache: 'no-store',
  });
  if (!res.ok) {
    throw new Error(`Failed to load resume (status ${res.status}).`);
  }
  const payload = (await res.json()) as {
    data: { processed_resume?: ResumeData; raw_resume?: { content?: string } };
  };
  if (payload.data.processed_resume) {
    return payload.data.processed_resume;
  }
  if (payload.data.raw_resume?.content) {
    try {
      return JSON.parse(payload.data.raw_resume.content) as ResumeData;
    } catch (error) {
      // Log error for debugging instead of silently failing
      // Note: Avoid logging content preview to prevent PII exposure
      console.error('Failed to parse resume JSON:', {
        resumeId: id,
        error: error instanceof Error ? error.message : 'Unknown error',
        contentLength: payload.data.raw_resume.content.length,
      });
      throw new Error('Failed to parse resume data. The resume content may be corrupted.');
    }
  }
  return {} as ResumeData;
}

/**
 * Parse spacing level from string, clamped to valid range 1-5
 */
function parseSpacingLevel(value: string | undefined, defaultValue: SpacingLevel): SpacingLevel {
  if (!value) return defaultValue;
  const num = parseInt(value, 10);
  if (isNaN(num) || num < 1 || num > 5) return defaultValue;
  return num as SpacingLevel;
}

/**
 * Parse margin value from string, clamped to valid range 5-25
 */
function parseMargin(value: string | undefined, defaultValue: number): number {
  if (!value) return defaultValue;
  const num = parseInt(value, 10);
  if (isNaN(num)) return defaultValue;
  return Math.max(5, Math.min(25, num));
}

/**
 * Validate template type
 */
function parseTemplate(value: string | undefined): TemplateType {
  // Allow-list mirrors TEMPLATE_OPTIONS in lib/types/template-settings.ts ÔÇö keep in sync.
  if (
    value === 'swiss-single' ||
    value === 'swiss-two-column' ||
    value === 'modern' ||
    value === 'modern-two-column' ||
    value === 'latex' ||
    value === 'clean' ||
    value === 'vivid'
  ) {
    return value;
  }
  return 'swiss-single';
}

/**
 * Validate page size
 */
function parsePageSize(value: string | undefined): PageSize {
  if (value === 'A4' || value === 'LETTER') {
    return value;
  }
  return 'A4';
}

export default async function PrintResumePage({ params, searchParams }: PageProps) {
  const resolvedParams = await params;
  const resolvedSearchParams = searchParams ? await searchParams : undefined;
  const resumeData = await fetchResumeData(resolvedParams.id);
  const locale = resolveLocale(resolvedSearchParams?.lang);
  const t = (key: string, params?: Record<string, string | number>) =>
    translate(locale, key, params);
  const localizedResumeData = withLocalizedDefaultSections(resumeData, t);
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
  const fallbackLabels = {
    name: t('resume.defaults.name'),
  };

  // Parse template settings from query params
  const settings: TemplateSettings = {
    template: parseTemplate(resolvedSearchParams?.template),
    pageSize: parsePageSize(resolvedSearchParams?.pageSize),
    margins: {
      top: parseMargin(resolvedSearchParams?.marginTop, DEFAULT_TEMPLATE_SETTINGS.margins.top),
      bottom: parseMargin(
        resolvedSearchParams?.marginBottom,
        DEFAULT_TEMPLATE_SETTINGS.margins.bottom
      ),
      left: parseMargin(resolvedSearchParams?.marginLeft, DEFAULT_TEMPLATE_SETTINGS.margins.left),
      right: parseMargin(
        resolvedSearchParams?.marginRight,
        DEFAULT_TEMPLATE_SETTINGS.margins.right
      ),
    },
    spacing: {
      section: parseSpacingLevel(
        resolvedSearchParams?.sectionSpacing,
        DEFAULT_TEMPLATE_SETTINGS.spacing.section
      ),
      item: parseSpacingLevel(
        resolvedSearchParams?.itemSpacing,
        DEFAULT_TEMPLATE_SETTINGS.spacing.item
      ),
      lineHeight: parseSpacingLevel(
        resolvedSearchParams?.lineHeight,
        DEFAULT_TEMPLATE_SETTINGS.spacing.lineHeight
      ),
    },
    fontSize: {
      base: parseSpacingLevel(
        resolvedSearchParams?.fontSize,
        DEFAULT_TEMPLATE_SETTINGS.fontSize.base
      ),
      headerScale: parseSpacingLevel(
        resolvedSearchParams?.headerScale,
        DEFAULT_TEMPLATE_SETTINGS.fontSize.headerScale
      ),
      headerFont: parseHeaderFont(resolvedSearchParams?.headerFont),
      bodyFont: parseBodyFont(resolvedSearchParams?.bodyFont),
      headerWeight: parseFontWeight(
        resolvedSearchParams?.headerWeight,
        DEFAULT_TEMPLATE_SETTINGS.fontSize.headerWeight
      ),
      bodyWeight: parseFontWeight(
        resolvedSearchParams?.bodyWeight,
        DEFAULT_TEMPLATE_SETTINGS.fontSize.bodyWeight
      ),
    },
    compactMode: parseBoolean(
      resolvedSearchParams?.compactMode,
      DEFAULT_TEMPLATE_SETTINGS.compactMode
    ),
    showContactIcons: parseBoolean(
      resolvedSearchParams?.showContactIcons,
      DEFAULT_TEMPLATE_SETTINGS.showContactIcons
    ),
    accentColor: parseAccentColor(resolvedSearchParams?.accentColor),
    maxPages: (resolvedSearchParams?.maxPages === '2' ? 2 : 1) as 1 | 2,
  };

  // Note: Margins are applied via @page CSS rule above so every page gets them
  // The Resume component gets zero margins so content fills to the @page margins
  const printSettings: TemplateSettings = {
    ...settings,
    // Zero out margins in CSS since @page rule handles them per-page
    margins: { top: 0, bottom: 0, left: 0, right: 0 },
  };

  return (
    <>
      <head>
        {/* Load web fonts so Playwright PDF output matches the browser preview exactly */}
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link
          href="https://fonts.googleapis.com/css2?family=Libre+Baskerville:ital,wght@0,400;0,700;1,400&family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap"
          rel="stylesheet"
        />
        {/* Print-specific CSS to ensure perfect rendering */}
        <style>{`
          @page {
            size: ${settings.pageSize === 'A4' ? '210mm 297mm' : '215.9mm 279.4mm'};
            margin: ${settings.margins.top}mm ${settings.margins.right}mm ${settings.margins.bottom}mm ${settings.margins.left}mm;
          }
          html, body {
            margin: 0 !important;
            padding: 0 !important;
            width: 100% !important;
            background: white !important;
            -webkit-print-color-adjust: exact !important;
            print-color-adjust: exact !important;
          }
          .resume-print {
            width: 100%;
            background: white;
            /* Remove overflow hidden - it cuts off content and doesn't help with blank pages */
            display: block;
          }
          /* Remove all bottom padding/margin from last section to prevent whitespace */
          .resume-section:last-child {
            margin-bottom: 0 !important;
            padding-bottom: 0 !important;
          }
          .resume-item:last-child {
            margin-bottom: 0 !important;
          }
          .resume-items:last-child {
            padding-bottom: 0 !important;
          }
        `}</style>
      </head>
      <div className="resume-print bg-white">
        <Resume
          resumeData={localizedResumeData}
          template={settings.template}
          settings={printSettings}
          additionalSectionLabels={additionalSectionLabels}
          sectionHeadings={sectionHeadings}
          fallbackLabels={fallbackLabels}
        />
      </div>
    </>
  );
}