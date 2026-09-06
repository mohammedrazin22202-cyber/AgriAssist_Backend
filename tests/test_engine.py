import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.models import RecommendationRequest
from app.engine import recommend_crops

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "online"


def test_metadata_endpoint():
    response = client.get("/api/metadata")
    assert response.status_code == 200
    data = response.json()
    assert len(data["soil_types"]) >= 5
    assert len(data["seasons"]) >= 3
    assert "Cereal" in data["crop_categories"]


def test_kharif_black_soil_cotton_soybean_priority():
    """Cotton and Soybean are classic high-scoring crops for Black Soil in Kharif."""
    req = RecommendationRequest(
        mode="simple",
        soil_type="Black Soil (Regur)",
        season="Kharif",
        water_availability="Moderate (Canal / Tube-well / Seasonal)",
        budget_preference="Commercial / High Value"
    )
    result = recommend_crops(req)
    assert result.total_crops_evaluated > 10
    top_ids = [c.crop_id for c in result.recommendations[:5]]
    # Cotton, Soybean, or Pigeon Pea should rank in the top 5
    assert any(c in top_ids for c in ["cotton", "soybean", "pigeon_pea", "sorghum"])
    top_crop = result.recommendations[0]
    assert top_crop.suitability_score >= 80.0


def test_rabi_season_wheat_mustard_gram():
    """Rabi season in Alluvial Soil should prominently recommend Wheat, Mustard, or Gram."""
    req = RecommendationRequest(
        mode="simple",
        soil_type="Alluvial Soil",
        season="Rabi",
        water_availability="Moderate (Canal / Tube-well / Seasonal)"
    )
    result = recommend_crops(req)
    top_ids = [c.crop_id for c in result.recommendations[:5]]
    assert any(c in top_ids for c in ["wheat", "mustard", "chickpea", "potato"])


def test_water_scarcity_penalizes_high_water_crops():
    """In drought/rainfed conditions, Rice and Sugarcane must be penalized while Bajra ranks high."""
    req = RecommendationRequest(
        mode="simple",
        soil_type="Sandy Loam Soil",
        season="Kharif",
        water_availability="Low (Rainfed / Drought-prone)"
    )
    result = recommend_crops(req)
    
    # Find Rice and Bajra
    rice_rec = next((c for c in result.recommendations if c.crop_id == "rice"), None)
    bajra_rec = next((c for c in result.recommendations if c.crop_id == "pearl_millet"), None)
    
    assert rice_rec is not None
    assert bajra_rec is not None
    assert bajra_rec.suitability_score > rice_rec.suitability_score
    # Rice should have a severe warning about water
    assert any("demands high water" in w.lower() or "risk" in w.lower() for w in rice_rec.warnings)


def test_advanced_mode_custom_npk_and_ph():
    """Passing custom N-P-K and pH should properly reflect in recommendations."""
    req = RecommendationRequest(
        mode="advanced",
        soil_type="Red Soil",
        season="Kharif",
        water_availability="Moderate (Canal / Tube-well / Seasonal)",
        nitrogen=110.0,
        phosphorus=45.0,
        potassium=50.0,
        ph=6.5,
        temperature_c=26.0,
        rainfall_mm=750.0
    )
    result = recommend_crops(req)
    assert result.applied_parameters["nitrogen"] == 110.0
    assert result.applied_parameters["ph"] == 6.5
    assert len(result.recommendations) > 0


def test_api_recommend_post():
    payload = {
        "mode": "simple",
        "soil_type": "Clay Loam Soil",
        "season": "Kharif",
        "water_availability": "High (Assured Irrigation / River / Drip)"
    }
    response = client.post("/api/recommend", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "recommendations" in data
    assert len(data["recommendations"]) > 0
    # Rice should be well-suited for Clay Loam + Kharif + High water
    paddy = next((c for c in data["recommendations"] if c["crop_id"] == "rice"), None)
    assert paddy is not None
    assert paddy["suitability_score"] >= 80.0
