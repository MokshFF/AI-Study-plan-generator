"""Builds Milestone 2 Official PDF Reports using ReportLab.

Compiles:
1. `docs/Milestone2_Main_Report.pdf` (The main official 7-section report)
2. `docs/Milestone2_Technical_Report.pdf` (The supporting 9-chapter technical report)
"""

import os
import re
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import (
    HRFlowable,
    KeepTogether,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

DOCS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "docs")


def clean_markdown_text(text: str) -> str:
    """Converts inline markdown formatting to ReportLab XML tags."""
    # Ensure <br> is properly self-closing <br/> for ReportLab
    text = re.sub(r"<br\s*/?>", "<br/>", text, flags=re.IGNORECASE)
    # Convert bold **text** to <b>text</b>
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    # Convert italic *text* to <i>text</i>
    text = re.sub(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)", r"<i>\1</i>", text)
    # Convert inline code `text` to font
    text = re.sub(r"`(.+?)`", r'<font face="Courier" color="#8B0000"><b>\1</b></font>', text)
    # Escape any stray ampersands not already in entities
    text = re.sub(r"&(?!(amp|lt|gt|quot|apos);)", "&amp;", text)
    # Escape any stray angle brackets that are not valid ReportLab tags
    return text


def parse_markdown_to_story(md_path: str, styles):
    story = []
    with open(md_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    in_table = False
    table_rows = []
    in_code_block = False
    code_lines = []

    for line in lines:
        stripped = line.strip()

        # Handle code blocks
        if stripped.startswith("```"):
            if in_code_block:
                # End code block
                code_text = "<br/>".join(code_lines)
                story.append(Paragraph(code_text, styles["CodeBlock"]))
                story.append(Spacer(1, 8))
                in_code_block = False
                code_lines = []
            else:
                in_code_block = True
                code_lines = []
            continue

        if in_code_block:
            safe_line = stripped.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            code_lines.append(safe_line)
            continue

        # Handle tables
        if stripped.startswith("|"):
            # Check if separator row like | :--- | :---: |
            if re.match(r"^\|(\s*[-:]+[-|\s:]*)\|$", stripped):
                continue
            cells = [c.strip() for c in stripped.split("|")[1:-1]]
            table_rows.append(cells)
            in_table = True
            continue
        elif in_table:
            # End of table, process collected rows
            if table_rows:
                num_cols = max(len(r) for r in table_rows)
                formatted_table_data = []
                for row_idx, r in enumerate(table_rows):
                    # Pad row if uneven
                    while len(r) < num_cols:
                        r.append("")
                    row_cells = []
                    for c in r:
                        clean_c = clean_markdown_text(c)
                        p_style = styles["TableHeader"] if row_idx == 0 else styles["TableCell"]
                        row_cells.append(Paragraph(clean_c, p_style))
                    formatted_table_data.append(row_cells)

                # Responsive column widths
                col_width = (letter[0] - 72) / num_cols
                t = Table(formatted_table_data, colWidths=[col_width] * num_cols)
                t.setStyle(
                    TableStyle([
                        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1E3A8A")),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),
                        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
                        ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#1E3A8A")),
                        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                        ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ])
                )
                story.append(t)
                story.append(Spacer(1, 10))
                table_rows = []
                in_table = False

        if not stripped:
            continue

        # Headings
        if stripped.startswith("# "):
            title_text = clean_markdown_text(stripped[2:])
            story.append(Paragraph(title_text, styles["DocTitle"]))
            story.append(Spacer(1, 6))
            story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#1E3A8A")))
            story.append(Spacer(1, 10))
        elif stripped.startswith("## "):
            h2_text = clean_markdown_text(stripped[3:])
            story.append(Spacer(1, 10))
            story.append(Paragraph(h2_text, styles["SectionHeading"]))
            story.append(Spacer(1, 6))
            story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#94A3B8")))
            story.append(Spacer(1, 8))
        elif stripped.startswith("### "):
            h3_text = clean_markdown_text(stripped[4:])
            story.append(Spacer(1, 6))
            story.append(Paragraph(h3_text, styles["SubSectionHeading"]))
            story.append(Spacer(1, 4))
        elif stripped.startswith("#### "):
            h4_text = clean_markdown_text(stripped[5:])
            story.append(Paragraph(h4_text, styles["SubSubSectionHeading"]))
            story.append(Spacer(1, 3))
        elif stripped.startswith("> "):
            quote_text = clean_markdown_text(stripped[2:])
            story.append(Paragraph(quote_text, styles["CalloutBox"]))
            story.append(Spacer(1, 6))
        elif stripped.startswith("- ") or stripped.startswith("* "):
            bullet_text = clean_markdown_text(stripped[2:])
            story.append(Paragraph(f"• {bullet_text}", styles["BulletItem"]))
            story.append(Spacer(1, 3))
        elif re.match(r"^\d+\.\s+", stripped):
            num_text = re.sub(r"^\d+\.\s+", "", stripped)
            prefix = re.match(r"^(\d+\.)\s+", stripped).group(1)
            clean_item = clean_markdown_text(num_text)
            story.append(Paragraph(f"{prefix} {clean_item}", styles["BulletItem"]))
            story.append(Spacer(1, 3))
        elif stripped.startswith("---"):
            story.append(Spacer(1, 6))
            story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#CBD5E1")))
            story.append(Spacer(1, 6))
        else:
            para_text = clean_markdown_text(stripped)
            story.append(Paragraph(para_text, styles["BodyText"]))
            story.append(Spacer(1, 6))

    return story


def build_pdf(md_filename: str, pdf_filename: str):
    md_path = os.path.join(DOCS_DIR, md_filename)
    pdf_path = os.path.join(DOCS_DIR, pdf_filename)

    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=letter,
        leftMargin=36,
        rightMargin=36,
        topMargin=36,
        bottomMargin=36,
    )

    styles = getSampleStyleSheet()

    # Custom styles
    styles.add(ParagraphStyle(
        name="DocTitle",
        fontName="Helvetica-Bold",
        fontSize=18,
        leading=22,
        textColor=colors.HexColor("#1E3A8A"),
    ))
    styles.add(ParagraphStyle(
        name="SectionHeading",
        fontName="Helvetica-Bold",
        fontSize=13,
        leading=16,
        textColor=colors.HexColor("#1E3A8A"),
    ))
    styles.add(ParagraphStyle(
        name="SubSectionHeading",
        fontName="Helvetica-Bold",
        fontSize=11,
        leading=14,
        textColor=colors.HexColor("#0F172A"),
    ))
    styles.add(ParagraphStyle(
        name="SubSubSectionHeading",
        fontName="Helvetica-Bold",
        fontSize=10,
        leading=13,
        textColor=colors.HexColor("#334155"),
    ))
    styles["BodyText"].fontSize = 8.5
    styles["BodyText"].leading = 11.5
    styles["BodyText"].textColor = colors.HexColor("#1E293B")

    styles.add(ParagraphStyle(
        name="BulletItem",
        fontName="Helvetica",
        fontSize=8.5,
        leading=11.5,
        leftIndent=14,
        textColor=colors.HexColor("#1E293B"),
    ))
    styles.add(ParagraphStyle(
        name="TableHeader",
        fontName="Helvetica-Bold",
        fontSize=7.5,
        leading=9.5,
        textColor=colors.white,
    ))
    styles.add(ParagraphStyle(
        name="TableCell",
        fontName="Helvetica",
        fontSize=7.5,
        leading=9.5,
        textColor=colors.HexColor("#0F172A"),
    ))
    styles.add(ParagraphStyle(
        name="CodeBlock",
        fontName="Courier",
        fontSize=7,
        leading=9,
        textColor=colors.HexColor("#1E293B"),
        backColor=colors.HexColor("#F1F5F9"),
        borderPadding=6,
    ))
    styles.add(ParagraphStyle(
        name="CalloutBox",
        fontName="Helvetica-Oblique",
        fontSize=8,
        leading=11,
        textColor=colors.HexColor("#0C4A6E"),
        backColor=colors.HexColor("#F0F9FF"),
        borderPadding=6,
    ))

    print(f"Parsing {md_filename}...")
    story = parse_markdown_to_story(md_path, styles)
    print(f"Building {pdf_filename} ({len(story)} flowables)...")
    doc.build(story)
    size_kb = os.path.getsize(pdf_path) / 1024
    print(f"Successfully generated: {pdf_filename} ({size_kb:.1f} KB)")


if __name__ == "__main__":
    build_pdf("Milestone2_Main_Report.md", "Milestone2_Main_Report.pdf")
    build_pdf("Milestone2_Technical_Report.md", "Milestone2_Technical_Report.pdf")
    build_pdf("Milestone2_Prescribed_Report.md", "Milestone2_Prescribed_Report.pdf")
