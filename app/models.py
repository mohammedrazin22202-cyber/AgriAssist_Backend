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
    affected_part: Optional[str] = None  # Frontend compatibility alias
    symptoms: Optional[List[str]] = None
    search_term: Optional[str] = None
    symptom_query: Optional[str] = None  # Frontend compatibility alias


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
    markets: Optional[List[MandiPriceItem]] = None  # Frontend compatibility alias


# ---------------- Smart Irrigation Models ----------------
class IrrigationRequest(BaseModel):
    crop_id: str
    growth_stage: str
    soil_type: str = "Alluvial Soil"
    land_size_acres: float = 1.0
    pump_hp: Optional[float] = 5.0
    pump_capacity_hp: Optional[float] = None  # Frontend compatibility alias
    forecast_rain_mm: Optional[float] = 0.0


class IrrigationScheduleResponse(BaseModel):
    crop_name: str
    growth_stage: str
    soil_type: str
    land_size_acres: float
    water_depth_mm: float
    water_volume_liters: float
    total_water_volume_liters: Optional[float] = None  # Frontend compatibility
    water_volume_acre_inches: float
    pump_runtime_hours: float
    pump_run_hours: Optional[float] = None  # Frontend compatibility
    irrigation_interval_days: int
    interval_days: Optional[str] = None  # Frontend compatibility
    total_irrigations_needed: int
    rain_warning: bool
    postpone_irrigation_alert: Optional[str] = None  # Frontend compatibility
    advisory_notes: str
    critical_stages: List[str]
    water_saving_tips: Optional[List[str]] = None  # Frontend compatibility
    weather_rain_forecast_mm: Optional[float] = None


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
    jeevamrutha_liters: Optional[float] = None  # Frontend compatibility
    beejamrit_kg: float
    beejamrit_liters: Optional[float] = None  # Frontend compatibility
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


class PmfbyDetail(BaseModel):
    season_category: str
    sum_insured_inr: float
    farmer_premium_rate_percent: float
    farmer_share_premium_inr: float
    govt_subsidy_share_inr: float
    official_portal: str = "https://pmfby.gov.in"


class KccDetail(BaseModel):
    scale_of_finance_per_acre_inr: float
    recommended_credit_limit_inr: float
    interest_rate_percent: float = 7.0
    prompt_repayment_incentive_percent: float = 3.0
    effective_interest_rate_percent: float = 4.0
    official_portal: str = "https://myscheme.gov.in"


class PmksyDripDetail(BaseModel):
    farmer_category: str
    subsidy_percentage: float
    approx_equipment_cost_inr: float
    eligible_subsidy_inr: float
    farmer_payable_inr: float


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
    pm_kisan_annual_cash_inr: Optional[float] = 6000.0  # Frontend compatibility
    pmfby: Optional[PmfbyDetail] = None  # Frontend structured support
    kcc: Optional[KccDetail] = None  # Frontend structured support
    pmksy_drip: Optional[PmksyDripDetail] = None  # Frontend structured support
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


# ---------------- Knapsack Sprayer & Dilution Models ----------------
class SprayerRequest(BaseModel):
    tank_capacity_liters: float = 16.0
    land_size_acres: Optional[float] = None
    field_acres: Optional[float] = None  # Frontend compatibility alias
    dosage_mode: str = "per_liter"  # "per_liter" or "per_acre"
    dosage_amount: float = 2.0  # ml or grams
    chemical_form: Optional[str] = None  # "Liquid (ml)" or "Powder (g)"
    chemical_formulation: Optional[str] = None  # Frontend compatibility alias
    spray_volume_liters_per_acre: Optional[float] = None
    water_volume_liters_per_acre: Optional[float] = None  # Frontend compatibility alias


class SprayerResponse(BaseModel):
    tank_capacity_liters: float
    land_size_acres: float
    chemical_per_tank: float
    chemical_unit: str
    tanks_needed_total: float
    total_spray_tanks: Optional[float] = None  # Frontend compatibility alias
    total_water_liters: float
    total_chemical_needed: float
    total_chemical_required: Optional[float] = None  # Frontend compatibility alias
    total_chemical_unit: Optional[str] = None  # Frontend compatibility alias
    nozzle_recommendation: str
    safety_checklist: List[str]
    application_tips: List[str]
    recommendations: Optional[List[str]] = None  # Frontend compatibility alias


