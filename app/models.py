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
