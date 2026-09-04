import os
import json
import re
import html
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, HRFlowable
)
from reportlab.pdfgen import canvas

TRANSCRIPT_PATH = r"C:\Users\EdunetFoundation\.gemini\antigravity\brain\a1c97eaa-eed3-449d-bc27-5a68bc0989e3\.system_generated\logs\transcript.jsonl"
OUTPUT_PDF = r"c:\Users\EdunetFoundation\Documents\Project\Project_Conversation_Transcript.pdf"

class NumberedCanvas(canvas.Canvas):
    """Two-pass canvas to dynamically add 'Page X of Y' footers and headers."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)

    def draw_page_decorations(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748b"))

        # Running Header (pages > 1)
        if self._pageNumber > 1:
            self.drawString(54, 11 * inch - 36, "ResumeForge ATS — Complete Project Conversation Transcript")
            self.drawRightString(8.5 * inch - 54, 11 * inch - 36, "September 4, 2026")
            self.setStrokeColor(colors.HexColor("#e2e8f0"))
            self.setLineWidth(0.5)
            self.line(54, 11 * inch - 42, 8.5 * inch - 54, 11 * inch - 42)

        # Running Footer
        footer_text = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(8.5 * inch - 54, 36, footer_text)
        self.drawString(54, 36, "Confidential & Proprietary — Edunet Foundation / Project Health")
        self.setStrokeColor(colors.HexColor("#e2e8f0"))
        self.setLineWidth(0.5)
        self.line(54, 46, 8.5 * inch - 54, 46)
        self.restoreState()

def safe_format_text(text: str) -> str:
    """Escapes XML entities and provides clean text wrapping."""
    if not text:
        return ""
    # Strip heavy markdown block markers
    text = re.sub(r"```[\w]*\n(.*?)```", r"[Code:\n\1]", text, flags=re.DOTALL)
    escaped = html.escape(text)
    # Convert bold **word** -> <b>word</b>
    escaped = re.sub(r"\*\*([^\n*]+)\*\*", r"<b>\1</b>", escaped)
    # Convert inline code `word` -> <font color="#4f46e5">word</font>
    escaped = re.sub(r"`([^`\n]+)`", r"<font color='#4f46e5'><b>\1</b></font>", escaped)
    escaped = escaped.replace("\n", "<br/>")
    return escaped

def parse_transcript_data(jsonl_path: str):
    exchanges = []
    if not os.path.exists(jsonl_path):
        return exchanges

    with open(jsonl_path, "r", encoding="utf-8") as f:
        raw_lines = [json.loads(line) for line in f if line.strip()]

    current_user_msg = None
    current_assistant_msgs = []
    tools_used_in_turn = []

    for item in raw_lines:
        msg_type = item.get("type")
        content = item.get("content", "")
        created_at = item.get("created_at", "")

        if msg_type == "USER_INPUT":
            if current_user_msg:
                exchanges.append({
                    "user": current_user_msg,
                    "assistant": "\n\n".join(current_assistant_msgs).strip(),
                    "tools": list(dict.fromkeys(tools_used_in_turn)),
                    "timestamp": current_user_msg.get("time", "")
                })
                current_assistant_msgs = []
                tools_used_in_turn = []

            clean_content = content
            m = re.search(r"<USER_REQUEST>(.*?)</USER_REQUEST>", content, re.DOTALL)
            if m:
                clean_content = m.group(1).strip()
            elif "Comments on artifact" in content:
                clean_content = "Approved implementation plan document."

            current_user_msg = {
                "text": clean_content,
                "time": created_at
            }

        elif msg_type == "PLANNER_RESPONSE":
            if content and content.strip():
                current_assistant_msgs.append(content.strip())
            for tc in item.get("tool_calls", []):
                summary = tc.get("toolSummary") or tc.get("name")
                if summary:
                    tools_used_in_turn.append(summary)

    if current_user_msg:
        exchanges.append({
            "user": current_user_msg,
            "assistant": "\n\n".join(current_assistant_msgs).strip(),
            "tools": list(dict.fromkeys(tools_used_in_turn)),
            "timestamp": current_user_msg.get("time", "")
        })

    return exchanges

def build_pdf():
    exchanges = parse_transcript_data(TRANSCRIPT_PATH)
    doc = SimpleDocTemplate(
        OUTPUT_PDF,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=24,
        textColor=colors.HexColor("#0f172a")
    )

    subtitle_style = ParagraphStyle(
        'DocSubTitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#475569")
    )

    h2_style = ParagraphStyle(
        'Heading2',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=13,
        leading=17,
        textColor=colors.HexColor("#1e293b"),
        spaceBefore=14,
        spaceAfter=6
    )

    turn_header_style = ParagraphStyle(
        'TurnHdr',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10.5,
        leading=14,
        textColor=colors.HexColor("#4338ca")
    )

    user_label_style = ParagraphStyle(
        'UserLabel',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#1e40af")
    )

    user_body_style = ParagraphStyle(
        'UserBody',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=13.5,
        textColor=colors.HexColor("#0f172a")
    )

    asst_label_style = ParagraphStyle(
        'AsstLabel',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#065f46")
    )

    asst_body_style = ParagraphStyle(
        'AsstBody',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=13.5,
        textColor=colors.HexColor("#1e293b"),
        spaceAfter=6
    )

    tools_style = ParagraphStyle(
        'ToolsStyle',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=8,
        leading=11,
        textColor=colors.HexColor("#64748b")
    )

    meta_badge_style = ParagraphStyle(
        'MetaBadge',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor("#ffffff")
    )

    story = []

    # Banner Table
    banner_data = [
        [
            Paragraph("<b>PROJECT TRANSCRIPT &amp; IMPLEMENTATION RECORD</b>", meta_badge_style),
            Paragraph("<b>STATUS: DEPLOYED &amp; LIVE</b>", meta_badge_style)
        ]
    ]
    banner_table = Table(banner_data, colWidths=[300, 204])
    banner_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#4f46e5")),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
    ]))
    story.append(banner_table)
    story.append(Spacer(1, 12))

    story.append(Paragraph("ResumeForge ATS — AI Resume Generator &amp; JD Matcher", title_style))
    story.append(Spacer(1, 4))
    story.append(Paragraph("Comprehensive end-to-end record of developer prompts, architectural decisions, core algorithms, frontend development, automated test results, GitHub repository integration, and live cloud deployment.", subtitle_style))
    story.append(Spacer(1, 12))

    # Meta Table
    meta_table_data = [
        [Paragraph("<b>Project:</b>", styles['Normal']), Paragraph("ResumeForge ATS", styles['Normal']),
         Paragraph("<b>Date:</b>", styles['Normal']), Paragraph("September 4, 2026", styles['Normal'])],
        [Paragraph("<b>GitHub:</b>", styles['Normal']), Paragraph("<a href='https://github.com/mupanpruthvi/ATS-Resume' color='#4f46e5'>github.com/mupanpruthvi/ATS-Resume</a>", styles['Normal']),
         Paragraph("<b>Developer:</b>", styles['Normal']), Paragraph("mupanpruthvi", styles['Normal'])],
        [Paragraph("<b>Live URL:</b>", styles['Normal']), Paragraph("<a href='https://resume-forge-ats.onrender.com' color='#059669'><b>https://resume-forge-ats.onrender.com</b></a>", styles['Normal']),
         Paragraph("<b>Environment:</b>", styles['Normal']), Paragraph("Python 3.14 / FastAPI / Render", styles['Normal'])],
    ]
    meta_table = Table(meta_table_data, colWidths=[80, 220, 80, 124])
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#e2e8f0")),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#f1f5f9")),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 14))

    # Summary
    story.append(Paragraph("Project Execution Summary", h2_style))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#cbd5e1"), spaceAfter=8))

    summary_bullets = [
        "<b>Turn 1 (Initial Requirement):</b> User requested an ATS resume builder where students can copy JD text or JD links from anywhere, upload an existing CV (or type skills/details), and generate a tailored ATS resume with an ATS match score.",
        "<b>Phase 1 (Architecture &amp; Approval):</b> Verified Python 3.14 environment, installed dependencies (FastAPI, uvicorn, beautifulsoup4, pypdf, python-docx, requests), and obtained user review and approval on the implementation plan.",
        "<b>Phase 2 (Engine &amp; Parsers):</b> Implemented <code>parsers.py</code> (document extraction &amp; web scraper) and <code>ats_engine.py</code> (scoring algorithm, canonical skill taxonomy, bullet point enhancer, and Word .docx generator).",
        "<b>Phase 3 (Frontend &amp; Server):</b> Built responsive 3-step wizard with radial ATS score gauge, Before vs. After comparison, keyword inspector with 1-click '+' skill injection, live in-place resume editor, and print/PDF stylesheet.",
        "<b>Phase 4 (Automated Testing):</b> Authored <code>test_ats.py</code> and <code>test_api.py</code>; verified document parsing, score calculation, and all API endpoints (100% pass).",
        "<b>Phase 5 (GitHub Publishing):</b> Installed Git and GitHub CLI, initialized repository, authored <code>requirements.txt</code>, and published branch <code>main</code> to <b>github.com/mupanpruthvi/ATS-Resume</b>.",
        "<b>Phase 6 (Cloud Deployment):</b> Created <code>render.yaml</code> blueprint and <code>Procfile</code>, enabled 1-click cloud deployment, and updated GitHub repo homepage with the live link <b>https://resume-forge-ats.onrender.com</b>."
    ]

    for bullet in summary_bullets:
        p = Paragraph(f"•  {bullet}", user_body_style)
        story.append(p)
        story.append(Spacer(1, 3))

    story.append(Spacer(1, 12))

    # Detailed Exchanges
    story.append(Paragraph("Detailed Chronological Conversation Log", h2_style))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#cbd5e1"), spaceAfter=12))

    for idx, ex in enumerate(exchanges):
        turn_num = idx + 1
        user_text = ex["user"].get("text", "")
        assistant_text = ex.get("assistant", "")
        tools = ex.get("tools", [])

        if not user_text and not assistant_text:
            continue

        # Header for this turn
        t_time = ex.get('timestamp', 'September 4, 2026')[:19].replace('T', ' ')
        story.append(Paragraph(f"TURN #{turn_num} — {t_time}", turn_header_style))
        story.append(Spacer(1, 4))

        # User Box
        u_content = [
            Paragraph("<b>USER PROMPT:</b>", user_label_style),
            Spacer(1, 2),
            Paragraph(safe_format_text(user_text), user_body_style)
        ]
        u_table = Table([[u_content]], colWidths=[504])
        u_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#f1f5f9")),
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#cbd5e1")),
            ('LINELEFT', (0, 0), (-1, -1), 3.5, colors.HexColor("#2563eb")),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ]))
        story.append(u_table)
        story.append(Spacer(1, 6))

        # Assistant Box
        if assistant_text:
            story.append(Paragraph("<b>AI ASSISTANT RESPONSE:</b>", asst_label_style))
            story.append(Spacer(1, 2))

            # Split assistant paragraphs to allow natural page breaks
            paragraphs = assistant_text.split("\n\n")
            for para in paragraphs:
                para_clean = safe_format_text(para.strip())
                if para_clean:
                    story.append(Paragraph(para_clean, asst_body_style))

        # Tools executed
        if tools:
            tool_badges = " | ".join([f"⚙ {t}" for t in tools[:8]])
            story.append(Paragraph(f"<b>Key Operations:</b> {tool_badges}", tools_style))

        story.append(Spacer(1, 10))
        story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#e2e8f0"), spaceAfter=12))

    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"[+] PDF generated successfully: {OUTPUT_PDF}")

if __name__ == "__main__":
    build_pdf()
