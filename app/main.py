"""FastAPI backend application for AgriAssist.
Provides REST endpoints for crop recommendations, agronomic metadata, and crop profiles.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, Any

from app.models import (
    RecommendationRequest,
    RecommendationResponse,
    CropRecommendation
)
from app.engine import recommend_crops
from app.database import get_all_crops, get_crop_by_id
from app.soil_presets import SOIL_PRESETS, SEASON_METADATA, WATER_AVAILABILITY_LEVELS

app = FastAPI(
    title="AgriAssist Decision Support API",
    description="Agronomic intelligence API to guide farmers on what crops to sow.",
    version="1.0.0"
)

# Enable CORS for local frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health_check():
    return {
        "status": "online",
        "service": "AgriAssist Engine",
        "version": "1.0.0"
    }


@app.get("/api/metadata")
def get_metadata():
    """Returns dropdown options, soil presets, and seasonal data for the farmer UI."""
    return {
        "soil_types": [
            {
                "name": k,
                "description": v["description"],
                "color_hint": v.get("color_hint", ""),
                "texture": v.get("texture", ""),
                "default_n": v["default_n"],
                "default_p": v["default_p"],
                "default_k": v["default_k"],
                "default_ph": v["default_ph"],
                "drainage": v["drainage"]
            }
            for k, v in SOIL_PRESETS.items()
        ],
        "seasons": [
            {
                "key": k,
                "name": v["name"],
                "sowing_period": v["sowing_period"],
                "harvest_period": v["harvest_period"],
                "description": v["description"],
                "typical_temp_c": v["typical_temp_c"],
                "typical_rainfall_mm": v["typical_rainfall_mm"]
            }
            for k, v in SEASON_METADATA.items()
        ],
        "water_availability": [
            {
                "name": k,
                "description": v["description"]
            }
            for k, v in WATER_AVAILABILITY_LEVELS.items()
        ],
        "budget_preferences": [
            {"id": "Low Cost", "label": "Low Cost (Minimal inputs, low risk)"},
            {"id": "Balanced", "label": "Balanced (Standard fertilizer & certified seeds)"},
            {"id": "Commercial / High Value", "label": "Commercial / High Value (Maximize market profits)"}
        ],
        "land_types": [
            {"id": "Plain", "label": "Plain Flat Land"},
            {"id": "Slope / Hill", "label": "Slope / Hill / Well-drained Upland"},
            {"id": "Lowland", "label": "Lowland (Prone to seasonal waterlogging)"}
        ],
        "crop_categories": ["All", "Cereal", "Pulse", "Oilseed", "Cash Crop", "Fiber", "Vegetable", "Spices"]
    }


@app.post("/api/recommend", response_model=RecommendationResponse)
def get_crop_recommendations(req: RecommendationRequest):
    """Computes ranked crop recommendations based on farmer's soil, season, and water access."""
    try:
        return recommend_crops(req)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Recommendation engine error: {str(e)}")


@app.get("/api/crops")
def list_crops():
    """Returns directory of all crops in knowledge base."""
    crops = get_all_crops()
    return [
        {
            "id": c["id"],
            "name": c["name"],
            "hindi_name": c.get("hindi_name"),
            "category": c["category"],
            "seasons": c["seasons"],
            "water_requirement": c["water_requirement"],
            "duration_days": c["duration_days"],
            "profit_potential": c["profit_potential"]
        }
        for c in crops
    ]


@app.get("/api/crops/{crop_id}")
def get_crop_details(crop_id: str):
    """Retrieves in-depth agronomic profile of a specific crop."""
    crop = get_crop_by_id(crop_id)
    if not crop:
        raise HTTPException(status_code=404, detail=f"Crop with ID '{crop_id}' not found.")
    return crop
