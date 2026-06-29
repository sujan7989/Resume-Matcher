"""PDF rendering utilities.

Strategy:
1. Try Playwright (headless Chromium) - best quality, needs browser installed
2. Fall back to fpdf2 direct generation from resume JSON data - always works

The fpdf2 fallback generates a properly formatted PDF directly from the
resume data without needing a browser, so it works on Render free tier.
"""

from __future__ import annotations

import asyncio
import logging
import os
import sys
from pathlib import Path
from typing import Any, Awaitable, NoReturn, Optional

from playwright.async_api import (
    Browser,
    Error as PlaywrightError,
    Page,
    Playwright,
    async_playwright,
)

logger = logging.getLogger(__name__)

# Navigation timeout - 90s for slow Render free tier
_NAV_TIMEOUT_MS = 90_000


class PDFRenderError(Exception):
    """Raised when PDF generation fails completely."""
    pass


_playwright: Optional[Any] = None
_browser: Optional[Browser] = None
_init_lock = asyncio.Lock()
_playwright_available: Optional[bool] = None  # None = not yet checked


async def _check_playwright_available() -> bool:
    """Check once if Playwright/Chromium is actually usable."""
    global _playwright_available
    if _playwright_available is not None:
        return _playwright_available
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            await browser.close()
        _playwright_available = True
        logger.info("Playwright/Chromium is available")
    except Exception as e:
        _playwright_available = False
        logger.warning(f"Playwright/Chromium not available: {e} - will use fpdf2 fallback")
    return _playwright_available


async def init_pdf_renderer() -> None:
    """Initialize the Playwright browser instance (lazy)."""
    global _playwright, _browser
    if _browser is not None:
        return
    async with _init_lock:
        if _browser is not None:
            return
        if not await _check_playwright_available():
            return
        try:
            logger.info("Starting Playwright browser...")
            _playwright = await async_playwright().start()
            _browser = await _playwright.chromium.launch()
            logger.info("Playwright browser started successfully")
        except Exception as e:
            logger.warning(f"Failed to start Playwright browser: {e}")
            _playwright = None
            _browser = None


async def close_pdf_renderer() -> None:
    """Close the Playwright browser instance."""
    global _playwright, _browser
    if _browser is not None:
        try:
            await _browser.close()
        except Exception:
            pass
        _browser = None
    if _playwright is not None:
        try:
            await _playwright.stop()
        except Exception:
            pass
        _playwright = None


def _resolve_pdf_format(page_size: str) -> str:
    return {"A4": "A4", "LETTER": "Letter"}.get(page_size, "A4")


def _resolve_pdf_margins(margins: Optional[dict]) -> dict:
    if margins:
        return {
            "top": f"{margins.get('top', 10)}mm",
            "right": f"{margins.get('right', 10)}mm",
            "bottom": f"{margins.get('bottom', 10)}mm",
            "left": f"{margins.get('left', 10)}mm",
        }
    return {"top": "10mm", "right": "10mm", "bottom": "10mm", "left": "10mm"}


async def _render_with_playwright(url: str, page_size: str, pdf_margins: dict) -> bytes:
    """Render URL to PDF using Playwright. Raises on any failure."""
    global _browser

    if _browser is None:
        await init_pdf_renderer()

    if _browser is None:
        raise PDFRenderError("Playwright browser not available")

    pdf_format = _resolve_pdf_format(page_size)
    page: Page = await _browser.new_page()
    try:
        logger.info(f"Playwright: loading {url}")
        await page.goto(url, wait_until="load", timeout=_NAV_TIMEOUT_MS)

        # Wait for resume content
        try:
            await page.wait_for_selector(".resume-print", timeout=30_000)
        except Exception:
            logger.warning("Selector .resume-print not found, rendering anyway")

        # Wait for fonts
        try:
            await page.wait_for_function(
                "() => document.fonts.ready.then(() => true)", timeout=30_000
            )
        except Exception:
            logger.warning("Font loading timed out, continuing")

        pdf_bytes = await page.pdf(
            format=pdf_format,
            print_background=True,
            margin=pdf_margins,
        )
        logger.info(f"Playwright PDF generated: {len(pdf_bytes)} bytes")
        return pdf_bytes
    finally:
        await page.close()


