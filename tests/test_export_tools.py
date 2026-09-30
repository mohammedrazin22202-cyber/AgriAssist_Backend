"""
Automated Pytest Suite for Agronomic Data Export Utilities.
Tests UTF-8 BOM CSV generation for Kisan Khata and RFC 5545 iCalendar generation.
"""

from fastapi.testclient import TestClient
from app.main import app
from app.export_tools import generate_khata_csv, generate_crop_calendar_ics

client = TestClient(app)


def test_generate_khata_csv_utf8_bom():
    sample_records = [
        {"date": "2026-07-01", "type": "Expense", "category": "Seeds (बीज)", "amount": 1200.0, "notes": "Wheat HD-2967 certified seeds"},
        {"date": "2026-07-15", "type": "Expense", "category": "Fertilizer (खाद)", "amount": 850.0, "notes": "2 bags Urea"},
        {"date": "2026-11-20", "type": "Income", "category": "Mandi Grain Sale", "amount": 45000.0, "notes": "Sold 20 quintals to APMC"}
    ]
    csv_str = generate_khata_csv(sample_records)
    # Check UTF-8 BOM
    assert csv_str.startswith("\ufeff")
    assert "Date,Type,Category,Amount_INR,Notes,Status" in csv_str
    assert "1200.00" in csv_str
    assert "Seeds (बीज)" in csv_str
    assert "45000.00" in csv_str


def test_generate_crop_calendar_ics():
    ics_str = generate_crop_calendar_ics(
        crop_name="Wheat (गेहूं)",
        sowing_date_str="2026-11-01",
        duration_days=120,
        field_name="North Plot"
    )
    assert "BEGIN:VCALENDAR" in ics_str
    assert "VERSION:2.0" in ics_str
    assert "BEGIN:VEVENT" in ics_str
    assert "SUMMARY:Wheat (गेहूं) - Sowing & Basal Fertilizer Application" in ics_str
    assert "SUMMARY:Wheat (गेहूं) - CRI Stage & 1st Irrigation" in ics_str
    assert "SUMMARY:Wheat (गेहूं) - Physiological Maturity & Harvest" in ics_str
    assert "END:VCALENDAR" in ics_str


def test_export_khata_csv_api_endpoint():
    records = [
        {"date": "2026-08-10", "type": "Expense", "category": "Labor", "amount": 600.0, "notes": "Weeding labor"}
    ]
    response = client.post("/api/export/khata-csv", json=records)
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    assert "attachment" in response.headers["content-disposition"]
    assert b"\xef\xbb\xbf" in response.content  # UTF-8 BOM bytes


def test_export_crop_calendar_ics_api_endpoint():
    payload = {
        "crop_name": "Mustard",
        "sowing_date": "2026-10-15",
        "duration_days": 110,
        "field_name": "South Acre"
    }
    response = client.post("/api/export/crop-calendar-ics", json=payload)
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/calendar")
    assert "attachment" in response.headers["content-disposition"]
    assert "BEGIN:VCALENDAR" in response.text