# ---------------- Solar Ag-Pump & PM-KUSUM Models ----------------
class SolarPumpRequest(BaseModel):
    water_source: str = "Borewell"  # "Borewell", "Open Well", "Canal / Surface"
    water_depth_feet: float = 150.0
    land_size_acres: Optional[float] = None
    command_area_acres: Optional[float] = None  # Frontend compatibility alias
    irrigation_type: Optional[str] = None  # "Flood", "Drip / Sprinkler"
    irrigation_method: Optional[str] = None  # Frontend compatibility alias
    farmer_category: str = "Small / Marginal (< 2 Ha)"
    state: Optional[str] = "All-India"


class SolarPumpResponse(BaseModel):
    water_source: str
    water_depth_feet: float
    land_size_acres: float
    recommended_pump_hp: float
    recommended_solar_array_kw: float
    solar_array_kwp: Optional[float] = None  # Frontend compatibility alias
    pump_type: str
    total_dynamic_head_meters: Optional[float] = None  # Frontend compatibility alias
    total_estimated_cost_inr: float
    estimated_total_cost: Optional[float] = None  # Frontend compatibility alias
    central_subsidy_inr: float
    central_subsidy: Optional[float] = None  # Frontend compatibility alias
    state_subsidy_inr: float
    state_subsidy: Optional[float] = None  # Frontend compatibility alias
    farmer_share_inr: float
    farmer_share: Optional[float] = None  # Frontend compatibility alias
    bank_loan_available: Optional[float] = None  # Frontend compatibility alias
    subsidy_percentage_total: float
    annual_diesel_savings_inr: float
    annual_diesel_cost_savings_rs: Optional[float] = None  # Frontend compatibility alias
    annual_diesel_saved_liters: Optional[float] = None  # Frontend compatibility alias
    co2_reduction_tons_per_year: Optional[float] = None  # Frontend compatibility alias
    payback_period_years: float
    advisory_notes: str
    pm_kusum_portal: str = "https://pmkusum.mnre.gov.in"


# ---------------- Intercropping & Companion Models ----------------
class IntercropPair(BaseModel):
    id: str
    main_crop_id: str
    main_crop_name: str
    main_crop: Optional[str] = None  # Frontend compatibility alias
    companion_crop_id: str
    companion_crop_name: str
    companion_crop: Optional[str] = None  # Frontend compatibility alias
    row_ratio: str
    spatial_ratio: Optional[str] = None  # Frontend compatibility alias
    synergy_type: str
    land_equivalent_ratio: float
    ler: Optional[float] = None  # Frontend compatibility alias
    nitrogen_fixation_kg_acre: float
    weed_suppression_pct: float
    pest_repellent_benefit: str
    economic_advisory: str
    biological_benefit: Optional[str] = None  # Frontend compatibility alias
    recommended_season: Optional[str] = None  # Frontend compatibility alias
    water_compatibility: Optional[str] = None  # Frontend compatibility alias


class IntercropResponse(BaseModel):
    total_pairs: int
    pairs: List[IntercropPair]


# ---------------- Post-Harvest Storage & Moisture Models ----------------
class StorageRiskCheckRequest(BaseModel):
    crop_id: Optional[str] = None
    crop_name: Optional[str] = None  # Frontend compatibility alias
    measured_moisture_pct: Optional[float] = None
    current_moisture_pct: Optional[float] = None  # Frontend compatibility alias
    storage_method: str = "Jute Gunny Bags"  # "Jute Gunny Bags", "HDPE Bags", "Metal Bins", "Mud Kothi"
    intended_duration_months: Optional[int] = None
    planned_duration_months: Optional[int] = None  # Frontend compatibility alias


class StorageRiskCheckResponse(BaseModel):
    crop_id: str
    crop_name: str
    measured_moisture_pct: float
    current_moisture_pct: Optional[float] = None  # Frontend compatibility alias
    safe_moisture_limit_pct: float
    safe_moisture_pct: Optional[float] = None  # Frontend compatibility alias
    risk_level: str  # "Safe / Green", "Moderate Risk / Yellow", "Critical Spoilage / Red"
    risk_explanation: str
    sun_drying_hours_needed: float
    traditional_preservation_tips: List[str]
    enwr_warehouse_pledge_benefit: str
    spoilage_warnings: Optional[List[str]] = None  # Frontend compatibility alias
    drying_action_plan: Optional[List[str]] = None  # Frontend compatibility alias


