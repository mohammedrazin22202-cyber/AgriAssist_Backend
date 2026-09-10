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
    FertilizerPrescription,
    PlantDoctorRequest,
    PlantDoctorResponse,
    MandiPriceResponse,
    IrrigationRequest,
    IrrigationScheduleResponse,
    OrganicPrescriptionRequest,
    OrganicPrescriptionResponse,
    GovtSchemesRequest,
    GovtSchemesResponse,
    StateDistrictResponse,
    SeedRateRequest,
    SeedRateResponse
)
from app.engine import recommend_crops
from app.database import get_all_crops, get_crop_by_id, get_all_pests_diseases, get_government_schemes_data
from app.soil_presets import SOIL_PRESETS, SEASON_METADATA, WATER_AVAILABILITY_LEVELS
from app.agri_tools import (
    generate_crop_rotation_plans,
    calculate_fertilizer_prescription,
    diagnose_plant_issue,
    get_mandi_prices_filtered,
    calculate_smart_irrigation,
    calculate_organic_prescription,
    calculate_government_schemes_and_kcc,
    get_district_presets,
    calculate_seed_rate_and_population,
    get_all_seed_crop_guidelines
)



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


# ---------------- Plant Doctor (Pest & Disease Diagnostic) ----------------
@app.post("/api/plant-doctor/diagnose", response_model=PlantDoctorResponse)
def diagnose_crop_health(req: PlantDoctorRequest):
    """Diagnoses crop pests and diseases and returns IPM prescriptions."""
    try:
        issues = diagnose_plant_issue(
            crop_id=req.crop_id,
            plant_part=req.plant_part,
            symptoms=req.symptoms,
            search_term=req.search_term
        )
        return PlantDoctorResponse(
            total_matches=len(issues),
            issues=issues
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Plant diagnostic error: {str(e)}")


@app.get("/api/plant-doctor/symptoms")
def get_plant_doctor_metadata():
    """Returns unique affected parts and symptoms catalog for interactive UI filters."""
    all_issues = get_all_pests_diseases()
    parts = set()
    symptoms = set()
    crops = set()

    for issue in all_issues:
        crops.add(issue["crop_name"])
        for p in issue.get("affected_parts", []):
            parts.add(p)
        for s in issue.get("symptoms", []):
            symptoms.add(s)

    return {
        "crops": sorted(list(crops)),
        "affected_parts": ["All"] + sorted(list(parts)),
        "sample_symptoms": sorted(list(symptoms))[:20]
    }


# ---------------- Mandi (APMC) Market Prices & Trends ----------------
@app.get("/api/mandi-prices", response_model=MandiPriceResponse)
def get_mandi_prices(crop_id: str = None, state: str = None, district: str = None):
    """Returns latest APMC mandi rates, 30-day price trends, and MSP comparison."""
    try:
        prices = get_mandi_prices_filtered(crop_id=crop_id, state=state, district=district)
        return MandiPriceResponse(
            total_mandis=len(prices),
            state=state,
            district=district,
            prices=prices
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Mandi price service error: {str(e)}")


# ---------------- Smart Irrigation & Water Budgeting ----------------
@app.post("/api/irrigation-schedule", response_model=IrrigationScheduleResponse)
def get_irrigation_schedule(req: IrrigationRequest):
    """Computes stage-wise water volume (liters/acre), pump runtimes, and weather postponement."""
    try:
        schedule = calculate_smart_irrigation(
            crop_id=req.crop_id,
            growth_stage=req.growth_stage,
            soil_type=req.soil_type,
            land_size_acres=req.land_size_acres,
            pump_hp=req.pump_hp,
            forecast_rain_mm=req.forecast_rain_mm or 0.0
        )
        return schedule
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Irrigation scheduler error: {str(e)}")


# ---------------- Organic & Natural Farming (Jaivik Kheti) ----------------
@app.post("/api/organic-prescription", response_model=OrganicPrescriptionResponse)
def get_organic_prescriptions(req: OrganicPrescriptionRequest):
    """Calculates biological preparations (Jeevamrutha, Beejamrit, Neemastra) and recipes."""
    try:
        prescription = calculate_organic_prescription(
            crop_id=req.crop_id,
            land_size_acres=req.land_size_acres
        )
        return prescription
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Organic farming error: {str(e)}")


# ---------------- Government Schemes & Subsidies ----------------
@app.post("/api/government-schemes/calculate", response_model=GovtSchemesResponse)
def calculate_schemes_and_kcc(req: GovtSchemesRequest):
    """Calculates PMFBY crop insurance premiums, KCC loan limits, and PMKSY drip subsidies."""
    try:
        result = calculate_government_schemes_and_kcc(
            crop_id=req.crop_id,
            land_size_acres=req.land_size_acres,
            farmer_category=req.farmer_category,
            state=req.state or "All-India"
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Government schemes calculation error: {str(e)}")


@app.get("/api/government-schemes")
def list_government_schemes():
    """Lists prominent central and state agricultural support schemes."""
    db = get_government_schemes_data()
    return db.get("schemes_list", [])


# ---------------- State & District Agro-Climatic Presets ----------------
@app.get("/api/districts", response_model=StateDistrictResponse)
def get_state_districts(state: str = None):
    """Returns districts mapped to dominant soil types and average annual rainfall."""
    try:
        reg = get_district_presets(state=state)
        return StateDistrictResponse(states=reg)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"District presets error: {str(e)}")


# ---------------- Seed Rate & Planting Geometry Calculator ----------------
@app.post("/api/seed-calculator", response_model=SeedRateResponse)
def calculate_seed_rate(req: SeedRateRequest):
    """Calculates precision seed quantity (kg), planting spacing geometry, and plant population."""
    try:
        return calculate_seed_rate_and_population(
            crop_id=req.crop_id,
            land_size_acres=req.land_size_acres,
            row_spacing_cm=req.row_spacing_cm,
            plant_spacing_cm=req.plant_spacing_cm,
            germination_rate_pct=req.germination_rate_pct or 85.0,
            sowing_method=req.sowing_method or "Line Sowing"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Seed calculator error: {str(e)}")


@app.get("/api/seed-calculator/guidelines")
def get_seed_guidelines():
    """Returns reference catalog of standard seed rates and planting geometry."""
    try:
        return get_all_seed_crop_guidelines()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Seed guidelines error: {str(e)}")



