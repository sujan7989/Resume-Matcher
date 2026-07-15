"""PDF rendering from resume data.

Generates PDF directly from resume JSON using HTML + Playwright (or fpdf2 fallback).
The HTML is built in-memory so there are NO network calls - works reliably on any host.
"""
from __future__ import annotations
import asyncio
import logging
import os
import sys
from typing import Any, Optional

logger = logging.getLogger(__name__)

_NAV_TIMEOUT_MS = 60_000


class PDFRenderError(Exception):
    pass


_playwright_instance = None
_browser_instance = None
_init_lock = asyncio.Lock()
_playwright_ok: Optional[bool] = None


async def _is_playwright_available() -> bool:
    global _playwright_ok
    if _playwright_ok is not None:
        return _playwright_ok
    try:
        from playwright.async_api import async_playwright
        async with async_playwright() as p:
            b = await p.chromium.launch()
            await b.close()
        _playwright_ok = True
        logger.info("Playwright/Chromium available")
    except Exception as e:
        _playwright_ok = False
        logger.warning(f"Playwright not available ({e}), will use fpdf2")
    return _playwright_ok


async def init_pdf_renderer() -> None:
    global _playwright_instance, _browser_instance
    if _browser_instance:
        return
    async with _init_lock:
        if _browser_instance:
            return
        if not await _is_playwright_available():
            return
        try:
            from playwright.async_api import async_playwright
            _playwright_instance = await async_playwright().start()
            _browser_instance = await _playwright_instance.chromium.launch()
            logger.info("Playwright browser started")
        except Exception as e:
            logger.warning(f"Browser start failed: {e}")
            _playwright_instance = None
            _browser_instance = None


async def close_pdf_renderer() -> None:
    global _playwright_instance, _browser_instance
    if _browser_instance:
        try:
            await _browser_instance.close()
        except Exception:
            pass
        _browser_instance = None
    if _playwright_instance:
        try:
            await _playwright_instance.stop()
        except Exception:
            pass
        _playwright_instance = None


def _safe(val: Any) -> str:
    """Convert to string and escape HTML special characters."""
    if val is None:
        return ""
    import html
    return html.escape(str(val))


