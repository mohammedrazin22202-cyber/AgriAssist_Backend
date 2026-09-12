import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_districts_endpoint():
    """Verify state and district agro-climatic registry."""
    response = client.get("/api/districts")
    assert response.status_code == 200
    data = response.json()
    assert "states" in data
    assert "Punjab" in data["states"]
    assert "Maharashtra" in data["states"]
    punjab_districts = data["states"]["Punjab"]
    assert len(punjab_districts) >= 2
    ludhiana = next((d for d in punjab_districts if d["district"] == "Ludhiana"), None)
    assert ludhiana is not None
    assert ludhiana["soil_type"] == "Alluvial Soil"


def test_plant_doctor_diagnose():
    """Verify pest & disease diagnosis with IPM prescriptions."""
    payload = {
        "crop_id": "cotton",
        "plant_part": "Fruit/Grain",
        "search_term": "pink"
    }
    response = client.post("/api/plant-doctor/diagnose", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["total_matches"] >= 1
    issue = data["issues"][0]
    assert "Pink Bollworm" in issue["name"]
    assert issue["severity"] == "Critical"
    assert len(issue["biological_control"]) > 0
    assert len(issue["chemical_control"]) > 0
    assert issue["pre_harvest_interval_days"] > 0


def test_plant_doctor_symptoms_metadata():
    """Verify symptom catalog metadata for frontend dropdowns."""
    response = client.get("/api/plant-doctor/symptoms")
    assert response.status_code == 200
    data = response.json()
    assert "crops" in data
    assert "affected_parts" in data
    assert "Leaf" in data["affected_parts"]


def test_mandi_prices_endpoint():
    """Verify APMC mandi price retrieval, 30-day trends, and MSP comparisons."""
    response = client.get("/api/mandi-prices?crop_id=wheat")
    assert response.status_code == 200
    data = response.json()
    assert data["total_mandis"] >= 1
    mandi = data["prices"][0]
    assert mandi["crop_id"] == "wheat"
    assert mandi["modal_price_per_quintal"] >= mandi["msp_price"]
    assert len(mandi["historical_30d"]) == 7
    assert len(mandi["selling_advice"]) > 0


def test_smart_irrigation_scheduler():
    """Verify stage-wise water volume and pumping runtime calculations."""
    payload = {
        "crop_id": "wheat",
        "growth_stage": "Crown Root Initiation (CRI at 21 days)",
        "soil_type": "Alluvial Soil",
        "land_size_acres": 2.0,
        "pump_hp": 5.0,
        "forecast_rain_mm": 0.0
    }
    response = client.post("/api/irrigation-schedule", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["water_depth_mm"] > 0
    assert data["water_volume_liters"] > 100000
    assert data["pump_runtime_hours"] > 0
    assert not data["rain_warning"]

    # Test with forecast rain > 15 mm -> rain warning must be active
    payload_rain = dict(payload)
    payload_rain["forecast_rain_mm"] = 28.0
    response_rain = client.post("/api/irrigation-schedule", json=payload_rain)
    assert response_rain.status_code == 200
    data_rain = response_rain.json()
    assert data_rain["rain_warning"]
    assert "POSTPONE" in data_rain["advisory_notes"].upper()


def test_organic_prescription_endpoint():
    """Verify Jaivik Kheti / ZBNF recipe dosages for given acreage."""
    payload = {
        "crop_id": "chickpea",
        "land_size_acres": 2.5
    }
    response = client.post("/api/organic-prescription", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["total_jeevamrutha_liters"] == 1000.0  # 400L/acre * 2.5
    assert len(data["recipes"]) >= 4
    # Chickpea is a pulse -> Rhizobium must be prescribed
    assert any("rhizobium" in b.lower() for b in data["biofertilizers"])


def test_government_schemes_calculator():
    """Verify PMFBY insurance premium, KCC limits, and PMKSY drip subsidies."""
    payload = {
        "crop_id": "rice",
        "land_size_acres": 2.0,
        "farmer_category": "Small / Marginal (< 2 Ha)"
    }
    response = client.post("/api/government-schemes/calculate", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["sum_insured_inr"] > 50000
    assert data["farmer_pmfby_premium_inr"] > 0
    assert data["govt_pmfby_subsidy_inr"] > data["farmer_pmfby_premium_inr"]
    assert data["kcc_crop_loan_limit_inr"] > 0
    assert data["drip_subsidy_pct"] == 55.0
    assert data["pm_kisan_annual_inr"] == 6000.0
    assert len(data["schemes"]) >= 4


def test_seed_calculator_endpoint():
    """Verify precision seed rate, planting geometry and estimated plant population."""
    # Test Wheat seed calculation for 2.5 acres
    payload = {
        "crop_id": "wheat",
        "land_size_acres": 2.5,
        "germination_rate_pct": 85.0
    }
    response = client.post("/api/seed-calculator", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["crop_id"] == "wheat"
    assert data["recommended_seed_rate_kg_per_acre"] == 40.0
    assert data["total_seed_required_kg"] == 100.0  # 40 kg/acre * 2.5 acres
    assert data["standard_row_spacing_cm"] == 22.5
    assert data["standard_plant_spacing_cm"] == 5.0
    assert data["population_per_acre"] > 300000
    assert data["estimated_plant_population"] > 750000
    assert data["estimated_seed_cost_inr"] > 0
    assert "Azotobacter" in data["seed_treatment_protocol"]

    # Test seed rate adjustment when germination rate is lower (e.g. 70%)
    payload_low_germ = {
        "crop_id": "cotton",
        "land_size_acres": 1.0,
        "germination_rate_pct": 70.0
    }
    response_low = client.post("/api/seed-calculator", json=payload_low_germ)
    assert response_low.status_code == 200
    data_low = response_low.json()
    assert data_low["recommended_seed_rate_kg_per_acre"] > 1.8  # compensated for lower germination


def test_seed_guidelines_catalog_endpoint():
    """Verify reference seed rates and spacing catalog."""
    response = client.get("/api/seed-calculator/guidelines")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 8
    wheat_item = next((c for c in data if c["crop_id"] == "wheat"), None)
    assert wheat_item is not None
    assert wheat_item["seed_rate_kg_acre"] == 40.0


def test_rotation_zero_acres_edge_case():
    """Verify rotation planner handles 0.0 or negative acres gracefully without ZeroDivisionError."""
    payload = {
        "soil_type": "Black Soil (Regur)",
        "land_size_acres": 0.0,
        "water_availability": "Moderate (Canal / Tube-well / Seasonal)"
    }
    response = client.post("/api/rotation-plan", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "plans" in data
    assert len(data["plans"]) >= 1
    plan = data["plans"][0]
    assert plan["total_annual_net_profit_inr"] > 0
    assert plan["soil_health_index"] >= 50


def test_plant_doctor_field_aliases():
    """Verify Plant Doctor accepts frontend aliases: affected_part and symptom_query."""
    payload = {
        "crop_id": "cotton",
        "affected_part": "Fruit/Grain",
        "symptom_query": "pink"
    }
    response = client.post("/api/plant-doctor/diagnose", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["total_matches"] >= 1
    assert "Pink Bollworm" in data["issues"][0]["name"]


def test_mandi_prices_markets_compatibility():
    """Verify Mandi prices response includes 'markets' compatibility alias for frontend."""
    response = client.get("/api/mandi-prices?crop_id=wheat")
    assert response.status_code == 200
    data = response.json()
    assert "markets" in data
    assert len(data["markets"]) > 0
    assert data["markets"][0]["crop_id"] == "wheat"


def test_irrigation_compatibility_fields():
    """Verify Smart Irrigation accepts pump_capacity_hp and returns total_water_volume_liters, pump_run_hours, interval_days."""
    payload = {
        "crop_id": "wheat",
        "growth_stage": "Crown Root Initiation (CRI at 21 days)",
        "soil_type": "Alluvial Soil",
        "land_size_acres": 2.0,
        "pump_capacity_hp": 5.0,
        "forecast_rain_mm": 20.0
    }
    response = client.post("/api/irrigation-schedule", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["total_water_volume_liters"] == data["water_volume_liters"]
    assert data["pump_run_hours"] == data["pump_runtime_hours"]
    assert "10" in data["interval_days"]
    assert data["irrigation_interval_days"] == 10
    assert data["postpone_irrigation_alert"] is not None


def test_organic_prescription_liters_aliases():
    """Verify Organic Doctor returns jeevamrutha_liters and beejamrit_liters."""
    payload = {
        "crop_id": "wheat",
        "land_size_acres": 2.0
    }
    response = client.post("/api/organic-prescription", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["jeevamrutha_liters"] == data["total_jeevamrutha_liters"]
    assert data["beejamrit_liters"] == data["beejamrit_kg"]


def test_government_schemes_nested_structure():
    """Verify Government Schemes response contains nested pmfby, kcc, pmksy_drip structures."""
    payload = {
        "crop_id": "rice",
        "land_size_acres": 2.0,
        "farmer_category": "Small / Marginal (< 2 Ha)"
    }
    response = client.post("/api/government-schemes/calculate", json=payload)
    assert response.status_code == 200
    data = response.json()
    # Check nested structures for frontend renderYojanaResult
    assert "pmfby" in data
    assert data["pmfby"]["season_category"] in ["Kharif", "Rabi", "Commercial / Horticultural"]
    assert data["pmfby"]["sum_insured_inr"] > 0
    assert "kcc" in data
    assert data["kcc"]["effective_interest_rate_percent"] == 4.0
    assert "pmksy_drip" in data
    assert data["pmksy_drip"]["subsidy_percentage"] == 55.0
    assert data["pm_kisan_annual_cash_inr"] == 6000


def test_sprayer_calculator_per_liter():
    """Verify knapsack sprayer calculation with dosage per liter."""
    payload = {
        "tank_capacity_liters": 16.0,
        "land_size_acres": 2.0,
        "dosage_mode": "per_liter",
        "dosage_amount": 2.5,
        "chemical_form": "Liquid (ml)",
        "spray_volume_liters_per_acre": 150.0
    }
    response = client.post("/api/sprayer-calculator", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["chemical_per_tank"] == 40.0  # 2.5 ml * 16 L
    assert data["total_water_liters"] == 300.0  # 2 acres * 150 L
    assert data["tanks_needed_total"] == 18.8  # 300 / 16
    assert data["chemical_unit"] == "ml"
    assert len(data["safety_checklist"]) >= 3


def test_sprayer_calculator_per_acre():
    """Verify knapsack sprayer calculation with dosage per acre."""
    payload = {
        "tank_capacity_liters": 15.0,
        "land_size_acres": 1.0,
        "dosage_mode": "per_acre",
        "dosage_amount": 300.0,
        "chemical_form": "Powder (g)",
        "spray_volume_liters_per_acre": 150.0
    }
    response = client.post("/api/sprayer-calculator", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["total_chemical_needed"] == 300.0
    assert data["chemical_per_tank"] == 30.0  # (300 / 10 tanks)
    assert data["chemical_unit"] == "grams"


def test_solar_pump_calculator():
    """Verify solar pump sizing and PM-KUSUM 60-80% subsidy breakdown."""
    payload = {
        "water_source": "Borewell",
        "water_depth_feet": 180.0,
        "land_size_acres": 3.0,
        "irrigation_type": "Drip / Sprinkler",
        "farmer_category": "Small / Marginal (< 2 Ha)"
    }
    response = client.post("/api/solar-pump-calculator", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["recommended_pump_hp"] >= 3.0
    assert data["recommended_solar_array_kw"] >= 3.0
    assert data["central_subsidy_inr"] > 0
    assert data["state_subsidy_inr"] > 0
    assert data["farmer_share_inr"] < data["total_estimated_cost_inr"]
    assert data["subsidy_percentage_total"] == 70.0  # 30% central + 40% state for marginal
    assert data["annual_diesel_savings_inr"] > 20000.0
    assert data["payback_period_years"] > 0.5


def test_intercropping_endpoint():
    """Verify synergistic companion crop combinations and LER."""
    response = client.get("/api/intercropping")
    assert response.status_code == 200
    data = response.json()
    assert data["total_pairs"] >= 8
    # Test specific crop filter
    response_cane = client.get("/api/intercropping?crop_id=sugarcane")
    assert response_cane.status_code == 200
    cane_data = response_cane.json()
    assert cane_data["total_pairs"] >= 2
    assert any("Mustard" in p["companion_crop_name"] for p in cane_data["pairs"])


def test_grain_storage_catalog_and_risk_check():
    """Verify grain moisture safe thresholds and risk check evaluation."""
    # 1. Catalog
    response_cat = client.get("/api/grain-storage/advisory")
    assert response_cat.status_code == 200
    cat_data = response_cat.json()
    assert len(cat_data) >= 5
    wheat_advisory = next((c for c in cat_data if c["crop_id"] == "wheat"), None)
    assert wheat_advisory is not None
    assert wheat_advisory["safe_moisture_limit_pct"] == 12.0

    # 2. Safe check
    payload_safe = {
        "crop_id": "wheat",
        "measured_moisture_pct": 11.5,
        "storage_method": "Jute Gunny Bags"
    }
    resp_safe = client.post("/api/grain-storage/check-risk", json=payload_safe)
    assert resp_safe.status_code == 200
    data_safe = resp_safe.json()
    assert "Safe" in data_safe["risk_level"]
    assert data_safe["sun_drying_hours_needed"] == 0.0

    # 3. Critical spoilage check (> 14.5% for wheat)
    payload_danger = {
        "crop_id": "wheat",
        "measured_moisture_pct": 16.0,
        "storage_method": "Jute Gunny Bags"
    }
    resp_danger = client.post("/api/grain-storage/check-risk", json=payload_danger)
    assert resp_danger.status_code == 200
    data_danger = resp_danger.json()
    assert "Critical" in data_danger["risk_level"]
    assert data_danger["sun_drying_hours_needed"] > 10.0



