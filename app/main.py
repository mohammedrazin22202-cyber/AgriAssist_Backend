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
    SeedRateResponse,
    SprayerRequest,
    SprayerResponse,
    SolarPumpRequest,
    SolarPumpResponse,
    IntercropPair,
    IntercropResponse,
    StorageRiskCheckRequest,
    StorageRiskCheckResponse,
    GrainStorageAdvisory,
    LivestockRationRequest,
    LivestockRationResponse,
    GestationRequest,
    GestationResponse,
    LivestockRemedy,
    MandiArbitrageRequest,
    MandiArbitrageResponse,
    MicronutrientPrescriptionRequest,
    MicronutrientPrescriptionResponse,
    FarmPondRequest,
    FarmPondResponse,
    MachineryRentVsBuyRequest,
    MachineryRentVsBuyResponse,
    CropCalendarRequest,
    CropCalendarResponse,
    PostHarvestAerationRequest,
    PostHarvestAerationResponse,
    PolyhouseClimateRequest,
    PolyhouseClimateResponse
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
    get_all_seed_crop_guidelines,
    calculate_sprayer_dilution,
    calculate_solar_pump_kusum,
    get_intercropping_recommendations,
    get_grain_storage_catalog_list,
    evaluate_grain_storage_risk,
    calculate_livestock_ration,
    calculate_gestation_calendar,
    get_livestock_evm_remedies,
    calculate_mandi_arbitrage,
    calculate_micronutrient_prescription,
    calculate_farm_pond_sizing,
    calculate_machinery_rent_vs_buy,
    generate_crop_calendar_events,
    calculate_post_harvest_aeration,
    calculate_polyhouse_climate_control
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
@app.post("/api/rotation-planner", response_model=RotationPlanResponse)
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
        part = req.plant_part or req.affected_part
        query = req.search_term or req.symptom_query
        issues = diagnose_plant_issue(
            crop_id=req.crop_id,
            plant_part=part,
            symptoms=req.symptoms,
            search_term=query
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
            prices=prices,
            markets=prices
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Mandi price service error: {str(e)}")


# ---------------- Smart Irrigation & Water Budgeting ----------------
@app.post("/api/irrigation-schedule", response_model=IrrigationScheduleResponse)
def get_irrigation_schedule(req: IrrigationRequest):
    """Computes stage-wise water volume (liters/acre), pump runtimes, and weather postponement."""
    try:
        pump = req.pump_hp if req.pump_hp is not None else (req.pump_capacity_hp if req.pump_capacity_hp is not None else 5.0)
        schedule = calculate_smart_irrigation(
            crop_id=req.crop_id,
            growth_stage=req.growth_stage,
            soil_type=req.soil_type,
            land_size_acres=req.land_size_acres,
            pump_hp=pump,
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


# ---------------- Knapsack Sprayer & Dilution Calculator ----------------
@app.post("/api/sprayer-calculator", response_model=SprayerResponse)
def calculate_sprayer(req: SprayerRequest):
    """Calculates chemical dosage per tank, total tanks required, and safety instructions."""
    try:
        acres = req.land_size_acres if req.land_size_acres is not None else (req.field_acres if req.field_acres is not None else 1.0)
        chem_form = req.chemical_form if req.chemical_form is not None else (req.chemical_formulation if req.chemical_formulation is not None else "Liquid (ml)")
        vol = req.spray_volume_liters_per_acre if req.spray_volume_liters_per_acre is not None else (req.water_volume_liters_per_acre if req.water_volume_liters_per_acre is not None else 150.0)
        return calculate_sprayer_dilution(
            tank_capacity_liters=req.tank_capacity_liters,
            land_size_acres=acres,
            dosage_mode=req.dosage_mode,
            dosage_amount=req.dosage_amount,
            chemical_form=chem_form,
            spray_volume_liters_per_acre=vol
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Sprayer calculator error: {str(e)}")


# ---------------- Solar Ag-Pump & PM-KUSUM Sizing Calculator ----------------
@app.post("/api/solar-pump-calculator", response_model=SolarPumpResponse)
def calculate_solar_pump(req: SolarPumpRequest):
    """Computes recommended solar pump HP, solar PV array, PM-KUSUM subsidy, and diesel savings."""
    try:
        acres = req.land_size_acres if req.land_size_acres is not None else (req.command_area_acres if req.command_area_acres is not None else 2.0)
        irrig = req.irrigation_type if req.irrigation_type is not None else (req.irrigation_method if req.irrigation_method is not None else "Drip / Sprinkler")
        return calculate_solar_pump_kusum(
            water_source=req.water_source,
            water_depth_feet=req.water_depth_feet,
            land_size_acres=acres,
            irrigation_type=irrig,
            farmer_category=req.farmer_category,
            state=req.state or "All-India"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Solar pump calculator error: {str(e)}")


# ---------------- Intercropping & Companion Crop Matrix ----------------
@app.get("/api/intercropping", response_model=IntercropResponse)
def get_intercropping_pairs(crop_id: str = None, main_crop: str = None):
    """Returns synergistic intercropping combinations, row ratios, and LER advantages."""
    try:
        target = crop_id or main_crop
        pairs = get_intercropping_recommendations(crop_id=target)
        return IntercropResponse(total_pairs=len(pairs), pairs=pairs)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Intercropping error: {str(e)}")


# ---------------- Post-Harvest Grain Storage & Moisture Doctor ----------------
@app.get("/api/grain-storage/advisory", response_model=List[GrainStorageAdvisory])
def get_grain_storage_advisories():
    """Returns safe moisture thresholds and non-chemical storage guidelines for major crops."""
    try:
        return get_grain_storage_catalog_list()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Grain storage catalog error: {str(e)}")


@app.post("/api/grain-storage/check-risk", response_model=StorageRiskCheckResponse)
def check_grain_storage_risk(req: StorageRiskCheckRequest):
    """Evaluates grain moisture, assigns spoilage risk tier, and prescribes sun-drying hours."""
    try:
        cid = req.crop_id or req.crop_name or "wheat"
        moist = req.measured_moisture_pct if req.measured_moisture_pct is not None else (req.current_moisture_pct if req.current_moisture_pct is not None else 12.0)
        dur = req.intended_duration_months if req.intended_duration_months is not None else (req.planned_duration_months if req.planned_duration_months is not None else 6)
        return evaluate_grain_storage_risk(
            crop_id=cid,
            measured_moisture_pct=moist,
            storage_method=req.storage_method or "Jute Gunny Bags",
            intended_duration_months=dur
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Grain storage risk error: {str(e)}")


# ---------------- 1. Dairy & Livestock Advisory Endpoints ----------------
@app.post("/api/livestock/ration", response_model=LivestockRationResponse)
def calculate_cattle_ration(req: LivestockRationRequest):
    """Calculates scientific dry matter, green fodder, bhusa, and concentrate feed ration."""
    try:
        return calculate_livestock_ration(
            animal_type=req.animal_type,
            body_weight_kg=req.body_weight_kg,
            daily_milk_liters=req.daily_milk_liters,
            milk_fat_pct=req.milk_fat_pct or 4.0,
            pregnancy_stage=req.pregnancy_stage or "None"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Livestock ration error: {str(e)}")


@app.post("/api/livestock/gestation", response_model=GestationResponse)
def get_gestation_schedule(req: GestationRequest):
    """Computes 21-day heat check, drying-off, and calving delivery milestones."""
    try:
        return calculate_gestation_calendar(
            animal_type=req.animal_type,
            insemination_date=req.insemination_date
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gestation calendar error: {str(e)}")


@app.get("/api/livestock/remedies", response_model=List[LivestockRemedy])
def list_livestock_remedies():
    """Returns validated Ethno-Veterinary Medicine (EVM) herbal formulations for common ailments."""
    try:
        return get_livestock_evm_remedies()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Livestock remedies error: {str(e)}")


# ---------------- 2. Mandi Distance & Profit Arbitrage ----------------
@app.post("/api/mandi-prices/arbitrage", response_model=MandiArbitrageResponse)
def check_mandi_arbitrage(req: MandiArbitrageRequest):
    """Calculates diesel consumption, transport cost, and true net profit between local vs distant mandis."""
    try:
        return calculate_mandi_arbitrage(
            crop_id=req.crop_id,
            quantity_quintals=req.quantity_quintals,
            local_mandi_name=req.local_mandi_name,
            local_mandi_price=req.local_mandi_price,
            local_mandi_distance_km=req.local_mandi_distance_km,
            distant_mandi_name=req.distant_mandi_name,
            distant_mandi_price=req.distant_mandi_price,
            distant_mandi_distance_km=req.distant_mandi_distance_km,
            vehicle_type=req.vehicle_type,
            diesel_price_per_liter=req.diesel_price_per_liter
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Mandi arbitrage error: {str(e)}")


# ---------------- 3. Soil Health Card Micronutrient Doctor ----------------
@app.post("/api/fertilizer/micronutrients", response_model=MicronutrientPrescriptionResponse)
def get_micronutrient_prescription(req: MicronutrientPrescriptionRequest):
    """Prescribes Zinc Sulfate, Bentonite Sulfur, Borax, and Iron amendments for micronutrient deficits."""
    try:
        return calculate_micronutrient_prescription(
            crop_id=req.crop_id,
            land_size_acres=req.land_size_acres,
            zinc_ppm=req.zinc_ppm,
            iron_ppm=req.iron_ppm,
            sulfur_ppm=req.sulfur_ppm,
            boron_ppm=req.boron_ppm,
            organic_carbon_pct=req.organic_carbon_pct
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Micronutrient prescription error: {str(e)}")


# ---------------- 4. Farm Pond & Rainwater Harvesting Sizer ----------------
@app.post("/api/water-conservation/farm-pond", response_model=FarmPondResponse)
def get_farm_pond_sizing(req: FarmPondRequest):
    """Calculates required farm pond dimensions, HDPE lining area, and PMKSY subsidy."""
    try:
        return calculate_farm_pond_sizing(
            catchment_acres=req.catchment_acres,
            annual_rainfall_mm=req.annual_rainfall_mm,
            catchment_soil_type=req.catchment_soil_type,
            supplementary_irrigation_acres=req.supplementary_irrigation_acres,
            dry_spell_days_target=req.dry_spell_days_target
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Farm pond sizing error: {str(e)}")


# ---------------- 5. Machinery Rent vs Buy Calculator ----------------
@app.post("/api/machinery/rent-vs-buy", response_model=MachineryRentVsBuyResponse)
def check_machinery_rent_vs_buy(req: MachineryRentVsBuyRequest):
    """Compares machinery ownership cost (fixed depreciation + fuel) vs custom hiring break-even."""
    try:
        return calculate_machinery_rent_vs_buy(
            machine_type=req.machine_type,
            farm_size_acres=req.farm_size_acres,
            purchase_price_inr=req.purchase_price_inr,
            custom_hire_rate_per_acre_or_hr=req.custom_hire_rate_per_acre_or_hr,
            commercial_rental_acres_to_others=req.commercial_rental_acres_to_others or 0.0
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Machinery economics error: {str(e)}")


# ---------------- 6. Dynamic Crop Calendar & ICS Generator ----------------
@app.post("/api/crop-calendar/generate", response_model=CropCalendarResponse)
def get_crop_calendar(req: CropCalendarRequest):
    """Generates milestone timeline and RFC 5545 iCalendar (.ics) string for phone calendar import."""
    try:
        return generate_crop_calendar_events(
            crop_id=req.crop_id,
            sowing_date=req.sowing_date,
            land_size_acres=req.land_size_acres or 1.0
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Crop calendar error: {str(e)}")


# ---------------- 7. Post-Harvest Grain Aeration & Storage Sizer ----------------
@app.post("/api/post-harvest-aeration", response_model=PostHarvestAerationResponse)
def get_post_harvest_aeration(req: PostHarvestAerationRequest):
    """Calculates water removal requirement, silo aeration airflow (CFM), motor HP,
    and mold-free storage shelf-life.
    """
    try:
        return calculate_post_harvest_aeration(
            grain_type=req.grain_type,
            quantity_quintals=req.quantity_quintals,
            initial_moisture_pct=req.initial_moisture_pct,
            target_moisture_pct=req.target_moisture_pct,
            ambient_temp_c=req.ambient_temp_c,
            ambient_rh_pct=req.ambient_rh_pct,
            storage_type=req.storage_type
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Post-harvest aeration calculation error: {str(e)}")


# ---------------- 8. Polyhouse & Greenhouse Climate Sizer ----------------
@app.post("/api/polyhouse-climate", response_model=PolyhouseClimateResponse)
def get_polyhouse_climate(req: PolyhouseClimateRequest):
    """Calculates ventilation fan capacity, evaporative cooling pad dimensions,
    Vapor Pressure Deficit (VPD in kPa), thermal drop, and MIDH government subsidy.
    """
    try:
        return calculate_polyhouse_climate_control(
            structure_type=req.structure_type,
            covered_area_sqm=req.covered_area_sqm,
            crop_type=req.crop_type,
            ambient_max_temp_c=req.ambient_max_temp_c,
            ambient_min_rh_pct=req.ambient_min_rh_pct,
            roof_height_meters=req.roof_height_meters
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Polyhouse climate calculation error: {str(e)}")