def _build_resume_html(data: dict, template: str, page_size: str, margins: dict) -> str:
    """Build a complete, styled HTML document from resume JSON.
    
    Respects template choice: single, two-column, modern, latex, clean, vivid.
    Designed for Playwright PDF rendering - 1 page, ATS-friendly.
    """
    mt = margins.get("top", 12)
    mb = margins.get("bottom", 12)
    ml = margins.get("left", 18)
    mr = margins.get("right", 18)

    personal = data.get("personalInfo") or {}
    name = _safe(personal.get("name", ""))
    title = _safe(personal.get("title", ""))
    email = _safe(personal.get("email", ""))
    phone = _safe(personal.get("phone", ""))
    location = _safe(personal.get("location", ""))
    website = _safe(personal.get("website") or "")
    linkedin = _safe(personal.get("linkedin") or "")
    github = _safe(personal.get("github") or "")
    summary = _safe(data.get("summary", ""))

    # Build contact parts with labels for LinkedIn/GitHub/Website
    def _contact_item(value: str, label: str = "") -> str:
        """Return clickable label or plain text for a contact field."""
        if not value:
            return ""
        if label in ("LinkedIn", "GitHub", "Portfolio"):
            href = value if value.startswith("http") else f"https://{value}"
            return f'<a href="{href}" style="color:inherit;text-decoration:underline;">{label}</a>'
        return value

    contact_parts_raw = [
        email,
        phone,
        location,
        _contact_item(website, "Portfolio"),
        _contact_item(linkedin, "LinkedIn"),
        _contact_item(github, "GitHub"),
    ]
    contact_parts = [p for p in contact_parts_raw if p]
    contact_line = " &nbsp;|&nbsp; ".join(contact_parts)

    work_exp = data.get("workExperience") or []
    education = data.get("education") or []
    projects = data.get("personalProjects") or []
    additional = data.get("additional") or {}
    skills = additional.get("technicalSkills") or []
    certs = additional.get("certificationsTraining") or []
    languages = additional.get("languages") or []
    awards = additional.get("awards") or []

    # ── Template-specific CSS ──────────────────────────────────────────────────
    if template in ("swiss-two-column", "modern-two-column"):
        layout_css = """
        .resume-body { display: grid; grid-template-columns: 1fr 2.2fr; gap: 14px; }
        .sidebar { background: #f5f6fa; padding: 8px; border-radius: 4px; }
        .main-col {}
        """
        two_col = True
    else:
        layout_css = ".resume-body { display: block; }"
        two_col = False

    if template == "modern" or template == "modern-two-column":
        accent = "#2563eb"
        header_style = f"background:{accent}; color:white; padding:12px {mr}mm 10px {ml}mm; margin:-{mt}mm -{mr}mm 10px -{ml}mm;"
        name_color = "white"
        section_color = accent
        section_border = f"border-bottom: 2px solid {accent};"
        font_family = "'Liberation Sans', Arial, Helvetica, sans-serif"
    elif template == "latex":
        accent = "#000000"
        header_style = ""
        name_color = "#000"
        section_color = "#000"
        section_border = "border-bottom: 1px solid #000;"
        font_family = "'Liberation Serif', Georgia, 'Times New Roman', serif"
    elif template == "clean":
        accent = "#374151"
        header_style = ""
        name_color = "#111"
        section_color = "#374151"
        section_border = "border-bottom: 1px solid #d1d5db;"
        font_family = "'Liberation Sans', Arial, Helvetica, sans-serif"
    elif template == "vivid":
        accent = "#7c3aed"
        header_style = f"border-left: 5px solid {accent}; padding-left: 10px; margin-bottom: 10px;"
        name_color = accent
        section_color = accent
        section_border = f"border-bottom: 2px solid {accent};"
        font_family = "'Liberation Sans', Arial, Helvetica, sans-serif"
    else:
        # swiss-single (default) - classic ATS
        accent = "#1e40af"
        header_style = ""
        name_color = "#111827"
        section_color = "#1e40af"
        section_border = "border-bottom: 1.5px solid #1e40af;"
        font_family = "'Liberation Sans', Arial, Helvetica, sans-serif"

    page_w = "210mm" if page_size == "A4" else "215.9mm"
    page_h = "297mm" if page_size == "A4" else "279.4mm"

    css = f"""
    @page {{ size: {page_w} {page_h}; margin: {mt}mm {mr}mm {mb}mm {ml}mm; }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{ font-family: {font_family}; font-size: 9pt; color: #222; line-height: 1.35;
           width: {page_w}; }}
    .header {{ {header_style} text-align: center; margin-bottom: 8px; }}
    .name {{ font-size: 20pt; font-weight: bold; color: {name_color}; letter-spacing: 0.5px; }}
    .job-title {{ font-size: 10pt; color: {"#e0e7ff" if "white" == name_color else "#555"}; margin-top: 2px; }}
    .contact {{ font-size: 7.5pt; color: {"#dbeafe" if "white" == name_color else "#666"}; margin-top: 3px; }}
    .section {{ margin-top: 7px; }}
    .section-title {{ font-size: 9.5pt; font-weight: bold; color: {section_color};
                      text-transform: uppercase; letter-spacing: 0.8px; padding-bottom: 1px;
                      {section_border} margin-bottom: 4px; }}
    .item {{ margin-bottom: 4px; }}
    .item-header {{ display: flex; justify-content: space-between; align-items: baseline; }}
    .item-title {{ font-weight: bold; font-size: 9pt; color: #111; }}
    .item-sub {{ font-size: 8.5pt; color: #444; font-style: italic; }}
    .item-date {{ font-size: 8pt; color: #666; white-space: nowrap; margin-left: 6px; }}
    .item-loc {{ font-size: 8pt; color: #666; }}
    ul {{ margin: 2px 0 0 12px; padding: 0; }}
    ul li {{ font-size: 8.5pt; color: #333; margin-bottom: 1px; line-height: 1.3; }}
    .summary-text {{ font-size: 8.5pt; color: #333; line-height: 1.4; }}
    .skills-list {{ font-size: 8.5pt; color: #333; }}
    .skill-tag {{ display: inline-block; background: #f3f4f6; border-radius: 2px;
                  padding: 1px 5px; margin: 1px 2px; font-size: 8pt; color: #374151; }}
    {layout_css}
    """

    # ── Section builders ───────────────────────────────────────────────────────
    def sec(title: str, content: str) -> str:
        return f'<div class="section"><div class="section-title">{title}</div>{content}</div>'

    def item_html(t: str, sub: str, date: str, loc: str, bullets: list) -> str:
        h = '<div class="item">'
        h += '<div class="item-header">'
        h += f'<span class="item-title">{t}</span>'
        if date:
            h += f'<span class="item-date">{date}</span>'
        h += '</div>'
        if sub:
            h += f'<div class="item-sub">{sub}</div>'
        if loc:
            h += f'<div class="item-loc">{loc}</div>'
        if bullets:
            h += '<ul>' + ''.join(f'<li>{_safe(b)}</li>' for b in bullets if b) + '</ul>'
        h += '</div>'
        return h

    # Build sections
    exp_html = ""
    for j in work_exp:
        if not isinstance(j, dict):
            continue
        exp_html += item_html(
            _safe(j.get("title", "")),
            _safe(j.get("company", "")),
            _safe(j.get("years", "")),
            _safe(j.get("location") or ""),
            j.get("description") or []
        )

    edu_html = ""
    for e in education:
        if not isinstance(e, dict):
            continue
        edu_html += item_html(
            _safe(e.get("institution", "")),  # institution = bold title (matches React templates)
            _safe(e.get("degree", "")),        # degree = italic subtitle
            _safe(e.get("years", "")),
            "",
            [e.get("description")] if e.get("description") else []
        )

    proj_html = ""
    for p in projects:
        if not isinstance(p, dict):
            continue
        links = " | ".join(x for x in [_safe(p.get("github") or ""), _safe(p.get("website") or "")] if x)
        proj_html += item_html(
            _safe(p.get("name", "")),
            _safe(p.get("role") or "") + (f" &mdash; {links}" if links else ""),
            _safe(p.get("years") or ""),
            "",
            p.get("description") or []
        )

    skills_html = ""
    if skills:
        tags = "".join(f'<span class="skill-tag">{_safe(s)}</span>' for s in skills if s)
        skills_html = f'<div class="skills-list">{tags}</div>'

    extra_html = ""
    if certs:
        extra_html += sec("Certifications", "<ul>" + "".join(f"<li>{_safe(c)}</li>" for c in certs if c) + "</ul>")
    if languages:
        extra_html += sec("Languages", f'<div class="skills-list">{" &nbsp;|&nbsp; ".join(_safe(l) for l in languages if l)}</div>')
    if awards:
        extra_html += sec("Awards", "<ul>" + "".join(f"<li>{_safe(a)}</li>" for a in awards if a) + "</ul>")

    # ── Layout: single vs two-column ──────────────────────────────────────────
    if two_col:
        sidebar = ""
        if contact_parts:
            sidebar += sec("Contact", f'<div class="summary-text">' + "<br>".join([
                email, phone, location,
                f'<a href="{(linkedin if linkedin.startswith("http") else "https://"+linkedin)}" style="color:inherit;text-decoration:underline;">LinkedIn</a>' if linkedin else "",
                f'<a href="{(github if github.startswith("http") else "https://"+github)}" style="color:inherit;text-decoration:underline;">GitHub</a>' if github else "",
                f'<a href="{(website if website.startswith("http") else "https://"+website)}" style="color:inherit;text-decoration:underline;">Portfolio</a>' if website else "",
            ]) + '</div>')
        if skills:
            sidebar += sec("Skills", skills_html)
        if certs:
            sidebar += sec("Certifications", "<ul>" + "".join(f"<li>{_safe(c)}</li>" for c in certs if c) + "</ul>")
        if languages:
            sidebar += sec("Languages", f'<div class="skills-list">{" | ".join(_safe(l) for l in languages if l)}</div>')
        if awards:
            sidebar += sec("Awards", "<ul>" + "".join(f"<li>{_safe(a)}</li>" for a in awards if a) + "</ul>")

        main = ""
        if summary:
            main += sec("Summary", f'<div class="summary-text">{summary}</div>')
        if exp_html:
            main += sec("Experience", exp_html)
        if edu_html:
            main += sec("Education", edu_html)
        if proj_html:
            main += sec("Projects", proj_html)

        body_content = f'<div class="resume-body"><div class="sidebar">{sidebar}</div><div class="main-col">{main}</div></div>'
    else:
        main = ""
        if summary:
            main += sec("Summary", f'<div class="summary-text">{summary}</div>')
        if exp_html:
            main += sec("Experience", exp_html)
        if edu_html:
            main += sec("Education", edu_html)
        if proj_html:
            main += sec("Projects", proj_html)
        if skills_html:
            main += sec("Technical Skills", skills_html)
        main += extra_html
        body_content = f'<div class="resume-body">{main}</div>'

    header_html = f"""
    <div class="header">
      <div class="name">{name}</div>
      {"<div class='job-title'>" + title + "</div>" if title else ""}
      {"<div class='contact'>" + contact_line + "</div>" if contact_line else ""}
    </div>
    """

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<style>{css}</style>
</head>
<body>
{header_html}
{body_content}
</body>
</html>"""


async def render_resume_pdf(
    url: str,
    page_size: str = "A4",
    selector: str = ".resume-print",
    margins: Optional[dict] = None,
    resume_data: Optional[dict] = None,
    template: str = "swiss-single",
    max_pages: int = 1,
) -> bytes:
    """Generate PDF from the frontend print page.

    Navigates to the frontend print URL with Playwright so the PDF output
    matches the preview exactly (same React components, CSS, fonts, spacing).
    Falls back to building HTML from resume JSON if the frontend is unreachable.
    
    max_pages: 1 = compact single page (preferred for ATS), 2 = allow two pages
    """
    margins = margins or {"top": 12, "bottom": 12, "left": 18, "right": 18}
    # Build Playwright margin strings from the margin dict
    pw_margins = {
        "top": f"{margins.get('top', 10)}mm",
        "right": f"{margins.get('right', 10)}mm",
        "bottom": f"{margins.get('bottom', 10)}mm",
        "left": f"{margins.get('left', 10)}mm",
    }

    # Try Playwright with the frontend print page URL first
    # Only use Playwright if explicitly available AND frontend is reachable
    if await _is_playwright_available():
        try:
            await init_pdf_renderer()
            if _browser_instance:
                page = await _browser_instance.new_page()
                try:
                    logger.info(f"Playwright: navigating to frontend print URL template={template} max_pages={max_pages}")
                    await page.goto(url, wait_until="networkidle", timeout=_NAV_TIMEOUT_MS)
                    
                    # Wait for fonts to load (Google Fonts + system fonts)
                    try:
                        await page.wait_for_function("() => document.fonts.ready.then(() => true)", timeout=10_000)
                        await page.wait_for_timeout(500)
                    except Exception as e:
                        logger.warning(f"Font wait failed: {e}")
                    
                    # Wait for resume content to render
                    try:
                        await page.wait_for_selector(selector, timeout=10_000)
                    except Exception:
                        logger.warning(f"Selector '{selector}' not found, proceeding with whatever is on the page")

                    # Check if page loaded correctly — error pages return empty/error content
                    page_content = await page.content()
                    if any(x in page_content.lower() for x in ["couldn't load", "couldn&#x2019;t load", "server error occurred", "reload to try", "page couldn"]):
                        logger.warning("Print page returned error content, falling back to HTML builder")
                        raise Exception("Print page returned error — frontend unreachable")

                    # Check page has actual resume content (not blank)
                    if len(page_content) < 2000:
                        logger.warning("Print page content too short (%d chars), falling back", len(page_content))
                        raise Exception("Print page content too short — likely error page")

                    pdf_format = "A4" if page_size == "A4" else "Letter"
                    zero_margins = {"top": "0mm", "right": "0mm", "bottom": "0mm", "left": "0mm"}
                    pdf_bytes = await page.pdf(
                        format=pdf_format,
                        print_background=True,
                        margin=zero_margins,
                        prefer_css_page_size=True,
                    )
                    logger.info(f"Playwright PDF from frontend: {len(pdf_bytes)} bytes")
                    return pdf_bytes
                finally:
                    await page.close()
        except Exception as e:
            logger.warning(f"Playwright frontend render failed: {e}, falling back to HTML builder")

    # Fallback: build HTML from resume data (for when frontend is unreachable)
    data = resume_data or {}
    html = _build_resume_html(data, template, page_size, margins)

    if await _is_playwright_available():
        try:
            await init_pdf_renderer()
            if _browser_instance:
                page = await _browser_instance.new_page()
                try:
                    logger.info(f"Playwright fallback: rendering built HTML template={template}")
                    await page.set_content(html, wait_until="domcontentloaded", timeout=_NAV_TIMEOUT_MS)
                    try:
                        await page.wait_for_function("() => document.fonts.ready.then(() => true)", timeout=10_000)
                        await page.wait_for_timeout(300)
                    except Exception as e:
                        logger.warning(f"Font wait failed in fallback: {e}")

                    pdf_format = "A4" if page_size == "A4" else "Letter"
                    if max_pages == 1:
                        pdf_bytes = await page.pdf(
                            format=pdf_format,
                            print_background=True,
                            margin=pw_margins,
                            prefer_css_page_size=True,
                        )
                    else:
                        pdf_bytes = await page.pdf(
                            format=pdf_format,
                            print_background=True,
                            margin=pw_margins,
                        )
                    logger.info(f"Playwright fallback PDF: {len(pdf_bytes)} bytes")
                    return pdf_bytes
                finally:
                    await page.close()
        except Exception as e:
            logger.warning(f"Playwright HTML render failed: {e}, using fpdf2")

    # fpdf2 fallback
    logger.info("Using fpdf2 fallback")
    return _generate_pdf_fpdf2(data, page_size, margins)


def _generate_pdf_fpdf2(data: dict, page_size: str = "A4", margins: Optional[dict] = None) -> bytes:
    """fpdf2 fallback - clean ATS-friendly PDF from resume JSON."""
    from fpdf import FPDF

    ml = (margins or {}).get("left", 18)
    mr = (margins or {}).get("right", 18)
    mt = (margins or {}).get("top", 12)
    mb = (margins or {}).get("bottom", 12)

    pdf = FPDF(format=page_size)
    pdf.set_margins(ml, mt, mr)
    pdf.set_auto_page_break(True, margin=mb)
    pdf.add_page()

    # Track section header state with explicit variables (not hasattr)
    _exp_hdr_done = False
    _edu_hdr_done = False
    _proj_hdr_done = False
    _cert_hdr_done = False

    def s(v: Any) -> str:
        if v is None: return ""
        t = str(v)
        for a, b in {"\u2019":"'","\u2018":"'","\u201c":'"',"\u201d":'"',"\u2013":"-","\u2014":"-","\u2022":"*","\u00e9":"e","\u00e0":"a","\u00f6":"o","\u00fc":"u"}.items():
            t = t.replace(a, b)
        return t

    pw = pdf.w - ml - mr

    def sec_hdr(title: str):
        pdf.set_font("Arial", "B", 9)
        pdf.set_text_color(30, 64, 175)
        pdf.cell(0, 5, title.upper(), ln=True)
        pdf.set_draw_color(30, 64, 175)
        pdf.line(ml, pdf.get_y(), ml + pw, pdf.get_y())
        pdf.ln(2)
        pdf.set_text_color(30, 30, 30)

    personal = data.get("personalInfo") or {}
    name = s(personal.get("name", "Resume"))

    pdf.set_font("Arial", "B", 16)
    pdf.set_text_color(20, 20, 20)
    pdf.cell(0, 9, name, ln=True, align="C")

    if personal.get("title"):
        pdf.set_font("Arial", "I", 10)
        pdf.set_text_color(80, 80, 80)
        pdf.cell(0, 5, s(personal["title"]), ln=True, align="C")

    # Build contact line: plain fields first, then labelled links (Portfolio / LinkedIn / GitHub)
    _label_map = {"website": "Portfolio", "linkedin": "LinkedIn", "github": "GitHub"}
    _link_keys = {"website", "linkedin", "github"}
    parts = []
    for k in ["email", "phone", "location", "website", "linkedin", "github"]:
        v = personal.get(k) or ""
        if not v:
            continue
        if k in _link_keys:
            parts.append(_label_map[k])   # show the label, not the raw URL
        else:
            parts.append(s(v))
    if parts:
        pdf.set_font("Arial", "", 8)
        pdf.set_text_color(90, 90, 90)
        pdf.cell(0, 4, "  |  ".join(parts), ln=True, align="C")

    pdf.set_draw_color(30, 64, 175)
    pdf.set_line_width(0.4)
    pdf.line(ml, pdf.get_y()+1, ml+pw, pdf.get_y()+1)
    pdf.ln(4)
    pdf.set_line_width(0.2)

    summary = s(data.get("summary",""))
    if summary:
        sec_hdr("Summary")
        pdf.set_font("Arial","",8.5)
        pdf.multi_cell(0, 4.5, summary)
        pdf.ln(3)

    for job in (data.get("workExperience") or []):
        if not isinstance(job, dict): continue
        if not _exp_hdr_done:
            sec_hdr("Experience")
            _exp_hdr_done = True
        left = " | ".join(x for x in [s(job.get("title","")), s(job.get("company",""))] if x)
        date = s(job.get("years",""))
        pdf.set_font("Arial","B",9)
        pdf.set_text_color(20,20,20)
        pdf.cell(pw*0.72, 5, left, ln=False)
        pdf.set_font("Arial","",8)
        pdf.set_text_color(90,90,90)
        pdf.cell(pw*0.28, 5, date, ln=True, align="R")
        if job.get("location"):
            pdf.set_font("Arial","I",8)
            pdf.cell(0, 4, s(job["location"]), ln=True)
        for b in (job.get("description") or []):
            if b:
                pdf.set_font("Arial","",8.5)
                pdf.set_text_color(50,50,50)
                pdf.set_x(ml+3)
                pdf.cell(3,4.5,"*",ln=False)
                pdf.set_x(ml+6)
                pdf.multi_cell(pw-6, 4.5, s(b))
        pdf.ln(2)

    for edu in (data.get("education") or []):
        if not isinstance(edu, dict): continue
        if not _edu_hdr_done:
            sec_hdr("Education")
            _edu_hdr_done = True
        left = " | ".join(x for x in [s(edu.get("degree","")), s(edu.get("institution",""))] if x)
        pdf.set_font("Arial","B",9)
        pdf.set_text_color(20,20,20)
        pdf.cell(pw*0.72, 5, left, ln=False)
        pdf.set_font("Arial","",8)
        pdf.set_text_color(90,90,90)
        pdf.cell(pw*0.28, 5, s(edu.get("years","")), ln=True, align="R")
        if edu.get("description"):
            pdf.set_font("Arial","",8.5)
            pdf.multi_cell(0, 4.5, s(edu["description"]))
        pdf.ln(2)

    for proj in (data.get("personalProjects") or []):
        if not isinstance(proj, dict): continue
        if not _proj_hdr_done:
            sec_hdr("Projects")
            _proj_hdr_done = True
        # Project name with optional github/website links
        proj_name = s(proj.get("name",""))
        github_url = s(proj.get("github") or "")
        website_url = s(proj.get("website") or "")
        links = " | ".join(x for x in [github_url, website_url] if x)
        display_name = proj_name + (f" ({links})" if links else "")
        pdf.set_font("Arial","B",9)
        pdf.set_text_color(20,20,20)
        pdf.cell(pw*0.72, 5, display_name, ln=False)
        pdf.set_font("Arial","",8)
        pdf.set_text_color(90,90,90)
        pdf.cell(pw*0.28, 5, s(proj.get("years") or ""), ln=True, align="R")
        if proj.get("role"):
            pdf.set_font("Arial","I",8.5)
            pdf.set_text_color(60,60,60)
            pdf.cell(0, 4, s(proj.get("role","")), ln=True)
        for b in (proj.get("description") or []):
            if b:
                pdf.set_font("Arial","",8.5)
                pdf.set_text_color(50,50,50)
                pdf.set_x(ml+3)
                pdf.cell(3,4.5,"*",ln=False)
                pdf.set_x(ml+6)
                pdf.multi_cell(pw-6, 4.5, s(b))
        pdf.ln(2)

    add = data.get("additional") or {}
    skills = add.get("technicalSkills") or []
    if skills:
        sec_hdr("Technical Skills")
        pdf.set_font("Arial","",8.5)
        pdf.multi_cell(0, 4.5, "  *  ".join(s(x) for x in skills if x))
        pdf.ln(2)

    for c in (add.get("certificationsTraining") or []):
        if not _cert_hdr_done:
            sec_hdr("Certifications")
            _cert_hdr_done = True
        pdf.set_font("Arial","",8.5)
        pdf.set_x(ml+3); pdf.cell(3,4.5,"*",ln=False)
        pdf.set_x(ml+6); pdf.multi_cell(pw-6, 4.5, s(c))

    # Languages and Awards
    lang_list = add.get("languages") or []
    if lang_list:
        sec_hdr("Languages")
        pdf.set_font("Arial","",8.5)
        pdf.multi_cell(0, 4.5, "  |  ".join(s(x) for x in lang_list if x))
        pdf.ln(2)

    awards_list = add.get("awards") or []
    if awards_list:
        sec_hdr("Awards")
        for award in awards_list:
            if award:
                pdf.set_font("Arial","",8.5)
                pdf.set_x(ml+3); pdf.cell(3,4.5,"*",ln=False)
                pdf.set_x(ml+6); pdf.multi_cell(pw-6, 4.5, s(award))

    out = pdf.output()
    return bytes(out) if isinstance(out, bytearray) else out
