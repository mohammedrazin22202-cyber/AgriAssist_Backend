import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.agri_tools import (
    calculate_post_harvest_aeration,
    calculate_polyhouse_climate_control,
    calculate_biochar_and_stubble_management
)

client = TestClient(app)


def test_post_harvest_aeration_calculations():
    """Verify grain aeration moisture removal, CFM requirements, and safe storage limits."""
    # Test Paddy at 20% moisture dried to 12%
    res = calculate_post_harvest_aeration(
        grain_type="Paddy (Rice)",
        quantity_quintals=100.0,
        initial_moisture_pct=20.0,
        target_moisture_pct=12.0,
        ambient_temp_c=28.0,
        ambient_rh_pct=65.0
    )
    assert res["grain_type"] == "Paddy (Rice)"
    assert res["quantity_quintals"] == 100.0
    assert res["moisture_to_remove_kg"] > 800.0  # Approx 909 kg
    assert res["final_quantity_quintals"] < 100.0
    assert res["aeration_fan_airflow_cfm"] >= 200.0
    assert res["fan_power_hp_estimate"] > 0.1
    assert res["safe_storage_duration_days"] < 15  # At 20% moisture, safe days are short!
    assert "Critical Hazard" in res["storage_risk_level"]
    assert len(res["recommended_protocols"]) >= 3

    # Test REST API endpoint
    payload = {
        "grain_type": "Wheat",
        "quantity_quintals": 50.0,
        "initial_moisture_pct": 14.0,
        "target_moisture_pct": 11.5,
        "ambient_temp_c": 25.0,
        "ambient_rh_pct": 60.0
    }
    response = client.post("/api/post-harvest-aeration", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["moisture_to_remove_kg"] > 0
    assert data["equilibrium_moisture_content_pct"] > 0


def test_polyhouse_climate_control():
    """Verify greenhouse ventilation, evaporative pad sizing, VPD, and MIDH subsidy."""
    # NVPH Test
    res_nvph = calculate_polyhouse_climate_control(
        structure_type="Naturally Ventilated Polyhouse (NVPH)",
        covered_area_sqm=1008.0,
        crop_type="Bell Pepper (Colored Capsicum)",
        ambient_max_temp_c=40.0,
        ambient_min_rh_pct=30.0
    )
    assert res_nvph["covered_area_sqm"] == 1008.0
    assert res_nvph["polyhouse_volume_m3"] > 3000.0
    assert res_nvph["ridge_vent_area_sqm"] > 100.0
    assert res_nvph["vapor_pressure_deficit_kpa"] > 0.5
    assert res_nvph["estimated_midh_subsidy_inr"] > 400000.0  # 50% of 1008 * 844 = 425,376

    # Fan-and-Pad Test
    res_fan = calculate_polyhouse_climate_control(
        structure_type="Fan-and-Pad Evaporative Greenhouse",
        covered_area_sqm=1008.0,
        crop_type="Indeterminate Tomato",
        ambient_max_temp_c=42.0,
        ambient_min_rh_pct=25.0
    )
    assert res_fan["number_of_exhaust_fans_50inch"] >= 4
    assert res_fan["cooling_pad_area_sqm"] > 30.0
    assert res_fan["cooling_water_flow_rate_lph"] > 10000.0
    assert res_fan["expected_inside_temp_c"] < 35.0  # Evaporative cooling drops temperature

    # Test REST API endpoint
    response = client.post("/api/polyhouse-climate", json={
        "structure_type": "Naturally Ventilated Polyhouse (NVPH)",
        "covered_area_sqm": 500.0,
        "crop_type": "Strawberry"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["estimated_midh_subsidy_inr"] > 200000.0


def test_biochar_and_stubble_management():
    """Verify crop residue biomass generation, biochar yield, averted emissions, and C:N recipe."""
    res = calculate_biochar_and_stubble_management(
        residue_crop="Paddy Straw (Parali)",
        land_size_acres=5.0
    )
    assert res["land_size_acres"] == 5.0
    assert res["estimated_residue_biomass_quintals"] == 140.0  # 5 * 28
    assert res["biochar_yield_quintals"] == 42.0  # 30% of 140
    assert res["economic_value_biochar_inr"] == 63000.0  # 4200 kg * 15
    assert res["soil_water_retention_gain_liters"] > 10000.0
    assert res["co2_emissions_averted_kg"] > 10000.0
    assert res["pm25_pollution_averted_kg"] > 50.0
    assert res["ngt_fine_penalty_averted_inr"] == 5000.0
    assert "cow_dung_slurry_required_kg" in res["composting_recipe"]

    # Test REST API endpoint
    response = client.post("/api/stubble-biochar", json={
        "residue_crop": "Cotton Stalks",
        "land_size_acres": 2.5
    })
    assert response.status_code == 200
    data = response.json()
    assert data["biochar_yield_quintals"] > 0
    assert data["economic_value_biochar_inr"] > 0
