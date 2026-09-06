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
