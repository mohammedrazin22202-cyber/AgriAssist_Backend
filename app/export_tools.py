"""
AgriAssist Agronomic Data Export Utilities.
Generates standard CSV exports with UTF-8 BOM encoding (for regional language preservation)
and standard RFC 5545 iCalendar (.ics) files for farm operations schedules.
"""

import io
import csv
from datetime import datetime, timedelta
from typing import List, Dict, Any


def generate_khata_csv(records: List[Dict[str, Any]]) -> str:
    """
    Generates a RFC 4180 compliant CSV string containing Kisan Khata ledger transactions.
    Prepends UTF-8 Byte Order Mark (BOM) to guarantee clean rendering in Microsoft Excel
    with Hindi, Marathi, Gujarati, and other regional scripts.
    """
    output = io.StringIO()
    # Write UTF-8 BOM
    output.write("\ufeff")

    fieldnames = ["Date", "Type", "Category", "Amount_INR", "Notes", "Status"]
    writer = csv.DictWriter(output, fieldnames=fieldnames, lineterminator="\r\n")
    writer.writeheader()

    for item in records:
        writer.writerow({
            "Date": item.get("date", datetime.now().strftime("%Y-%m-%d")),
            "Type": item.get("type", "Expense"),
            "Category": item.get("category", "General Farm Operation"),
            "Amount_INR": f"{float(item.get('amount', 0.0)):.2f}",
            "Notes": item.get("notes", "").strip(),
            "Status": item.get("status", "Completed")
        })

    return output.getvalue()


def generate_crop_calendar_ics(
    crop_name: str,
    sowing_date_str: str,
    duration_days: int = 120,
    field_name: str = "Main Field"
) -> str:
    """
    Generates an RFC 5545 compliant iCalendar (.ics) string containing key phenological
    milestones: Sowing, First Irrigation, Weed Management, Mid-season Top Dressing,
    and Physiological Maturity/Harvest.
    """
    try:
        sowing_dt = datetime.strptime(sowing_date_str, "%Y-%m-%d")
    except ValueError:
        sowing_dt = datetime.now()

    milestones = [
        (0, "Sowing & Basal Fertilizer Application", "Sow certified seeds and apply basal NPK dose (DAP/Urea/MOP)."),
        (21, "CRI Stage & 1st Irrigation", "Crown root initiation stage (CRI). Critical irrigation window."),
        (35, "Weed Control & Foliar Spray", "Target broadleaf/grassy weeds before full canopy closure."),
        (60, "Active Tillering & Nitrogen Top Dressing", "Broadcast 2nd split dose of Urea/Neem coated urea."),
        (85, "Flowering & Moisture Monitoring", "Maintain optimal moisture; avoid water stress during anthesis."),
        (duration_days, "Physiological Maturity & Harvest", f"Harvest {crop_name} at recommended grain moisture.")
    ]

    now_stamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")

    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//AgriAssist//Agronomic Crop Calendar Engine//EN",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH"
    ]

    for offset_days, title, desc in milestones:
        event_dt = sowing_dt + timedelta(days=offset_days)
        dt_str = event_dt.strftime("%Y%m%d")
        dt_end = (event_dt + timedelta(days=1)).strftime("%Y%m%d")
        uid = f"agriassist-{crop_name.lower().replace(' ', '-')}-{offset_days}d-{dt_str}@agriassist.local"

        lines.extend([
            "BEGIN:VEVENT",
            f"UID:{uid}",
            f"DTSTAMP:{now_stamp}",
            f"DTSTART;VALUE=DATE:{dt_str}",
            f"DTEND;VALUE=DATE:{dt_end}",
            f"SUMMARY:{crop_name} - {title}",
            f"DESCRIPTION:{desc} [Field: {field_name}]",
            "LOCATION:Farm Plot",
            "STATUS:CONFIRMED",
            "TRANSP:TRANSPARENT",
            "END:VEVENT"
        ])

    lines.append("END:VCALENDAR")
    return "\r\n".join(lines)
