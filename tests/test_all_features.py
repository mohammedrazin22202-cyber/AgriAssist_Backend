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
