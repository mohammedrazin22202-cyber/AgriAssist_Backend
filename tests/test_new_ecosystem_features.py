"""Tests for the new advanced features:
1. Precision Drip Fertigation & Venturi Schedule
2. Carbon Credits & Regenerative Agriculture
3. Integrated Farming System (IFS) Planner & Silage Sizer
4. Kisan Conversational AI Assistant
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_fertigation_schedule_endpoint():
    payload = {
        "crop_id": "tomato",
        "land_size_acres": 2.0,
        "growth_stage": "Flowering / Fruit Set (31-60 DAP)",
        "drip_lateral_spacing_m": 1.2,
        "dripper_spacing_m": 0.4,
        "dripper_discharge_lph": 2.0,
        "venturi_suction_rate_lph": 60.0
    }
    response = client.post("/api/fertigation-schedule", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["crop_id"] == "tomato"
    assert data["land_size_acres"] == 2.0
    assert data["total_emitters_count"] > 10000
    assert len(data["water_soluble_fertilizers"]) >= 3
    assert data["venturi_injection_minutes_per_cycle"] > 0
    assert "Phosphoric Acid" in data["acid_wash_cleaning_protocol"]


def test_carbon_credits_endpoint():
    payload = {
        "land_size_acres": 10.0,
        "practices_adopted": [
            "Zero Tillage / No-Till",
            "Biochar Soil Application",
            "Solar Agricultural Pump (PM-KUSUM)"
        ],
        "voluntary_carbon_price_usd_per_ton": 25.0,
        "inr_per_usd": 85.0
    }
    response = client.post("/api/carbon-credits", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["land_size_acres"] == 10.0
    assert data["practices_count"] == 3
    assert data["annual_total_tco2e_sequestered"] > 0
    assert data["gross_revenue_inr"] > 0
    assert data["net_farmer_carbon_payout_inr"] > 0
    assert len(data["practice_breakdowns"]) == 3
    assert len(data["soil_and_climate_co_benefits"]) >= 3


def test_integrated_farming_plan_endpoint():
    payload = {
        "total_land_acres": 4.0,
        "enterprises": [
            "Field Crops & Vegetables",
            "Dairy Cattle",
            "Farm Pond Aquaculture",
            "Vermicomposting & Biogas"
        ],
        "cattle_count": 3,
        "poultry_birds": 60,
        "pond_area_sqm": 600.0
    }
    response = client.post("/api/integrated-farming/plan", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["total_land_acres"] == 4.0
    assert data["annual_net_profit_inr"] > 0
    assert len(data["internal_resource_recycling_loops"]) >= 3
    assert data["silage_dry_period_buffer_tons"] > 0
    assert data["silage_pit_length_m"] > 0
    assert data["sustainability_index_score"] >= 70


def test_kisan_assistant_chat_intent_detection():
    # Crop intent in English
    res1 = client.post("/api/assistant/chat", json={"message": "What crop should I sow this Kharif season in black soil?", "language": "en"})
    assert res1.status_code == 200
    d1 = res1.json()
    assert d1["detected_intent"] == "crop_recommendation"
    assert d1["suggested_tab"] == "advisor"

    # Fertilizer intent in Hindi
    res2 = client.post("/api/assistant/chat", json={"message": "गेहूं में कितनी यूरिया और DAP खाद डालनी चाहिए?", "language": "hi"})
    assert res2.status_code == 200
    d2 = res2.json()
    assert d2["detected_intent"] == "fertilizer_prescription"
    assert d2["suggested_tab"] == "fertilizer"
    assert "यूरिया" in d2["reply_text"] or "DAP" in d2["reply_text"]

    # Carbon credits query
    res3 = client.post("/api/assistant/chat", json={"message": "How do I earn carbon credits from biochar and no-till?", "language": "en"})
    assert res3.status_code == 200
    d3 = res3.json()
    assert d3["detected_intent"] == "carbon_and_biochar"
    assert d3["suggested_tab"] == "carbon"
