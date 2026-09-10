from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any


class RecommendationRequest(BaseModel):
    mode: str = Field(default="simple", description="'simple' or 'advanced'")
    soil_type: str = Field(..., description="Soil type name e.g. 'Alluvial', 'Black', 'Red', 'Sandy Loam', 'Clay'")
    season: str = Field(..., description="Agricultural season e.g. 'Kharif', 'Rabi', 'Zaid', 'Year-round'")
    water_availability: str = Field(..., description="Water availability e.g. 'Low (Rainfed)', 'Moderate', 'High (Assured)'")
    land_size_acres: Optional[float] = Field(default=1.0, description="Farm land size in acres")
    land_type: Optional[str] = Field(default="Plain", description="Topography: 'Plain', 'Slope / Hill', 'Lowland'")
    budget_preference: Optional[str] = Field(default="Balanced", description="'Low Cost', 'Balanced', 'Commercial / High Value'")
    
    # Advanced soil lab & weather parameters (optional, defaults derived from soil presets)
    nitrogen: Optional[float] = Field(default=None, description="Available Nitrogen in kg/ha")
    phosphorus: Optional[float] = Field(default=None, description="Available Phosphorus in kg/ha")
    potassium: Optional[float] = Field(default=None, description="Available Potassium in kg/ha")
    ph: Optional[float] = Field(default=None, description="Soil pH (0-14)")
    rainfall_mm: Optional[float] = Field(default=None, description="Expected seasonal rainfall in mm")
    temperature_c: Optional[float] = Field(default=None, description="Average temperature in Celsius")
    humidity_pct: Optional[float] = Field(default=None, description="Average relative humidity %")


class FertilizerScheduleItem(BaseModel):
    stage: str
    advice: str


class FertilizerPrescription(BaseModel):
    urea_kg: float
    urea_bags_50kg: float
    dap_kg: float
    dap_bags_50kg: float
    mop_kg: float
    mop_bags_50kg: float
    approx_fertilizer_cost_inr: float
    application_schedule: List[FertilizerScheduleItem]
    amendment_type: str
    lime_kg: float
    gypsum_kg: float
    amendment_advice: str


class FinancialSummary(BaseModel):
    land_size_acres: float
    msp_or_market_price_per_quintal: float
    avg_yield_per_acre_quintal: float
    total_estimated_yield_quintals: float
    seed_cost_inr: float
    fertilizer_cost_inr: float
    operations_and_labor_cost_inr: float
    total_investment_cost_inr: float
    gross_revenue_inr: float
    net_profit_inr: float
    roi_percentage: float
    profit_per_acre_inr: float


class GrowthStage(BaseModel):
    day_range: str
    stage_name: str
    activities: str
    pest_warning: Optional[str] = None


class CropRecommendation(BaseModel):
    crop_id: str
    name: str
    hindi_name: Optional[str] = None
    scientific_name: str
    category: str  # Cereal, Pulse, Oilseed, Cash Crop, Fiber, Vegetable, Spices
    suitability_score: float  # 0 to 100
    suitability_level: str  # Highly Recommended, Recommended, Moderately Suitable, Marginal
    sowing_window: str
    duration_days: str
    water_requirement: str  # Low, Medium, High
    estimated_yield_per_acre: str
    investment_level: str  # Low, Moderate, High
    profit_potential: str  # Moderate, High, Very High
    reasons: List[str]
    warnings: List[str]
    sowing_tips: str
    fertilizer_advice: str
    soil_notes: str
    companion_crops: Optional[List[str]] = None
    financials: Optional[FinancialSummary] = None
    fertilizer_prescription: Optional[FertilizerPrescription] = None
    growth_stages: Optional[List[GrowthStage]] = None


class RecommendationResponse(BaseModel):
    total_crops_evaluated: int
    recommendations: List[CropRecommendation]
    top_pick: Optional[CropRecommendation] = None
    soil_summary: Dict[str, Any]
    applied_parameters: Dict[str, Any]


class SoilPreset(BaseModel):
    name: str
    description: str
    default_n: float
    default_p: float
    default_k: float
    default_ph: float
    drainage: str
    organic_matter: str
    suitable_crops_sample: List[str]


# ---------------- Rotation Models ----------------
class RotationSeasonCrop(BaseModel):
    season: str
    crop_id: str
    crop_name: str
    role: str
    duration: str
    water: str
    net_profit_per_acre: float


class AnnualRotationPlan(BaseModel):
    plan_id: str
    title: str
    badge: str
    description: str
    soil_health_index: int
    nitrogen_fixation_benefit: str
    pest_break_benefit: str
    crops: List[RotationSeasonCrop]
    total_annual_net_profit_inr: float
    annual_net_profit_per_acre_inr: float


class RotationPlanRequest(BaseModel):
    soil_type: str = Field(default="Alluvial Soil", description="Soil type name")
    water_availability: str = Field(default="Moderate (Canal / Tube-well / Seasonal)", description="Water availability")
    budget_preference: Optional[str] = Field(default="Balanced")
    land_size_acres: Optional[float] = Field(default=1.0)


class RotationPlanResponse(BaseModel):
    soil_type: str
    water_availability: str
    land_size_acres: float
    plans: List[AnnualRotationPlan]


class StandaloneFertilizerRequest(BaseModel):
    crop_id: Optional[str] = None
    ideal_n: Optional[float] = None
    ideal_p: Optional[float] = None
    ideal_k: Optional[float] = None
    soil_n: float = 140.0
    soil_p: float = 30.0
    soil_k: float = 180.0
    soil_ph: Optional[float] = 7.0
    land_size_acres: Optional[float] = 1.0


