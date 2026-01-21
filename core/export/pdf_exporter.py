from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


def export_schedule_pdf(
    schedule: Dict[str, Dict[int, Dict[int, Optional[Tuple[int, int]]]]],
    output_dir: str,
    *,
    days: List[str],
    lessons_per_day: int,
    classes: List[Dict[str, Any]],
    classes_by_id: Dict[int, Dict[str, Any]],
    teachers_by_id: Dict[int, Dict[str, Any]],
    subjects_by_id: Dict[int, Dict[str, Any]],
    title: str = "School Schedule",
) -> Path:
    """
    Export the schedule into a PDF with per-class tables (lessons x days).
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    pdf_path = output_path / "schedule.pdf"

    doc = SimpleDocTemplate(str(pdf_path), pagesize=landscape(A4))
    styles = getSampleStyleSheet()
    elements = [Paragraph(title, styles["Title"]), Spacer(1, 12)]

    for cls in classes:
        class_name = cls["name"]
        class_id = cls["id"]

        elements.append(Paragraph(class_name, styles["Heading2"]))
        elements.append(Spacer(1, 6))

        table_data: List[List[str]] = []
        header = ["Lesson"] + days
        table_data.append(header)

        for lesson in range(1, lessons_per_day + 1):
            row = [str(lesson)]
            for day in days:
                assignment = schedule[day][lesson].get(class_id)
                if assignment is None:
                    row.append("-")
                    continue

                teacher_id, subject_id = assignment
                subject_name = subjects_by_id.get(subject_id, {}).get("name", "N/A")
                teacher_name = teachers_by_id.get(teacher_id, {}).get("name", "N/A")
                row.append(f"{subject_name}\n{teacher_name}")
            table_data.append(row)

        table = Table(
            table_data,
            repeatRows=1,
            hAlign="LEFT",
        )
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                    ("FONTSIZE", (0, 0), (-1, -1), 9),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
                    ("TOPPADDING", (0, 0), (-1, 0), 6),
                ]
            )
        )

        elements.append(table)
        elements.append(Spacer(1, 18))

    doc.build(elements)
    return pdf_path
