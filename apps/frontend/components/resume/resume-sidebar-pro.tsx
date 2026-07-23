import React from 'react';
import { Mail, Phone, MapPin, Globe, Linkedin, Github } from 'lucide-react';
import type {
  ResumeData,
  ResumeSectionHeadings,
  ResumeFallbackLabels,
} from '@/components/dashboard/resume-component';
import { getSortedSections, getSectionMeta } from '@/lib/utils/section-helpers';
import { formatDateRange } from '@/lib/utils';
import { SafeHtml } from './safe-html';
import baseStyles from './styles/_base.module.css';
import styles from './styles/sidebar-pro.module.css';

interface ResumeSidebarProProps {
  data: ResumeData;
  showContactIcons?: boolean;
  sectionHeadings?: Partial<ResumeSectionHeadings>;
  fallbackLabels?: Partial<ResumeFallbackLabels>;
}

/**
 * Sidebar Pro Template
 * Two-column layout: dark accent left sidebar (contact, skills, education) +
 * white main content (summary, experience, projects).
 * Professional and visually distinct; accent color drives sidebar background.
 */
export const ResumeSidebarPro: React.FC<ResumeSidebarProProps> = ({
  data,
  showContactIcons = false,
  sectionHeadings,
  fallbackLabels,
}) => {
  const { personalInfo, summary, workExperience, education, personalProjects, additional } = data;
  const sortedSections = getSortedSections(data);
  const allSections = getSectionMeta(data);

  const nameFallback = fallbackLabels?.name ?? 'Your Name';
  const hf: ResumeSectionHeadings = {
    summary: sectionHeadings?.summary ?? 'Summary',
    experience: sectionHeadings?.experience ?? 'Experience',
    education: sectionHeadings?.education ?? 'Education',
    projects: sectionHeadings?.projects ?? 'Projects',
    certifications: sectionHeadings?.certifications ?? 'Certifications',
    skills: sectionHeadings?.skills ?? 'Skills',
    languages: sectionHeadings?.languages ?? 'Languages',
    awards: sectionHeadings?.awards ?? 'Awards',
    links: sectionHeadings?.links ?? 'Links',
  };

  const isSectionVisible = (key: string) =>
    allSections.find((s) => s.key === key)?.isVisible ?? true;
  const getSectionName = (key: string, fallback: string) =>
    sortedSections.find((s) => s.key === key)?.displayName ?? fallback;

  const clean = (arr?: string[]) =>
    (arr ?? []).filter((i): i is string => typeof i === 'string' && i.trim() !== '');

  const contactIcons: Record<string, React.ReactNode> = {
    Email: <Mail size={11} />,
    Phone: <Phone size={11} />,
    Location: <MapPin size={11} />,
    Website: <Globe size={11} />,
    LinkedIn: <Linkedin size={11} />,
    GitHub: <Github size={11} />,
  };

  const renderSidebarContact = (label: string, value?: string, prefix = '') => {
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
    if (label === 'Email' || label === 'Phone') display = value;
    if (label === 'Location') display = value;
    return (
      <div className="flex items-start gap-1.5 mb-1">
        {showContactIcons && (
          <span style={{ color: 'rgba(255,255,255,0.7)', marginTop: '0.15rem' }}>
            {contactIcons[label]}
          </span>
        )}
        {isLink ? (
          <a href={href} target="_blank" rel="noopener noreferrer" className={styles.sidebarLink}>
            {display}
          </a>
        ) : (
          <span className={styles.sidebarText}>{display}</span>
        )}
      </div>
    );
  };

  const skills = clean(additional?.technicalSkills);
  const langs = clean(additional?.languages);
  const certs = clean(additional?.certificationsTraining);
  const awards = clean(additional?.awards);

  return (
    <div className={styles.wrapper}>
      {/* ── Left Sidebar ────────────────────────────────────────────── */}
      <div className={styles.sidebar}>
        {/* Name + title */}
        <div>
          <div className={styles.sidebarName}>{personalInfo?.name ?? nameFallback}</div>
          {personalInfo?.title && <div className={styles.sidebarTitle}>{personalInfo.title}</div>}
        </div>

        {/* Contact */}
        {personalInfo && (
          <div>
            <div className={styles.sidebarSectionTitle}>Contact</div>
            {renderSidebarContact('Email', personalInfo.email, 'mailto:')}
            {renderSidebarContact('Phone', personalInfo.phone, 'tel:')}
            {renderSidebarContact('Location', personalInfo.location)}
            {renderSidebarContact('LinkedIn', personalInfo.linkedin)}
            {renderSidebarContact('GitHub', personalInfo.github)}
            {renderSidebarContact('Website', personalInfo.website)}
          </div>
        )}

        {/* Skills */}
        {isSectionVisible('additional') && skills.length > 0 && (
          <div>
            <div className={styles.sidebarSectionTitle}>{hf.skills}</div>
            {skills.map((s, i) => (
              <span key={i} className={styles.sidebarSkill}>
                {s}
              </span>
            ))}
          </div>
        )}

        {/* Languages */}
        {isSectionVisible('additional') && langs.length > 0 && (
          <div>
            <div className={styles.sidebarSectionTitle}>{hf.languages}</div>
            <div className={styles.sidebarText}>{langs.join(' · ')}</div>
          </div>
        )}

        {/* Education */}
        {isSectionVisible('education') && education?.length ? (
          <div>
            <div className={styles.sidebarSectionTitle}>
              {getSectionName('education', hf.education)}
            </div>
            {education.map((edu) => (
              <div key={edu.id} className="mb-2">
                <div className={styles.sidebarText} style={{ fontWeight: 600 }}>
                  {edu.institution}
                </div>
                <div className={styles.sidebarText}>{edu.degree}</div>
                {edu.years && (
                  <div
                    className={`${styles.sidebarText}`}
                    style={{ opacity: 0.7, fontSize: 'calc(var(--font-size-base) * 0.78)' }}
                  >
                    {formatDateRange(edu.years)}
                  </div>
                )}
              </div>
            ))}
          </div>
        ) : null}

        {/* Awards */}
        {isSectionVisible('additional') && awards.length > 0 && (
          <div>
            <div className={styles.sidebarSectionTitle}>{hf.awards}</div>
            {awards.map((a, i) => (
              <div key={i} className={styles.sidebarText}>
                {a}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* ── Main Content ─────────────────────────────────────────────── */}
      <div className={styles.main}>
        {/* Summary */}
        {isSectionVisible('summary') && summary && (
          <div>
            <h3 className={styles.mainSectionTitle}>{getSectionName('summary', hf.summary)}</h3>
            <p className={`text-justify ${baseStyles['resume-text']}`}>{summary}</p>
          </div>
        )}

        {/* Experience */}
        {isSectionVisible('workExperience') && workExperience?.length ? (
          <div>
            <h3 className={styles.mainSectionTitle}>
              {getSectionName('workExperience', hf.experience)}
            </h3>
            <div className={baseStyles['resume-items']}>
              {workExperience.map((exp) => (
                <div key={exp.id} className={baseStyles['resume-item']}>
                  <div
                    className={`flex justify-between items-baseline ${baseStyles['resume-row-tight']}`}
                  >
                    <div>
                      <span className={styles.entryTitle}>{exp.title}</span>
                      {exp.company && <span className={styles.entryOrg}> · {exp.company}</span>}
                    </div>
                    <span className={styles.entryDate}>{formatDateRange(exp.years)}</span>
                  </div>
                  {exp.location && (
                    <div
                      className={`${baseStyles['resume-text-xs']} ${baseStyles['resume-row-tight']}`}
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
        ) : null}

        {/* Projects */}
        {isSectionVisible('personalProjects') && personalProjects?.length ? (
          <div>
            <h3 className={styles.mainSectionTitle}>
              {getSectionName('personalProjects', hf.projects)}
            </h3>
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
        ) : null}

        {/* Certifications */}
        {isSectionVisible('additional') && certs.length > 0 && (
          <div>
            <h3 className={styles.mainSectionTitle}>{hf.certifications}</h3>
            <ul className={`ml-4 ${baseStyles['resume-list']} ${baseStyles['resume-text-sm']}`}>
              {certs.map((c, i) => (
                <li key={i} className="flex">
                  <span className="mr-1.5 shrink-0">•&nbsp;</span>
                  <span>{c}</span>
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </div>
  );
};

export default ResumeSidebarPro;