# ---------------- Plant Doctor Models ----------------
class PestDiseaseItem(BaseModel):
    id: str
    crop_id: str
    crop_name: str
    name: str
    hindi_name: Optional[str] = None
    type: str  # Pest, Fungal, Bacterial, Viral, Nutrient Deficiency
    affected_parts: List[str]  # Leaf, Stem, Root, Fruit/Grain, Whole Plant
    symptoms: List[str]
    severity: str  # Low, Moderate, High, Critical
    biological_control: List[str]
    chemical_control: List[str]
    chemical_dosage: str
    pre_harvest_interval_days: int
    prevention_tips: List[str]


class PlantDoctorRequest(BaseModel):
    crop_id: Optional[str] = None
    plant_part: Optional[str] = None
    symptoms: Optional[List[str]] = None
    search_term: Optional[str] = None


class PlantDoctorResponse(BaseModel):
    total_matches: int
    issues: List[PestDiseaseItem]


# ---------------- Mandi Price Models ----------------
class MandiPriceTrendPoint(BaseModel):
    date: str
    modal_price: float


class MandiPriceItem(BaseModel):
    crop_id: str
    crop_name: str
    commodity: str
    state: str
    district: str
    market_apmc: str
    modal_price_per_quintal: float
    min_price: float
    max_price: float
    msp_price: float
    price_vs_msp_diff: float
    trend: str  # Bullish / Rising, Bearish / Dropping, Stable
    selling_advice: str
    historical_30d: List[MandiPriceTrendPoint]


class MandiPriceResponse(BaseModel):
    total_mandis: int
    state: Optional[str] = None
    district: Optional[str] = None
    prices: List[MandiPriceItem]


# ---------------- Smart Irrigation Models ----------------
class IrrigationRequest(BaseModel):
    crop_id: str
    growth_stage: str
    soil_type: str = "Alluvial Soil"
    land_size_acres: float = 1.0
    pump_hp: float = 5.0
    forecast_rain_mm: Optional[float] = 0.0


class IrrigationScheduleResponse(BaseModel):
    crop_name: str
    growth_stage: str
    soil_type: str
    land_size_acres: float
    water_depth_mm: float
    water_volume_liters: float
    water_volume_acre_inches: float
    pump_runtime_hours: float
    irrigation_interval_days: int
    total_irrigations_needed: int
    rain_warning: bool
    advisory_notes: str
    critical_stages: List[str]


# ---------------- Organic & Natural Farming Models ----------------
class OrganicRecipe(BaseModel):
    id: str
    name: str
    hindi_name: str
    purpose: str
    ingredients: List[str]
    preparation_steps: List[str]
    application_method: str
    application_timing: str
    dosage_per_acre: str


class OrganicPrescriptionRequest(BaseModel):
    crop_id: str
    land_size_acres: float = 1.0


class OrganicPrescriptionResponse(BaseModel):
    crop_id: str
    crop_name: str
    land_size_acres: float
    total_jeevamrutha_liters: float
    beejamrit_kg: float
    ghanjeevamrit_kg: float
    vermicompost_tons: float
    neemastra_liters: float
    biofertilizers: List[str]
    recipes: List[OrganicRecipe]


# ---------------- Government Schemes & Subsidies Models ----------------
class SchemeDetail(BaseModel):
    scheme_id: str
    name: str
    category: str
    eligibility: str
    benefits: str
    calculated_benefit_inr: float
    action_link: str


class GovtSchemesRequest(BaseModel):
    crop_id: str = "wheat"
    land_size_acres: float = 1.0
    farmer_category: str = "Small / Marginal (< 2 Ha)"
    state: Optional[str] = "All-India"


class GovtSchemesResponse(BaseModel):
    farmer_category: str
    land_size_acres: float
    crop_name: str
    sum_insured_inr: float
    farmer_pmfby_premium_inr: float
    govt_pmfby_subsidy_inr: float
    kcc_crop_loan_limit_inr: float
    drip_subsidy_pct: float
    drip_subsidy_amount_inr: float
    pm_kisan_annual_inr: float
    schemes: List[SchemeDetail]


# ---------------- State & District Presets Models ----------------
class DistrictPreset(BaseModel):
    district: str
    state: str
    soil_type: str
    annual_rainfall_mm: float
    avg_temp_c: float
    priority_crops: List[str]


class StateDistrictResponse(BaseModel):
    states: Dict[str, List[DistrictPreset]]


# ---------------- Seed Rate & Planting Geometry Models ----------------
class SeedRateRequest(BaseModel):
    crop_id: str
    land_size_acres: float = 1.0
    row_spacing_cm: Optional[float] = None
    plant_spacing_cm: Optional[float] = None
    germination_rate_pct: Optional[float] = 85.0
    sowing_method: Optional[str] = "Line Sowing"


class SeedRateResponse(BaseModel):
    crop_id: str
    crop_name: str
    land_size_acres: float
    recommended_seed_rate_kg_per_acre: float
    total_seed_required_kg: float
    standard_row_spacing_cm: float
    standard_plant_spacing_cm: float
    effective_row_spacing_cm: float
    effective_plant_spacing_cm: float
    estimated_plant_population: int
    population_per_acre: int
    sowing_depth_cm: str
    sowing_method: str
    seed_treatment_protocol: str
    certified_seed_rate_per_kg_inr: float
    estimated_seed_cost_inr: float
    agronomic_advisory: str


