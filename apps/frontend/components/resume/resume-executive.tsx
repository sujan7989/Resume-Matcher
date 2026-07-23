import React from 'react';
import { Mail, Phone, MapPin, Globe, Linkedin, Github } from 'lucide-react';
import type { ResumeData, AdditionalSectionLabels } from '@/components/dashboard/resume-component';
import { getSortedSections } from '@/lib/utils/section-helpers';
import { formatDateRange } from '@/lib/utils';
import { SafeHtml } from './safe-html';
import baseStyles from './styles/_base.module.css';
import styles from './styles/executive.module.css';

interface ResumeExecutiveProps {
  data: ResumeData;
  showContactIcons?: boolean;
  additionalSectionLabels?: Partial<AdditionalSectionLabels>;
}

/**
 * Executive Template
 * Senior professional layout: double-underline name, small-caps section headers,
 * clean serif typography optimised for managers and senior engineers.
 */
export const ResumeExecutive: React.FC<ResumeExecutiveProps> = ({
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
                    <div>
                      <span className={styles.entryTitle}>{exp.title}</span>
                      {exp.company && <span className={styles.entryOrg}>, {exp.company}</span>}
                    </div>
                    <span className={styles.entryDate}>{formatDateRange(exp.years)}</span>
                  </div>
                  {exp.location && (
                    <div
                      className={`${baseStyles['resume-text-sm']} ${baseStyles['resume-row']}`}
                      style={{ color: 'var(--resume-text-tertiary)' }}
                    >
                      {exp.location}
                    </div>
                  )}
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
                    <div>
                      <span className={styles.entryTitle}>{edu.institution}</span>
                      {edu.degree && <span className={styles.entryOrg}>, {edu.degree}</span>}
                    </div>
                    <span className={styles.entryDate}>{formatDateRange(edu.years)}</span>
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
                    <span className={styles.entryTitle}>{p.name}</span>
                    {p.years && (
                      <span className={styles.entryDate}>{formatDateRange(p.years)}</span>
                    )}
                  </div>
                  {p.role && (
                    <div className={`${styles.entryOrg} ${baseStyles['resume-row-tight']}`}>
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
        <header className={`text-center ${baseStyles['resume-header']}`}>
          {personalInfo.name && <h1 className={styles.name}>{personalInfo.name}</h1>}
          <div className={styles.nameUnderline}>
            <div className={styles.nameUnderlinePrimary} />
            <div className={styles.nameUnderlineSecondary} />
          </div>
          {personalInfo.title && (
            <div
              className={`${baseStyles['resume-title']} mt-3`}
              style={{ color: 'var(--resume-text-secondary)' }}
            >
              {personalInfo.title}
            </div>
          )}
          {contactItems.length > 0 && (
            <div
              className={`flex flex-wrap justify-center items-center gap-x-3 gap-y-1 mt-2 ${styles.contactRow}`}
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

export default ResumeExecutive;