async def render_resume_pdf(
    url: str,
    page_size: str = "A4",
    selector: str = ".resume-print",
    margins: Optional[dict] = None,
    resume_data: Optional[dict] = None,
) -> bytes:
    """Render resume to PDF.

    Tries Playwright first (browser-rendered, high quality).
    Falls back to fpdf2 direct generation from resume_data if Playwright fails.

    Args:
        url: The frontend print URL (used by Playwright)
        page_size: "A4" or "LETTER"
        selector: CSS selector to wait for (Playwright only)
        margins: Page margins dict {top, right, bottom, left} in mm
        resume_data: Resume JSON data (used for fpdf2 fallback)
    """
    pdf_margins = _resolve_pdf_margins(margins)

    # Try Playwright first
    if await _check_playwright_available():
        try:
            return await _render_with_playwright(url, page_size, pdf_margins)
        except Exception as e:
            logger.warning(f"Playwright rendering failed: {e}. Falling back to fpdf2.")

    # fpdf2 fallback - generate directly from resume data
    logger.info("Using fpdf2 to generate PDF from resume data")
    return _generate_pdf_from_data(resume_data, page_size, margins)


def _generate_pdf_from_data(
    resume_data: Optional[dict],
    page_size: str = "A4",
    margins: Optional[dict] = None,
) -> bytes:
    """Generate a properly formatted PDF from resume JSON data using fpdf2.

    This is the reliable fallback that works without a browser.
    Produces a clean, professional PDF with all resume sections.
    """
    from fpdf import FPDF

    margin_top = (margins or {}).get("top", 15)
    margin_bottom = (margins or {}).get("bottom", 15)
    margin_left = (margins or {}).get("left", 20)
    margin_right = (margins or {}).get("right", 20)

    pdf = FPDF(format=page_size)
    pdf.set_margins(margin_left, margin_top, margin_right)
    pdf.set_auto_page_break(auto=True, margin=margin_bottom)
    pdf.add_page()

    data = resume_data or {}

    # ── Helper functions ──────────────────────────────────────────────────────

    def safe_text(val: Any) -> str:
        if val is None:
            return ""
        text = str(val)
        # Replace unicode characters that fpdf2 can't handle in core fonts
        replacements = {
            "\u2019": "'", "\u2018": "'", "\u201c": '"', "\u201d": '"',
            "\u2013": "-", "\u2014": "-", "\u2022": "*", "\u00b7": "*",
            "\u00e9": "e", "\u00e8": "e", "\u00ea": "e", "\u00eb": "e",
            "\u00e0": "a", "\u00e2": "a", "\u00e4": "a", "\u00f4": "o",
            "\u00f6": "o", "\u00fc": "u", "\u00fb": "u", "\u00e7": "c",
            "\u00f1": "n", "\u00ed": "i", "\u00ee": "i", "\u00ef": "i",
        }
        for orig, repl in replacements.items():
            text = text.replace(orig, repl)
        return text

    def section_header(title: str) -> None:
        """Draw a section header with underline."""
        pdf.set_font("Arial", "B", 11)
        pdf.set_text_color(30, 30, 30)
        pdf.cell(0, 6, safe_text(title.upper()), ln=True)
        # Draw underline
        x = pdf.get_x()
        y = pdf.get_y()
        page_w = pdf.w - pdf.l_margin - pdf.r_margin
        pdf.set_draw_color(100, 100, 100)
        pdf.line(pdf.l_margin, y, pdf.l_margin + page_w, y)
        pdf.ln(2)

    def body_text(text: str, indent: float = 0) -> None:
        """Write body text with optional indent."""
        pdf.set_font("Arial", "", 9)
        pdf.set_text_color(50, 50, 50)
        if indent:
            pdf.set_x(pdf.l_margin + indent)
        pdf.multi_cell(0, 5, safe_text(text))

    def bullet_item(text: str) -> None:
        """Write a bullet point item."""
        pdf.set_font("Arial", "", 9)
        pdf.set_text_color(50, 50, 50)
        x_start = pdf.l_margin + 4
        available_w = pdf.w - pdf.l_margin - pdf.r_margin - 8
        pdf.set_x(pdf.l_margin)
        pdf.cell(4, 5, "*")
        pdf.set_x(x_start)
        pdf.multi_cell(available_w, 5, safe_text(text))

    def small_gap() -> None:
        pdf.ln(2)

    def medium_gap() -> None:
        pdf.ln(4)

    # ── Personal Info / Header ────────────────────────────────────────────────
    personal = data.get("personalInfo", {}) or {}
    name = safe_text(personal.get("name", "Resume"))
    title = safe_text(personal.get("title", ""))
    email = safe_text(personal.get("email", ""))
    phone = safe_text(personal.get("phone", ""))
    location = safe_text(personal.get("location", ""))
    website = safe_text(personal.get("website", "") or "")
    linkedin = safe_text(personal.get("linkedin", "") or "")
    github = safe_text(personal.get("github", "") or "")

    # Name
    pdf.set_font("Arial", "B", 18)
    pdf.set_text_color(20, 20, 20)
    pdf.cell(0, 10, name, ln=True, align="C")

    # Title
    if title:
        pdf.set_font("Arial", "I", 11)
        pdf.set_text_color(80, 80, 80)
        pdf.cell(0, 6, title, ln=True, align="C")

    # Contact line
    contact_parts = [p for p in [email, phone, location] if p]
    if contact_parts:
        pdf.set_font("Arial", "", 9)
        pdf.set_text_color(80, 80, 80)
        pdf.cell(0, 5, "  |  ".join(contact_parts), ln=True, align="C")

    # Links line
    link_parts = [p for p in [website, linkedin, github] if p]
    if link_parts:
        pdf.set_font("Arial", "", 9)
        pdf.set_text_color(80, 80, 80)
        pdf.cell(0, 5, "  |  ".join(link_parts), ln=True, align="C")

    # Divider under header
    pdf.ln(2)
    pdf.set_draw_color(60, 60, 60)
    pdf.set_line_width(0.5)
    pdf.line(pdf.l_margin, pdf.get_y(), pdf.w - pdf.r_margin, pdf.get_y())
    pdf.set_line_width(0.2)
    medium_gap()

    # ── Summary ───────────────────────────────────────────────────────────────
    summary = safe_text(data.get("summary", ""))
    if summary:
        section_header("Summary")
        body_text(summary)
        medium_gap()

    # ── Work Experience ───────────────────────────────────────────────────────
    work_exp = data.get("workExperience", []) or []
    if work_exp:
        section_header("Experience")
        for job in work_exp:
            if not isinstance(job, dict):
                continue
            job_title = safe_text(job.get("title", ""))
            company = safe_text(job.get("company", ""))
            years = safe_text(job.get("years", ""))
            loc = safe_text(job.get("location", "") or "")
            description = job.get("description", []) or []

            # Title + Company on same line, years on right
            if job_title or company:
                pdf.set_font("Arial", "B", 10)
                pdf.set_text_color(20, 20, 20)
                left = " | ".join(p for p in [job_title, company] if p)
                # Two-column: left text, right date
                page_w = pdf.w - pdf.l_margin - pdf.r_margin
                if years:
                    pdf.cell(page_w * 0.7, 5, left, ln=False)
                    pdf.set_font("Arial", "", 9)
                    pdf.set_text_color(80, 80, 80)
                    pdf.cell(page_w * 0.3, 5, years, ln=True, align="R")
                else:
                    pdf.cell(0, 5, left, ln=True)

            if loc:
                pdf.set_font("Arial", "I", 9)
                pdf.set_text_color(100, 100, 100)
                pdf.cell(0, 4, loc, ln=True)

            for bullet in description:
                if bullet and isinstance(bullet, str):
                    bullet_item(bullet)

            small_gap()
        medium_gap()

    # ── Education ─────────────────────────────────────────────────────────────
    education = data.get("education", []) or []
    if education:
        section_header("Education")
        for edu in education:
            if not isinstance(edu, dict):
                continue
            institution = safe_text(edu.get("institution", ""))
            degree = safe_text(edu.get("degree", ""))
            years = safe_text(edu.get("years", ""))
            desc = safe_text(edu.get("description", "") or "")

            page_w = pdf.w - pdf.l_margin - pdf.r_margin
            pdf.set_font("Arial", "B", 10)
            pdf.set_text_color(20, 20, 20)
            left = " | ".join(p for p in [degree, institution] if p)
            if years:
                pdf.cell(page_w * 0.7, 5, left, ln=False)
                pdf.set_font("Arial", "", 9)
                pdf.set_text_color(80, 80, 80)
                pdf.cell(page_w * 0.3, 5, years, ln=True, align="R")
            else:
                pdf.cell(0, 5, left, ln=True)

            if desc:
                body_text(desc, indent=4)
            small_gap()
        medium_gap()

    # ── Projects ──────────────────────────────────────────────────────────────
    projects = data.get("personalProjects", []) or []
    if projects:
        section_header("Projects")
        for proj in projects:
            if not isinstance(proj, dict):
                continue
            proj_name = safe_text(proj.get("name", ""))
            role = safe_text(proj.get("role", "") or "")
            years = safe_text(proj.get("years", "") or "")
            gh = safe_text(proj.get("github", "") or "")
            web = safe_text(proj.get("website", "") or "")
            description = proj.get("description", []) or []

            page_w = pdf.w - pdf.l_margin - pdf.r_margin
            pdf.set_font("Arial", "B", 10)
            pdf.set_text_color(20, 20, 20)
            left = proj_name
            if role:
                left = f"{proj_name} - {role}"
            if years:
                pdf.cell(page_w * 0.7, 5, left, ln=False)
                pdf.set_font("Arial", "", 9)
                pdf.set_text_color(80, 80, 80)
                pdf.cell(page_w * 0.3, 5, years, ln=True, align="R")
            else:
                pdf.cell(0, 5, left, ln=True)

            if gh or web:
                links = "  |  ".join(p for p in [gh, web] if p)
                pdf.set_font("Arial", "I", 8)
                pdf.set_text_color(80, 80, 150)
                pdf.cell(0, 4, links, ln=True)

            for bullet in description:
                if bullet and isinstance(bullet, str):
                    bullet_item(bullet)
            small_gap()
        medium_gap()

    # ── Skills & Additional ───────────────────────────────────────────────────
    additional = data.get("additional", {}) or {}
    skills = additional.get("technicalSkills", []) or []
    certs = additional.get("certificationsTraining", []) or []
    languages = additional.get("languages", []) or []
    awards = additional.get("awards", []) or []

    if skills:
        section_header("Technical Skills")
        pdf.set_font("Arial", "", 9)
        pdf.set_text_color(50, 50, 50)
        pdf.multi_cell(0, 5, "  *  ".join(safe_text(s) for s in skills if s))
        medium_gap()

    if certs:
        section_header("Certifications")
        for cert in certs:
            if cert:
                bullet_item(cert)
        medium_gap()

    if languages:
        section_header("Languages")
        pdf.set_font("Arial", "", 9)
        pdf.set_text_color(50, 50, 50)
        pdf.cell(0, 5, "  *  ".join(safe_text(l) for l in languages if l), ln=True)
        medium_gap()

    if awards:
        section_header("Awards")
        for award in awards:
            if award:
                bullet_item(award)
        medium_gap()

    # ── Custom Sections ───────────────────────────────────────────────────────
    custom_sections = data.get("customSections", {}) or {}
    if isinstance(custom_sections, dict):
        for section_key, section_val in custom_sections.items():
            if not isinstance(section_val, dict):
                continue
            sec_title = safe_text(section_val.get("title", section_key))
            sec_type = section_val.get("sectionType", "")
            items = section_val.get("items", []) or []
            if not items:
                continue
            section_header(sec_title)
            for item in items:
                if not isinstance(item, dict):
                    continue
                item_title = safe_text(item.get("title", "") or "")
                item_years = safe_text(item.get("years", "") or "")
                item_desc = item.get("description", []) or []
                if item_title:
                    page_w = pdf.w - pdf.l_margin - pdf.r_margin
                    pdf.set_font("Arial", "B", 10)
                    pdf.set_text_color(20, 20, 20)
                    if item_years:
                        pdf.cell(page_w * 0.7, 5, item_title, ln=False)
                        pdf.set_font("Arial", "", 9)
                        pdf.set_text_color(80, 80, 80)
                        pdf.cell(page_w * 0.3, 5, item_years, ln=True, align="R")
                    else:
                        pdf.cell(0, 5, item_title, ln=True)
                for bullet in item_desc:
                    if bullet and isinstance(bullet, str):
                        bullet_item(bullet)
                small_gap()
            medium_gap()

    pdf_bytes = pdf.output()
    if isinstance(pdf_bytes, bytearray):
        pdf_bytes = bytes(pdf_bytes)
    logger.info(f"fpdf2 PDF generated: {len(pdf_bytes)} bytes")
    return pdf_bytes
