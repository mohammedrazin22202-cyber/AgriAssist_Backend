import pytest
from app.database import CROPS_DATABASE, CROP_METADATA_EXTENSIONS, get_all_crops, get_crop_by_id
from app.engine import recommend_crops
from app.models import RecommendationRequest

EXPECTED_CATEGORIES = {
    "Cereal", "Pulse", "Oilseed", "Cash Crop", "Fiber", "Vegetable", "Spices"
}

REQUIRED_CROPS_DB_KEYS = {
    "id", "name", "hindi_name", "scientific_name", "category",
    "suitable_soils", "tolerated_soils", "min_ph", "max_ph", "optimal_ph_min", "optimal_ph_max",
    "min_temp", "max_temp", "optimal_temp_min", "optimal_temp_max",
    "min_rainfall", "max_rainfall", "water_requirement", "seasons",
    "sowing_window", "duration_days", "estimated_yield_per_acre",
    "investment_level", "profit_potential", "ideal_n", "ideal_p", "ideal_k",
    "sowing_tips", "fertilizer_advice", "soil_notes", "risk_factors", "companion_crops"
}

REQUIRED_EXTENSION_KEYS = {
    "msp_per_quintal", "seed_rate_kg_acre", "seed_cost_per_kg",
    "cultivation_cost_per_acre", "yield_quintal_min", "yield_quintal_max",
    "is_legume", "growth_stages"
}

REQUIRED_GROWTH_STAGE_KEYS = {"day_range", "stage_name", "activities", "pest_warning"}


def test_database_exact_100_crops():
    """Verify that exactly 100 crops exist with unique IDs."""
    assert len(CROPS_DATABASE) == 100, f"Expected 100 crops in CROPS_DATABASE, found {len(CROPS_DATABASE)}"
    assert len(CROP_METADATA_EXTENSIONS) == 100, f"Expected 100 extensions, found {len(CROP_METADATA_EXTENSIONS)}"
    
    db_ids = [crop["id"] for crop in CROPS_DATABASE]
    assert len(set(db_ids)) == 100, "Duplicate crop ID found in CROPS_DATABASE"
    assert set(db_ids) == set(CROP_METADATA_EXTENSIONS.keys()), "Mismatch between CROPS_DATABASE and CROP_METADATA_EXTENSIONS keys"


def test_all_crops_have_valid_schemas():
    """Verify all 100 crops possess all 32 core keys and 8 extension keys."""
    for crop in CROPS_DATABASE:
        crop_id = crop["id"]
        missing_db_keys = REQUIRED_CROPS_DB_KEYS - set(crop.keys())
        assert not missing_db_keys, f"Crop '{crop_id}' is missing core keys: {missing_db_keys}"

        assert crop["category"] in EXPECTED_CATEGORIES, f"Crop '{crop_id}' has unexpected category '{crop['category']}'"
        assert len(crop["seasons"]) >= 1, f"Crop '{crop_id}' must have at least one season"
        assert len(crop["suitable_soils"]) >= 1, f"Crop '{crop_id}' must have at least one suitable soil"

        # Bounds checks
        assert crop["min_ph"] <= crop["optimal_ph_min"] <= crop["optimal_ph_max"] <= crop["max_ph"]
        assert crop["min_temp"] <= crop["optimal_temp_min"] <= crop["optimal_temp_max"] <= crop["max_temp"]
        assert crop["min_rainfall"] <= crop["max_rainfall"]
        assert crop["ideal_n"] >= 0
        assert crop["ideal_p"] >= 0
        assert crop["ideal_k"] >= 0

        # Extension checks
        ext = CROP_METADATA_EXTENSIONS[crop_id]
        missing_ext_keys = REQUIRED_EXTENSION_KEYS - set(ext.keys())
        assert not missing_ext_keys, f"Crop '{crop_id}' is missing extension keys: {missing_ext_keys}"

        assert ext["msp_per_quintal"] > 0
        assert ext["seed_rate_kg_acre"] > 0
        assert ext["seed_cost_per_kg"] >= 0
        assert ext["cultivation_cost_per_acre"] > 0
        assert ext["yield_quintal_min"] <= ext["yield_quintal_max"]
        assert isinstance(ext["is_legume"], bool)

        # 4-stage growth timeline
        stages = ext["growth_stages"]
        assert len(stages) == 4, f"Crop '{crop_id}' must have exactly 4 growth stages, found {len(stages)}"
        for idx, stage in enumerate(stages):
            missing_stage_keys = REQUIRED_GROWTH_STAGE_KEYS - set(stage.keys())
            assert not missing_stage_keys, f"Crop '{crop_id}' stage {idx} missing keys: {missing_stage_keys}"


def test_category_distribution():
    """Verify category counts match expected distribution totaling 100 crops."""
    counts = {}
    for crop in CROPS_DATABASE:
        cat = crop["category"]
        counts[cat] = counts.get(cat, 0) + 1

    expected_counts = {
        "Cereal": 15,
        "Pulse": 13,
        "Oilseed": 10,
        "Cash Crop": 15,
        "Fiber": 5,
        "Vegetable": 26,
        "Spices": 16,
    }
    assert counts == expected_counts, f"Category count mismatch: got {counts}, expected {expected_counts}"


def test_get_all_crops_and_get_by_id():
    """Verify get_all_crops() returns all 100 merged crops."""
    all_crops = get_all_crops()
    assert len(all_crops) == 100
    
    for crop in all_crops:
        assert "msp_per_quintal" in crop
        assert "growth_stages" in crop
        
        single = get_crop_by_id(crop["id"])
        assert single is not None
        assert single["id"] == crop["id"]


def test_recommend_engine_across_all_seasons():
    """Verify recommendation engine evaluates all 100 crops across Kharif, Rabi, and Zaid."""
    for season in ["Kharif", "Rabi", "Zaid"]:
        req = RecommendationRequest(
            soil_type="Alluvial Soil",
            season=season,
            water_availability="Moderate",
            nitrogen=200.0,
            phosphorus=40.0,
            potassium=240.0,
            ph=7.0,
            temperature_c=26.0,
            rainfall_mm=700.0
        )
        response = recommend_crops(req)
        assert response.total_crops_evaluated == 100, f"Expected 100 crops evaluated, got {response.total_crops_evaluated}"
        assert len(response.recommendations) >= 5, f"Expected at least 5 recommendations for season {season}"
        for rec in response.recommendations:
            assert rec.suitability_score >= 0
            assert rec.name != ""
            assert rec.hindi_name != ""
            assert rec.financials is not None
