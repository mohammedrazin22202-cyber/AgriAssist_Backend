"""Unit tests for newly added zero-cost agricultural features:
1. Dairy & Livestock Ration Calculator, Gestation Calendar, and EVM Remedies.
2. Mandi Distance & Profit Arbitrage.
3. Soil Health Card Micronutrient Doctor.
4. Farm Pond (Khet Talab) Sizer.
5. Machinery Rent vs. Buy Calculator.
6. Dynamic Crop Calendar & RFC 5545 iCalendar Generator.
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


# ---------------- 1. Dairy & Livestock Advisory Tests ----------------
def test_livestock_ration_cow():
    """Verify ration calculation for crossbred dairy cow."""
    payload = {
        "animal_type": "Cow (Crossbred HF/Jersey)",
        "body_weight_kg": 400.0,
        "daily_milk_liters": 12.0,
        "milk_fat_pct": 4.0,
        "pregnancy_stage": "None"
    }
    response = client.post("/api/livestock/ration", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["dry_matter_requirement_kg"] > 8.0
    assert data["green_fodder_kg"] > 15.0
    assert data["dry_straw_bhusa_kg"] > 2.0
    assert data["concentrate_feed_kg"] >= 4.0
    assert data["mineral_mixture_grams"] == 50.0
    assert data["water_requirement_liters"] > 60.0
    assert len(data["feeding_tips"]) >= 3


def test_livestock_ration_buffalo_and_goat():
    """Verify ration calculation for buffalo and goat."""
    # Buffalo
    resp_buf = client.post("/api/livestock/ration", json={
        "animal_type": "Buffalo (Murrah)",
        "body_weight_kg": 500.0,
        "daily_milk_liters": 10.0,
        "pregnancy_stage": "Last Trimester (Advance Pregnant)"
    })
    assert resp_buf.status_code == 200
    data_buf = resp_buf.json()
    assert data_buf["concentrate_feed_kg"] >= 5.0
    assert data_buf["mineral_mixture_grams"] == 55.0

    # Goat
    resp_goat = client.post("/api/livestock/ration", json={
        "animal_type": "Goat",
        "body_weight_kg": 35.0,
        "daily_milk_liters": 2.0
    })
    assert resp_goat.status_code == 200
    data_goat = resp_goat.json()
    assert data_goat["concentrate_feed_kg"] < 2.0
    assert data_goat["mineral_mixture_grams"] == 15.0


def test_gestation_calendar():
    """Verify pregnancy milestones for cattle."""
    # Cow
    resp = client.post("/api/livestock/gestation", json={
        "animal_type": "Cow",
        "insemination_date": "2026-01-01"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["gestation_period_days"] == 280
    assert data["heat_check_date_21d"] == "2026-01-22"
    assert len(data["milestones"]) == 5

    # Buffalo
    resp_b = client.post("/api/livestock/gestation", json={
        "animal_type": "Buffalo",
        "insemination_date": "2026-01-01"
    })
    assert resp_b.status_code == 200
    assert resp_b.json()["gestation_period_days"] == 310


def test_livestock_remedies():
    """Verify Ethno-Veterinary Medicine formulations catalog."""
    response = client.get("/api/livestock/remedies")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 4
    mastitis = next((r for r in data if r["id"] == "mastitis"), None)
    assert mastitis is not None
    assert "Turmeric" in " ".join(mastitis["ingredients"])
    assert "Aloe" in " ".join(mastitis["ingredients"])


# ---------------- 2. Mandi Distance & Profit Arbitrage Tests ----------------
def test_mandi_arbitrage_profitable():
    """Verify distant mandi arbitrage when higher price justifies travel."""
    payload = {
        "crop_id": "wheat",
        "quantity_quintals": 50.0,
        "local_mandi_name": "Tehsil Mandi",
        "local_mandi_price": 2200.0,
        "local_mandi_distance_km": 10.0,
        "distant_mandi_name": "District Terminal Mandi",
        "distant_mandi_price": 2450.0,
        "distant_mandi_distance_km": 40.0,
        "vehicle_type": "Tractor Trolley",
        "diesel_price_per_liter": 90.0
    }
    response = client.post("/api/mandi-prices/arbitrage", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["is_distant_mandi_worth_it"] is True
    assert data["net_profit_difference"] > 5000.0
    assert "GO TO DISTANT MANDI" in data["recommendation"]


def test_mandi_arbitrage_unprofitable():
    """Verify warning when travel cost exceeds price differential."""
    payload = {
        "crop_id": "mustard",
        "quantity_quintals": 10.0,
        "local_mandi_name": "Local Mandi",
        "local_mandi_price": 5400.0,
        "local_mandi_distance_km": 5.0,
        "distant_mandi_name": "Distant Mandi",
        "distant_mandi_price": 5450.0,
        "distant_mandi_distance_km": 60.0,
        "vehicle_type": "Tractor Trolley",
        "diesel_price_per_liter": 90.0
    }
    response = client.post("/api/mandi-prices/arbitrage", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["is_distant_mandi_worth_it"] is False
    assert data["net_profit_difference"] < 0
    assert "SELL LOCALLY" in data["recommendation"]


# ---------------- 3. Soil Health Card Micronutrient Doctor Tests ----------------
def test_micronutrient_prescription():
    """Verify micronutrient prescriptions for Zinc, Sulfur, Boron, and Iron deficits."""
    payload = {
        "crop_id": "mustard",
        "land_size_acres": 2.0,
        "zinc_ppm": 0.40,
        "sulfur_ppm": 7.5,
        "boron_ppm": 0.30,
        "iron_ppm": 3.5,
        "organic_carbon_pct": 0.38
    }
    response = client.post("/api/fertilizer/micronutrients", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert len(data["prescriptions"]) == 4
    # Zinc
    zn = next((p for p in data["prescriptions"] if "Zinc" in p["nutrient"]), None)
    assert zn is not None
    assert "Deficient" in zn["soil_status"]
    assert zn["total_dosage_kg"] == 20.0
    # Sulfur for mustard (oilseed requires higher sulfur)
    s = next((p for p in data["prescriptions"] if "Sulfur" in p["nutrient"]), None)
    assert s is not None
    assert s["total_dosage_kg"] == 24.0
    # Organic carbon warning
    assert "CRITICAL" in data["organic_manure_advice"]
    assert len(data["foliar_spray_options"]) >= 2
    assert data["approx_total_cost_inr"] > 0


# ---------------- 4. Farm Pond Sizer Tests ----------------
def test_farm_pond_sizing():
    """Verify rainwater runoff harvesting and pond dimension calculation."""
    payload = {
        "catchment_acres": 6.0,
        "annual_rainfall_mm": 850.0,
        "catchment_soil_type": "Loam",
        "supplementary_irrigation_acres": 2.5,
        "dry_spell_days_target": 30
    }
    response = client.post("/api/water-conservation/farm-pond", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["storage_capacity_lakh_liters"] > 5.0
    assert data["recommended_top_length_m"] > data["recommended_top_width_m"]
    assert data["recommended_bottom_length_m"] > 0
    assert data["geomembrane_lining_area_sqm"] > 300.0
    assert data["pmksy_khet_talab_subsidy_inr"] > 0
    assert data["net_farmer_cost_inr"] < data["estimated_total_cost_inr"]


# ---------------- 5. Machinery Rent vs Buy Tests ----------------
def test_machinery_rent_vs_buy():
    """Verify break-even and recommendation for machinery."""
    # Small farm: Rent should be recommended
    resp_small = client.post("/api/machinery/rent-vs-buy", json={
        "machine_type": "Tractor 45-50 HP",
        "farm_size_acres": 4.0,
        "commercial_rental_acres_to_others": 0.0
    })
    assert resp_small.status_code == 200
    data_small = resp_small.json()
    assert "RENT" in data_small["recommendation"]

    # Large farm with commercial hiring: Buy should be recommended
    resp_large = client.post("/api/machinery/rent-vs-buy", json={
        "machine_type": "Tractor 45-50 HP",
        "farm_size_acres": 25.0,
        "commercial_rental_acres_to_others": 40.0
    })
    assert resp_large.status_code == 200
    data_large = resp_large.json()
    assert "BUY" in data_large["recommendation"]
    assert data_large["commercial_rental_income_inr"] > 0


# ---------------- 6. Dynamic Crop Calendar & ICS Tests ----------------
def test_crop_calendar_endpoint():
    """Verify crop milestone timeline and RFC 5545 iCalendar generation."""
    payload = {
        "crop_id": "wheat",
        "sowing_date": "2026-11-15",
        "land_size_acres": 2.0
    }
    response = client.post("/api/crop-calendar/generate", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["crop_name"] == "Wheat"
    assert len(data["events"]) >= 5
    assert data["events"][0]["activity_type"] == "Sowing"
    assert "BEGIN:VCALENDAR" in data["ics_calendar_text"]
    assert "BEGIN:VEVENT" in data["ics_calendar_text"]
    assert "END:VCALENDAR" in data["ics_calendar_text"]
