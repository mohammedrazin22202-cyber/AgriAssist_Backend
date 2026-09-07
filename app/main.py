"""FastAPI backend application for AgriAssist.
Provides REST endpoints for crop recommendations, agronomic metadata, and crop profiles.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, Any

from app.models import (
    RecommendationRequest,
    RecommendationResponse,
    CropRecommendation,
    RotationPlanRequest,
    RotationPlanResponse,
    StandaloneFertilizerRequest,
    FertilizerPrescription
)
from app.engine import recommend_crops
from app.database import get_all_crops, get_crop_by_id
from app.soil_presets import SOIL_PRESETS, SEASON_METADATA, WATER_AVAILABILITY_LEVELS
from app.agri_tools import generate_crop_rotation_plans, calculate_fertilizer_prescription


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


@app.post("/api/rotation-plan", response_model=RotationPlanResponse)
def get_crop_rotation_plan(req: RotationPlanRequest):
    """Generates ranked 1-Year Multi-Crop Rotation Plans (Kharif -> Rabi -> Zaid)."""
    try:
        plans = generate_crop_rotation_plans(
            soil_type=req.soil_type,
            water_availability=req.water_availability,
            budget_preference=req.budget_preference or "Balanced",
            land_size_acres=req.land_size_acres or 1.0
        )
        return RotationPlanResponse(
            soil_type=req.soil_type,
            water_availability=req.water_availability,
            land_size_acres=req.land_size_acres or 1.0,
            plans=plans
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Rotation planning error: {str(e)}")


@app.post("/api/fertilizer-prescription", response_model=FertilizerPrescription)
def get_fertilizer_prescription(req: StandaloneFertilizerRequest):
    """Calculates exact Urea, DAP, MOP bags and soil amendments for given soil and crop."""
    try:
        ideal_n = req.ideal_n
        ideal_p = req.ideal_p
        ideal_k = req.ideal_k
        if req.crop_id:
            crop = get_crop_by_id(req.crop_id)
            if crop:
                ideal_n = ideal_n if ideal_n is not None else crop.get("ideal_n", 100.0)
                ideal_p = ideal_p if ideal_p is not None else crop.get("ideal_p", 50.0)
                ideal_k = ideal_k if ideal_k is not None else crop.get("ideal_k", 40.0)

        ideal_n = ideal_n if ideal_n is not None else 100.0
        ideal_p = ideal_p if ideal_p is not None else 50.0
        ideal_k = ideal_k if ideal_k is not None else 40.0

        presc = calculate_fertilizer_prescription(
            soil_n=req.soil_n,
            soil_p=req.soil_p,
            soil_k=req.soil_k,
            soil_ph=req.soil_ph or 7.0,
            ideal_n=ideal_n,
            ideal_p=ideal_p,
            ideal_k=ideal_k,
            land_size_acres=req.land_size_acres or 1.0
        )
        return presc
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fertilizer calculation error: {str(e)}")