class GrainStorageAdvisory(BaseModel):
    crop_id: str
    crop_name: str
    crop: Optional[str] = None  # Frontend compatibility alias
    safe_moisture_limit_pct: float
    safe_moisture_pct: Optional[float] = None  # Frontend compatibility alias
    max_shelf_life_months: int
    max_safe_duration_months: Optional[int] = None  # Frontend compatibility alias
    common_storage_pests: List[str]
    major_pests: Optional[str] = None  # Frontend compatibility alias
    natural_protectants: List[str]
    safe_practices: Optional[str] = None  # Frontend compatibility alias
    stacking_and_storage_guidelines: str


# =======================================================================
# 1. Livestock & Dairy Advisory Models
# =======================================================================
class LivestockRationRequest(BaseModel):
    animal_type: str = "Cow (Crossbred HF/Jersey)"  # "Cow (Indigenous/Desi)", "Cow (Crossbred HF/Jersey)", "Buffalo (Murrah)", "Goat"
    body_weight_kg: float = 400.0
    daily_milk_liters: float = 10.0
    milk_fat_pct: Optional[float] = 4.0
    pregnancy_stage: Optional[str] = "None"  # "None", "Early/Mid", "Last Trimester (Advance Pregnant)"


class LivestockRationResponse(BaseModel):
    animal_type: str
    body_weight_kg: float
    daily_milk_liters: float
    dry_matter_requirement_kg: float
    green_fodder_kg: float
    dry_straw_bhusa_kg: float
    concentrate_feed_kg: float
    mineral_mixture_grams: float
    salt_grams: float
    water_requirement_liters: float
    estimated_daily_feed_cost_inr: float
    feeding_tips: List[str]


class GestationRequest(BaseModel):
    animal_type: str = "Cow"  # "Cow", "Buffalo", "Goat"
    insemination_date: str  # "YYYY-MM-DD"


class GestationMilestone(BaseModel):
    days_after_insemination: int
    milestone_date: str
    title: str
    action_notes: str


class GestationResponse(BaseModel):
    animal_type: str
    insemination_date: str
    gestation_period_days: int
    heat_check_date_21d: str
    pregnancy_diagnosis_date_60d: str
    dry_off_date: str
    expected_calving_date: str
    milestones: List[GestationMilestone]
    advisory_notes: str


class LivestockRemedy(BaseModel):
    id: str
    condition: str
    symptoms: List[str]
    evm_formulation_name: str
    ingredients: List[str]
    preparation_method: str
    dosage_and_application: str
    prevention_guidelines: str


# =======================================================================
# 2. Mandi Distance & Profit Arbitrage Models
# =======================================================================
class MandiArbitrageRequest(BaseModel):
    crop_id: str = "wheat"
    quantity_quintals: float = 30.0
    local_mandi_name: str = "Local Mandi"
    local_mandi_price: float = 2200.0
    local_mandi_distance_km: float = 10.0
    distant_mandi_name: str = "Terminal District Mandi"
    distant_mandi_price: float = 2400.0
    distant_mandi_distance_km: float = 50.0
    vehicle_type: str = "Tractor Trolley"  # "Tractor Trolley", "Pickup Truck (Bolero/Ace)", "3-Wheeler Loader", "Large 6-Wheeler Truck"
    diesel_price_per_liter: float = 90.0


class MandiArbitrageResponse(BaseModel):
    crop_id: str
    quantity_quintals: float
    local_gross_revenue: float
    local_transport_cost: float
    local_net_revenue: float
    distant_gross_revenue: float
    distant_transport_cost: float
    distant_net_revenue: float
    net_profit_difference: float
    is_distant_mandi_worth_it: bool
    break_even_price_per_quintal: float
    recommendation: str
    round_trip_km_distant: float
    fuel_liters_consumed_distant: float


# =======================================================================
# 3. Soil Health Card Micronutrient Doctor Models
# =======================================================================
class MicronutrientPrescriptionRequest(BaseModel):
    crop_id: Optional[str] = "wheat"
    land_size_acres: float = 1.0
    zinc_ppm: Optional[float] = None
    iron_ppm: Optional[float] = None
    sulfur_ppm: Optional[float] = None
    boron_ppm: Optional[float] = None
    organic_carbon_pct: Optional[float] = None


class MicronutrientItem(BaseModel):
    nutrient: str
    soil_status: str  # "Critical Deficient", "Low / Deficient", "Optimal / Sufficient"
    measured_value: Optional[float] = None
    critical_threshold: str
    recommended_fertilizer: str
    dosage_kg_per_acre: float
    total_dosage_kg: float
    application_method: str
    visual_deficiency_symptom: str


