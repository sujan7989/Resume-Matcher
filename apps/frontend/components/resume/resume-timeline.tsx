import React from 'react';
import { Mail, Phone, MapPin, Globe, Linkedin, Github } from 'lucide-react';
import type { ResumeData, AdditionalSectionLabels } from '@/components/dashboard/resume-component';
import { getSortedSections } from '@/lib/utils/section-helpers';
import { formatDateRange } from '@/lib/utils';
import { SafeHtml } from './safe-html';
import baseStyles from './styles/_base.module.css';
import styles from './styles/timeline.module.css';

interface ResumeTimelineProps {
  data: ResumeData;
  showContactIcons?: boolean;
  additionalSectionLabels?: Partial<AdditionalSectionLabels>;
}

/**
 * Timeline Pro Template
 * Single-column with accent left-border section titles and timeline dots on entries.
 * For experienced engineers who want visual hierarchy without color overload.
 */
export const ResumeTimeline: React.FC<ResumeTimelineProps> = ({
  data,
  showContactIcons = false,
  additionalSectionLabels,
}) => {
  const { personalInfo, summary, workExperience, education, personalProjects, additional } = data;
  const sortedSections = getSortedSections(data);

  const contactIcons: Record<string, React.ReactNode> = {
    Email: <Mail size={12} />,
    Phone: <Phone size={12} />,
    Location: <MapPin size={12} />,
    Website: <Globe size={12} />,
    LinkedIn: <Linkedin size={12} />,
    GitHub: <Github size={12} />,
  };

  const renderContact = (label: string, value?: string, prefix = '') => {
    if (!value) return null;
    if (['Website', 'LinkedIn', 'GitHub'].includes(label) && !value.startsWith('http'))
      prefix = 'https://';
    const isLink =
      prefix.startsWith('http') ||
      prefix.startsWith('mailto:') ||
      prefix.startsWith('tel:') ||
      value.startsWith('http');
    const href = value.startsWith('http') ? value : prefix + value;
    let display = value;
    if (isLink && label === 'LinkedIn') display = 'LinkedIn';
    if (isLink && label === 'GitHub') display = 'GitHub';
    if (isLink && label === 'Website') display = 'Portfolio';
    return (
      <span className="inline-flex items-center gap-1">
        {showContactIcons && contactIcons[label]}
        {isLink ? (
          <a
            href={href}
            target="_blank"
            rel="noopener noreferrer"
            className={baseStyles['resume-link']}
          >
            {display}
          </a>
        ) : (
          <span>{display}</span>
        )}
      </span>
    );
  };

  const clean = (arr?: string[]) =>
    (arr ?? []).filter((i): i is string => typeof i === 'string' && i.trim() !== '');
  const mergedLabels = {
    technicalSkills: additionalSectionLabels?.technicalSkills ?? 'Technical Skills:',
    languages: additionalSectionLabels?.languages ?? 'Languages:',
    certifications: additionalSectionLabels?.certifications ?? 'Certifications:',
    awards: additionalSectionLabels?.awards ?? 'Awards:',
  };

  /** Renders experience/project items with timeline track on the left */
  const renderTimelineItem = (
    key: number,
    title: React.ReactNode,
    sub: React.ReactNode,
    date: string | undefined,
    bullets?: string[],
    isLast = false
  ) => (
    <div key={key} className={styles.timelineItem}>
      <div className={styles.timelineTrack}>
        <div className={styles.timelineDot} />
        {!isLast && <div className={styles.timelineLine} />}
      </div>
      <div className={styles.timelineContent}>
        <div
          className={`flex justify-between items-baseline gap-2 ${baseStyles['resume-row-tight']}`}
        >
          <div>{title}</div>
          {date && <span className={styles.entryDate}>{formatDateRange(date)}</span>}
        </div>
        {sub}
        {bullets?.length ? (
          <ul className={`ml-2 ${baseStyles['resume-list']} ${baseStyles['resume-text-sm']}`}>
            {bullets.map((d, i) => (
              <li key={i} className="flex">
                <span className="mr-1.5 shrink-0">•&nbsp;</span>
                <span>
                  <SafeHtml html={d} />
                </span>
              </li>
            ))}
          </ul>
        ) : null}
      </div>
    </div>
  );

  const renderSection = (section: (typeof sortedSections)[0]) => {
    switch (section.key) {
      case 'personalInfo':
        return null;
      case 'summary':
        if (!summary) return null;
        return (
          <div key={section.id} className={baseStyles['resume-section']}>
            <h3 className={styles.sectionTitle}>{section.displayName}</h3>
            <p className={`text-justify ${baseStyles['resume-text']}`}>{summary}</p>
          </div>
        );
      case 'workExperience':
        if (!workExperience?.length) return null;
        return (
          <div key={section.id} className={baseStyles['resume-section']}>
            <h3 className={styles.sectionTitle}>{section.displayName}</h3>
            {workExperience.map((exp, idx) =>
              renderTimelineItem(
                exp.id,
                <>
                  <span className={styles.entryTitle}>{exp.title}</span>
                  {exp.company && <span className={styles.entryOrg}> · {exp.company}</span>}
                </>,
                exp.location ? (
                  <div
                    className={baseStyles['resume-text-xs']}
                    style={{ color: 'var(--resume-text-tertiary)' }}
                  >
                    {exp.location}
                  </div>
                ) : null,
                exp.years,
                exp.description,
                idx === workExperience.length - 1
              )
            )}
          </div>
        );
      case 'education':
        if (!education?.length) return null;
        return (
          <div key={section.id} className={baseStyles['resume-section']}>
            <h3 className={styles.sectionTitle}>{section.displayName}</h3>
            {education.map((edu, idx) =>
              renderTimelineItem(
                edu.id,
                <>
                  <span className={styles.entryTitle}>{edu.institution}</span>
                </>,
                <div
                  className={baseStyles['resume-text-sm']}
                  style={{ color: 'var(--resume-text-secondary)' }}
                >
                  {edu.degree}
                </div>,
                edu.years,
                edu.description ? [edu.description] : undefined,
                idx === education.length - 1
              )
            )}
          </div>
        );
      case 'personalProjects':
        if (!personalProjects?.length) return null;
        return (
          <div key={section.id} className={baseStyles['resume-section']}>
            <h3 className={styles.sectionTitle}>{section.displayName}</h3>
            {personalProjects.map((p, idx) =>
              renderTimelineItem(
                p.id,
                <span className={styles.entryTitle}>{p.name}</span>,
                p.role ? (
                  <div
                    className={baseStyles['resume-text-sm']}
                    style={{ color: 'var(--resume-text-secondary)' }}
                  >
                    {p.role}
                  </div>
                ) : null,
                p.years,
                p.description,
                idx === personalProjects.length - 1
              )
            )}
          </div>
        );
      case 'additional': {
        if (!additional) return null;
        const skills = clean(additional.technicalSkills);
        const langs = clean(additional.languages);
        const certs = clean(additional.certificationsTraining);
        const awards = clean(additional.awards);
        if (!skills.length && !langs.length && !certs.length && !awards.length) return null;
        return (
          <div key={section.id} className={baseStyles['resume-section']}>
            <h3 className={styles.sectionTitle}>{section.displayName}</h3>
            <div className={`${baseStyles['resume-stack']} ${baseStyles['resume-text-sm']}`}>
              {skills.length > 0 && (
                <div className="flex">
                  <span className="font-bold w-32 shrink-0">{mergedLabels.technicalSkills}</span>
                  <span>{skills.join(', ')}</span>
                </div>
              )}
              {langs.length > 0 && (
                <div className="flex">
                  <span className="font-bold w-32 shrink-0">{mergedLabels.languages}</span>
                  <span>{langs.join(', ')}</span>
                </div>
              )}
              {certs.length > 0 && (
                <div className="flex">
                  <span className="font-bold w-32 shrink-0">{mergedLabels.certifications}</span>
                  <span>{certs.join(', ')}</span>
                </div>
              )}
              {awards.length > 0 && (
                <div className="flex">
                  <span className="font-bold w-32 shrink-0">{mergedLabels.awards}</span>
                  <span>{awards.join(', ')}</span>
                </div>
              )}
            </div>
          </div>
        );
      }
      default:
        return null;
    }
  };

  const contactItems = [
    renderContact('Email', personalInfo?.email, 'mailto:'),
    renderContact('Phone', personalInfo?.phone, 'tel:'),
    renderContact('Location', personalInfo?.location),
    renderContact('LinkedIn', personalInfo?.linkedin),
    renderContact('GitHub', personalInfo?.github),
    renderContact('Website', personalInfo?.website),
  ].filter(Boolean);

  return (
    <div className={styles.container}>
      {personalInfo && (
        <header
          className={`text-center ${baseStyles['resume-header']} border-b`}
          style={{ borderColor: 'var(--resume-border-secondary)' }}
        >
          {personalInfo.name && (
            <h1 className={`${baseStyles['resume-name']} tracking-tight uppercase`}>
              {personalInfo.name}
            </h1>
          )}
          {personalInfo.title && (
            <h2
              className={`${baseStyles['resume-title']} ${baseStyles['resume-meta']} uppercase tracking-wide mt-1`}
            >
              {personalInfo.title}
            </h2>
          )}
          {contactItems.length > 0 && (
            <div
              className={`flex flex-wrap justify-center items-center gap-x-3 gap-y-1 mt-2 ${baseStyles['resume-meta']}`}
            >
              {contactItems.map((item, i) => (
                <React.Fragment key={i}>
                  {i > 0 && <span style={{ color: 'var(--resume-text-tertiary)' }}>·</span>}
                  {item}
                </React.Fragment>
              ))}
            </div>
          )}
        </header>
      )}
      {sortedSections.filter((s) => s.key !== 'personalInfo').map((s) => renderSection(s))}
    </div>
  );
};

export default ResumeTimeline;
