"""Unit and API integration tests for the zero-cost agronomic features."""
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.agri_tools import (
    calculate_mandi_fair_payout,
    get_weed_management_recommendations,
    calculate_zecc_storage_and_shelf_life,
    calculate_natural_farming_formulation,
    calculate_fodder_and_silage_planner,
    calculate_nasa_agroclimatology_gdd
)

client = TestClient(app)


def test_mandi_fair_payout_engine():
    res = calculate_mandi_fair_payout(
        gross_weight_quintals=50.0,
        mandi_bid_rate_per_quintal=2275.0,
        measured_moisture_pct=15.0,
        foreign_matter_pct=1.5,
        trader_proposed_deduction_kg=250.0,
        crop_name="Wheat (गेहूं)"
    )
    assert res["gross_weight_quintals"] == 50.0
    assert res["standard_moisture_limit_pct"] == 12.0
    assert res["excess_moisture_pct"] == 3.0
    assert res["legitimate_moisture_cut_kg"] > 0
    assert res["foreign_matter_cut_kg"] > 0
    assert res["total_legitimate_cut_kg"] < 250.0  # Trader deducted way too much
    assert "Illegal / Excessive" in res["audit_verdict"]
    assert res["unjustified_trader_deduction_loss_inr"] > 0


def test_mandi_fair_payout_api():
    resp = client.post("/api/mandi-fair-payout", json={
        "crop_name": "Paddy / Rice (धान)",
        "gross_weight_quintals": 40.0,
        "mandi_bid_rate_per_quintal": 2203.0,
        "measured_moisture_pct": 14.0,
        "foreign_matter_pct": 0.8,
        "trader_proposed_deduction_kg": 0.0
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["standard_moisture_limit_pct"] == 14.0
    assert data["excess_moisture_pct"] == 0.0
    assert data["legitimate_moisture_cut_kg"] == 0.0
    assert "Fair APMC Settlement" in data["audit_verdict"]


def test_weed_management_engine():
    res = get_weed_management_recommendations(
        crop_id="wheat",
        weed_type="All",
        crop_stage="Post-Emergence (15-25 Days)",
        land_size_acres=2.5
    )
    assert res["crop_id"] == "wheat"
    assert len(res["options"]) >= 1
    assert any("Sulfosulfuron" in opt["herbicide_molecule"] for opt in res["options"])
    assert res["options"][0]["knapsack_tanks_15L_count"] >= 15
    assert len(res["cultural_and_organic_controls"]) >= 2


def test_weed_management_api():
    resp = client.post("/api/weed-management", json={
        "crop_id": "rice_paddy",
        "weed_type": "All",
        "crop_stage": "Pre-Emergence (0-3 Days)",
        "land_size_acres": 1.0
    })
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["options"]) >= 1
    assert any("Pretilachlor" in opt["herbicide_molecule"] for opt in data["options"])


def test_zecc_storage_engine():
    res = calculate_zecc_storage_and_shelf_life(
        storage_capacity_crates=25,
        primary_produce="Tomato (टमाटर)"
    )
    assert res["storage_capacity_crates"] == 25
    assert res["total_produce_kg"] == 500.0
    assert res["red_clay_bricks_required"] > 300
    assert res["coarse_river_sand_bags_50kg"] >= 4
    assert res["estimated_diy_cost_inr"] > 2000
    assert len(res["perishable_produce_database"]) >= 5


def test_zecc_storage_api():
    resp = client.post("/api/zecc-storage", json={
        "storage_capacity_crates": 20,
        "primary_produce": "Green Chilli (हरी मिर्च)"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["cavity_gap_cm"] == 7.5
    assert len(data["step_by_step_construction_guide"]) == 7


def test_natural_farming_formulation_engine():
    res_200 = calculate_natural_farming_formulation("jeevamrut", 200.0)
    assert res_200["volume_liters"] == 200.0
    cow_dung = next(i for i in res_200["ingredients"] if "Cow Dung" in i["name"])
    assert cow_dung["amount"] == 10.0

    res_50 = calculate_natural_farming_formulation("jeevamrut", 50.0)
    cow_dung_50 = next(i for i in res_50["ingredients"] if "Cow Dung" in i["name"])
    assert cow_dung_50["amount"] == 2.5  # Exactly 1/4th of 10kg


def test_natural_farming_api():
    resp = client.post("/api/natural-farming/formulation", json={
        "formulation_id": "agniastra",
        "volume_liters": 20.0
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "Agniastra" in data["title"]
    assert any("Neem" in i["name"] for i in data["ingredients"])
    assert data["shelf_life_days"] == 90


def test_fodder_silage_planner_engine():
    res = calculate_fodder_and_silage_planner(
        cows_count=3,
        buffaloes_count=1,
        average_milk_yield_liters_per_day=10.0,
        available_fodder_land_acres=1.0
    )
    assert res["total_livestock_units"] > 4.0
    assert res["daily_green_fodder_kg"] > 80.0
    assert res["recommended_silage_reserve_tons"] > 4.0
    assert res["silage_pit_trench_dimensions"]["length_ft"] > 5.0
    assert len(res["year_round_fodder_cropping_calendar"]) == 3


def test_fodder_silage_api():
    resp = client.post("/api/fodder-silage/plan", json={
        "cows_count": 2,
        "buffaloes_count": 0,
        "average_milk_yield_liters_per_day": 8.0,
        "available_fodder_land_acres": 0.5
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "Kharif" in data["year_round_fodder_cropping_calendar"][0]["season"]
    assert "molasses" in data["silage_additives"]["jaggery_or_molasses_kg"].lower()


def test_nasa_agroclimatology_gdd_api():
    resp = client.post("/api/nasa-power/gdd", json={
        "latitude": 18.5204,
        "longitude": 73.8567,
        "sowing_date": "2026-06-01",
        "crop_name": "Maize",
        "base_temperature_c": 10.0,
        "target_maturity_gdd": 1500.0
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["crop_name"] == "Maize"
    assert data["accumulated_gdd"] > 0
    assert data["progress_percentage"] > 0
    assert data["avg_daily_solar_insolation_mj_m2"] > 10.0
    assert len(data["thermal_stress_alerts"]) >= 1