class MicronutrientPrescriptionResponse(BaseModel):
    land_size_acres: float
    crop_id: str
    prescriptions: List[MicronutrientItem]
    organic_manure_advice: str
    foliar_spray_options: List[str]
    approx_total_cost_inr: float


# =======================================================================
# 4. Farm Pond & Rainwater Harvesting Sizer Models
# =======================================================================
class FarmPondRequest(BaseModel):
    catchment_acres: float = 5.0
    annual_rainfall_mm: float = 800.0
    catchment_soil_type: str = "Loam"  # "Clay", "Loam", "Sandy"
    supplementary_irrigation_acres: float = 2.0
    dry_spell_days_target: int = 30


class FarmPondResponse(BaseModel):
    catchment_acres: float
    annual_rainfall_mm: float
    runoff_volume_cu_meters: float
    storage_capacity_liters: float
    storage_capacity_lakh_liters: float
    recommended_top_length_m: float
    recommended_top_width_m: float
    recommended_bottom_length_m: float
    recommended_bottom_width_m: float
    recommended_depth_m: float
    side_slope_ratio: str
    geomembrane_lining_area_sqm: float
    estimated_earthwork_cost_inr: float
    estimated_hdpe_lining_cost_inr: float
    estimated_total_cost_inr: float
    pmksy_khet_talab_subsidy_inr: float
    net_farmer_cost_inr: float
    water_security_advisory: str


# =======================================================================
# 5. Machinery Rent vs Buy Models
# =======================================================================
class MachineryRentVsBuyRequest(BaseModel):
    machine_type: str = "Tractor 45-50 HP"  # "Tractor 45-50 HP", "Rotavator (6 ft)", "Seed Cum Fert Drill", "Laser Land Leveller", "Combine Harvester"
    farm_size_acres: float = 8.0
    purchase_price_inr: Optional[float] = None
    custom_hire_rate_per_acre_or_hr: Optional[float] = None
    commercial_rental_acres_to_others: Optional[float] = 0.0


class MachineryRentVsBuyResponse(BaseModel):
    machine_type: str
    farm_size_acres: float
    commercial_rental_acres_to_others: float
    total_operated_acres: float
    annual_hiring_cost_inr: float
    annual_ownership_cost_inr: float
    annual_diesel_burn_liters: float
    annual_fuel_cost_inr: float
    break_even_acres: float
    commercial_rental_income_inr: float
    net_annual_saving_or_loss_inr: float
    recommendation: str
    payback_period_years: float
    key_decision_factors: List[str]


# =======================================================================
# 6. Dynamic Crop Calendar & ICS Models
# =======================================================================
class CropCalendarRequest(BaseModel):
    crop_id: str = "wheat"
    sowing_date: str = "2026-11-15"  # YYYY-MM-DD
    land_size_acres: Optional[float] = 1.0


class CropCalendarEvent(BaseModel):
    day_offset: int
    target_date: str
    phase_name: str
    activity_type: str  # "Sowing", "Irrigation", "Nutrient", "Weeding", "Pest Management", "Harvesting"
    action_required: str
    critical_alert: Optional[str] = None
    weather_sensitivity: str


class CropCalendarResponse(BaseModel):
    crop_id: str
    crop_name: str
    sowing_date: str
    harvest_date: str
    total_duration_days: int
    events: List[CropCalendarEvent]
    ics_calendar_text: str


# =======================================================================
# 7. Post-Harvest Grain Aeration & Moisture Drying Models
# =======================================================================
class PostHarvestAerationRequest(BaseModel):
    grain_type: str = "Paddy (Rice)"
    quantity_quintals: float = 100.0
    initial_moisture_pct: float = 19.5
    target_moisture_pct: Optional[float] = 12.0
    ambient_temp_c: Optional[float] = 28.0
    ambient_rh_pct: Optional[float] = 65.0
    storage_type: Optional[str] = "Bagged in Warehouse"


class PostHarvestAerationResponse(BaseModel):
    grain_type: str
    quantity_quintals: float
    initial_moisture_pct: float
    target_moisture_pct: float
    moisture_to_remove_kg: float
    final_quantity_quintals: float
    equilibrium_moisture_content_pct: float
    aeration_fan_airflow_cfm: float
    fan_power_hp_estimate: float
    estimated_drying_hours_sun: float
    estimated_drying_hours_forced_air: float
    safe_storage_duration_days: int
    storage_risk_level: str
    aflatoxin_mold_warning: str
    recommended_protocols: List[str]






