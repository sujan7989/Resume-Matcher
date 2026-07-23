import React from 'react';
import { Mail, Phone, MapPin, Globe, Linkedin, Github } from 'lucide-react';
import type { ResumeData, AdditionalSectionLabels } from '@/components/dashboard/resume-component';
import { getSortedSections } from '@/lib/utils/section-helpers';
import { formatDateRange } from '@/lib/utils';
import { SafeHtml } from './safe-html';
import baseStyles from './styles/_base.module.css';
import styles from './styles/nova.module.css';

interface ResumeNovaProps {
  data: ResumeData;
  showContactIcons?: boolean;
  additionalSectionLabels?: Partial<AdditionalSectionLabels>;
}

/**
 * Nova Student Template
 *
 * Single-column ATS-friendly layout for students and fresh graduates.
 * Bold accent stripe under name, skill chips, clean sans-serif typography.
 */
export const ResumeNova: React.FC<ResumeNovaProps> = ({
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

  const renderContactDetail = (label: string, value?: string, hrefPrefix = '') => {
    if (!value) return null;
    let prefix = hrefPrefix;
    if (['Website', 'LinkedIn', 'GitHub'].includes(label) && !value.startsWith('http')) {
      prefix = 'https://';
    }
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

  const mergedLabels = {
    technicalSkills: additionalSectionLabels?.technicalSkills ?? 'Technical Skills:',
    languages: additionalSectionLabels?.languages ?? 'Languages:',
    certifications: additionalSectionLabels?.certifications ?? 'Certifications:',
    awards: additionalSectionLabels?.awards ?? 'Awards:',
  };

  const clean = (items?: string[]) =>
    (items ?? []).filter((i): i is string => typeof i === 'string' && i.trim() !== '');

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
            <div className={baseStyles['resume-items']}>
              {workExperience.map((exp) => (
                <div key={exp.id} className={baseStyles['resume-item']}>
                  <div
                    className={`flex justify-between items-baseline ${baseStyles['resume-row-tight']}`}
                  >
                    <h4 className={baseStyles['resume-item-title']}>{exp.title}</h4>
                    <span className={baseStyles['resume-date']}>{formatDateRange(exp.years)}</span>
                  </div>
                  <div
                    className={`flex justify-between ${baseStyles['resume-item-subtitle']} ${baseStyles['resume-row']}`}
                  >
                    <span>{exp.company}</span>
                    {exp.location && <span>{exp.location}</span>}
                  </div>
                  {exp.description?.length ? (
                    <ul
                      className={`ml-4 ${baseStyles['resume-list']} ${baseStyles['resume-text-sm']}`}
                    >
                      {exp.description.map((d, i) => (
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
              ))}
            </div>
          </div>
        );
      case 'education':
        if (!education?.length) return null;
        return (
          <div key={section.id} className={baseStyles['resume-section']}>
            <h3 className={styles.sectionTitle}>{section.displayName}</h3>
            <div className={baseStyles['resume-items']}>
              {education.map((edu) => (
                <div key={edu.id} className={baseStyles['resume-item']}>
                  <div
                    className={`flex justify-between items-baseline ${baseStyles['resume-row-tight']}`}
                  >
                    <h4 className={baseStyles['resume-item-title']}>{edu.institution}</h4>
                    <span className={baseStyles['resume-date']}>{formatDateRange(edu.years)}</span>
                  </div>
                  <div
                    className={`${baseStyles['resume-item-subtitle']} ${baseStyles['resume-row-tight']}`}
                  >
                    {edu.degree}
                  </div>
                  {edu.description && (
                    <p className={baseStyles['resume-text-sm']}>{edu.description}</p>
                  )}
                </div>
              ))}
            </div>
          </div>
        );
      case 'personalProjects':
        if (!personalProjects?.length) return null;
        return (
          <div key={section.id} className={baseStyles['resume-section']}>
            <h3 className={styles.sectionTitle}>{section.displayName}</h3>
            <div className={baseStyles['resume-items']}>
              {personalProjects.map((p) => (
                <div key={p.id} className={baseStyles['resume-item']}>
                  <div
                    className={`flex justify-between items-baseline ${baseStyles['resume-row-tight']}`}
                  >
                    <h4 className={baseStyles['resume-item-title']}>{p.name}</h4>
                    {p.years && (
                      <span className={baseStyles['resume-date']}>{formatDateRange(p.years)}</span>
                    )}
                  </div>
                  {p.role && (
                    <div
                      className={`${baseStyles['resume-item-subtitle']} ${baseStyles['resume-row']}`}
                    >
                      {p.role}
                    </div>
                  )}
                  {p.description?.length ? (
                    <ul
                      className={`ml-4 ${baseStyles['resume-list']} ${baseStyles['resume-text-sm']}`}
                    >
                      {p.description.map((d, i) => (
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
              ))}
            </div>
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
                <div>
                  <span className="font-bold mr-1">{mergedLabels.technicalSkills}</span>
                  <span className={styles.skillsWrap}>
                    {skills.map((s, i) => (
                      <span key={i} className={styles.skillChip}>
                        {s}
                      </span>
                    ))}
                  </span>
                </div>
              )}
              {langs.length > 0 && (
                <div className="flex">
                  <span className="font-bold w-28 shrink-0">{mergedLabels.languages}</span>
                  <span>{langs.join(', ')}</span>
                </div>
              )}
              {certs.length > 0 && (
                <div className="flex">
                  <span className="font-bold w-28 shrink-0">{mergedLabels.certifications}</span>
                  <span>{certs.join(', ')}</span>
                </div>
              )}
              {awards.length > 0 && (
                <div className="flex">
                  <span className="font-bold w-28 shrink-0">{mergedLabels.awards}</span>
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

  return (
    <div className={styles.container}>
      {personalInfo && (
        <header className={`text-center ${baseStyles['resume-header']}`}>
          {personalInfo.name && (
            <h1 className={`${baseStyles['resume-name']} uppercase tracking-tight`}>
              {personalInfo.name}
            </h1>
          )}
          {personalInfo.title && (
            <h2
              className={`${baseStyles['resume-title']} ${baseStyles['resume-meta']} tracking-wide mt-1`}
            >
              {personalInfo.title}
            </h2>
          )}
          <div className={styles.headerAccentBar} />
          <div
            className={`flex flex-wrap justify-center gap-x-3 gap-y-1 mt-2 ${baseStyles['resume-meta']}`}
          >
            {renderContactDetail('Email', personalInfo.email, 'mailto:')}
            {personalInfo.phone && <>{renderContactDetail('Phone', personalInfo.phone, 'tel:')}</>}
            {personalInfo.location && <>{renderContactDetail('Location', personalInfo.location)}</>}
            {personalInfo.website && <>{renderContactDetail('Website', personalInfo.website)}</>}
            {personalInfo.linkedin && <>{renderContactDetail('LinkedIn', personalInfo.linkedin)}</>}
            {personalInfo.github && <>{renderContactDetail('GitHub', personalInfo.github)}</>}
          </div>
        </header>
      )}
      {sortedSections.filter((s) => s.key !== 'personalInfo').map((s) => renderSection(s))}
    </div>
  );
};

export default ResumeNova;
