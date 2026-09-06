"""Core agronomic scoring and recommendation engine for AgriAssist.
Evaluates soil compatibility, seasonal alignment, water security, and economic factors.
"""

from typing import List, Dict, Any, Tuple
from app.models import RecommendationRequest, CropRecommendation, RecommendationResponse
from app.soil_presets import SOIL_PRESETS, SEASON_METADATA
from app.database import get_all_crops


def resolve_parameters(req: RecommendationRequest) -> Dict[str, Any]:
    """Resolves input parameters, falling back to soil and season presets if missing."""
    preset = SOIL_PRESETS.get(req.soil_type, SOIL_PRESETS["Alluvial Soil"])
    season_info = SEASON_METADATA.get(req.season, SEASON_METADATA["Kharif"])

    n = req.nitrogen if req.nitrogen is not None else preset["default_n"]
    p = req.phosphorus if req.phosphorus is not None else preset["default_p"]
    k = req.potassium if req.potassium is not None else preset["default_k"]
    ph = req.ph if req.ph is not None else preset["default_ph"]
    rainfall = req.rainfall_mm if req.rainfall_mm is not None else season_info["typical_rainfall_mm"]
    temp = req.temperature_c if req.temperature_c is not None else season_info["typical_temp_c"]

    return {
        "soil_type": req.soil_type,
        "season": req.season,
        "water_availability": req.water_availability,
        "land_size_acres": req.land_size_acres or 1.0,
        "land_type": req.land_type or "Plain",
        "budget_preference": req.budget_preference or "Balanced",
        "nitrogen": n,
        "phosphorus": p,
        "potassium": k,
        "ph": ph,
        "rainfall_mm": rainfall,
        "temperature_c": temp,
        "drainage": preset.get("drainage", "Moderate"),
        "soil_desc": preset.get("description", "")
    }


def calculate_crop_score(crop: Dict[str, Any], params: Dict[str, Any]) -> Tuple[float, List[str], List[str]]:
    """Calculates a 0-100 suitability score with explicit reasons and warning flags."""
    score = 0.0
    reasons: List[str] = []
    warnings: List[str] = []

    req_season = params["season"]
    req_soil = params["soil_type"]
    water = params["water_availability"]
    ph = params["ph"]
    temp = params["temperature_c"]
    budget = params["budget_preference"]
    land_type = params["land_type"]

    # ---------------- 1. SEASON SUITABILITY (Max 30 pts) ----------------
    crop_seasons = crop.get("seasons", [])
    if req_season in crop_seasons or "All Season / Flexible" in crop_seasons:
        score += 30.0
        reasons.append(f"Optimal sowing window in {req_season} season ({crop.get('sowing_window')}).")
    elif any(s in req_season for s in crop_seasons):
        score += 26.0
        reasons.append(f"Season aligns well with {crop.get('name')} growth cycle.")
    else:
        # Penalize severely for out-of-season sowing
        score -= 25.0
        warnings.append(f"Typically not sown in {req_season}. Recommended season: {', '.join(crop_seasons)}.")

    # ---------------- 2. SOIL TYPE COMPATIBILITY (Max 25 pts) ----------------
    suitable_soils = crop.get("suitable_soils", [])
    tolerated_soils = crop.get("tolerated_soils", [])

    if req_soil in suitable_soils:
        score += 25.0
        reasons.append(f"Highly compatible with {req_soil} ({crop.get('soil_notes')[:60]}...).")
    elif req_soil in tolerated_soils:
        score += 15.0
        reasons.append(f"Tolerates {req_soil} with adequate organic manure and aeration.")
        warnings.append(f"Yield is moderate in {req_soil}; incorporate organic compost or FYM.")
    else:
        score += 5.0
        warnings.append(f"{req_soil} is not ideal; requires rigorous soil conditioning and drainage management.")

    # ---------------- 3. WATER & IRRIGATION MATCH (Max 25 pts) ----------------
    crop_water = crop.get("water_requirement", "Medium")  # Low, Medium, High

    if "Low" in water:  # Rainfed / Drought-prone
        if crop_water == "Low":
            score += 25.0
            reasons.append("Highly drought-hardy; thrives under rainfed / water-scarce conditions.")
        elif crop_water == "Medium":
            score += 10.0
            warnings.append("Requires at least 2-3 protective irrigations; risky under pure rainfed conditions.")
        else:  # High water crop under rainfed
            score -= 30.0
            warnings.append(f"CRITICAL: {crop['name']} demands high water (irrigation); severe risk of crop failure in rainfed conditions.")
    elif "Moderate" in water:  # Canal / Tube-well
        if crop_water == "Low":
            score += 22.0
            reasons.append("Low water need ensures safe yields with minimal pumping cost.")
        elif crop_water == "Medium":
            score += 25.0
            reasons.append("Moderate irrigation access is the perfect match for this crop's water budget.")
        else:
            score += 14.0
            warnings.append("High water demand; ensure your tube-well/canal supply remains reliable during flowering.")
    else:  # High / Assured irrigation
        if crop_water == "High":
            score += 25.0
            reasons.append("Assured irrigation allows this high-yield crop to reach maximum genetic potential.")
        elif crop_water == "Medium":
            score += 23.0
            reasons.append("Assured irrigation eliminates moisture stress.")
        else:
            score += 19.0
            reasons.append("Low water need; avoid over-irrigation to prevent root rot.")

    # ---------------- 4. pH & NUTRIENT BALANCE (Max 10 pts) ----------------
    min_ph = crop.get("optimal_ph_min", 6.0)
    max_ph = crop.get("optimal_ph_max", 7.5)
    abs_min_ph = crop.get("min_ph", 5.5)
    abs_max_ph = crop.get("max_ph", 8.2)

    if min_ph <= ph <= max_ph:
        score += 10.0
        reasons.append(f"Soil pH {ph:.1f} is right in the ideal range ({min_ph}-{max_ph}).")
    elif abs_min_ph <= ph <= abs_max_ph:
        score += 6.0
        reasons.append(f"Soil pH {ph:.1f} is acceptable for {crop['name']}.")
    else:
        score += 1.0
        if ph < abs_min_ph:
            warnings.append(f"Soil is overly acidic (pH {ph:.1f}); apply agricultural lime before sowing.")
        else:
            warnings.append(f"Soil is overly alkaline (pH {ph:.1f}); apply gypsum and organic mulch.")

    # ---------------- 5. TEMPERATURE & CLIMATE ENVELOPE (Max 10 pts) ----------------
    opt_temp_min = crop.get("optimal_temp_min", 18.0)
    opt_temp_max = crop.get("optimal_temp_max", 32.0)
    abs_temp_min = crop.get("min_temp", 12.0)
    abs_temp_max = crop.get("max_temp", 40.0)

    if opt_temp_min <= temp <= opt_temp_max:
        score += 10.0
    elif abs_temp_min <= temp <= abs_temp_max:
        score += 6.0
    else:
        score += 2.0
        warnings.append(f"Temperature ({temp:.1f}°C) is outside optimum range ({opt_temp_min}-{opt_temp_max}°C).")

    # ---------------- 6. BUDGET & LAND ADJUSTMENTS ----------------
    crop_inv = crop.get("investment_level", "Moderate")
    crop_prof = crop.get("profit_potential", "Moderate")

    if budget == "Low Cost" and crop_inv == "Low":
        score += 4.0
        reasons.append("Low initial seed & input investment fits your low-cost preference.")
    elif budget == "Low Cost" and crop_inv == "High":
        score -= 6.0
        warnings.append("High initial capital required (seeds/seedlings/inputs).")
    elif budget == "Commercial / High Value" and "High" in crop_prof:
        score += 5.0
        reasons.append(f"High profit potential ({crop['profit_potential']}) aligns with commercial objective.")

    # Topography checks
    if land_type == "Lowland" and crop["id"] == "rice":
        score += 5.0
        reasons.append("Lowland fields with water stagnation are ideal for paddy.")
    elif land_type == "Lowland" and crop["id"] in ["maize", "cotton", "turmeric", "chilli"]:
        score -= 10.0
        warnings.append("Prone to root rot in waterlogging lowlands; construct deep drainage furrows.")

    # Bound score between 0 and 100
    final_score = max(0.0, min(100.0, round(score, 1)))
    return final_score, reasons, warnings


def recommend_crops(req: RecommendationRequest) -> RecommendationResponse:
    """Evaluates all crops in database and produces ranked recommendations."""
    params = resolve_parameters(req)
    all_crops = get_all_crops()
    evaluated: List[CropRecommendation] = []

    for crop in all_crops:
        score, reasons, warnings = calculate_crop_score(crop, params)

        if score >= 80.0:
            level = "Highly Recommended"
        elif score >= 65.0:
            level = "Recommended"
        elif score >= 48.0:
            level = "Moderately Suitable"
        else:
            level = "Marginal / High Risk"

        rec = CropRecommendation(
            crop_id=crop["id"],
            name=crop["name"],
            hindi_name=crop.get("hindi_name"),
            scientific_name=crop["scientific_name"],
            category=crop["category"],
            suitability_score=score,
            suitability_level=level,
            sowing_window=crop["sowing_window"],
            duration_days=crop["duration_days"],
            water_requirement=crop["water_requirement"],
            estimated_yield_per_acre=crop["estimated_yield_per_acre"],
            investment_level=crop["investment_level"],
            profit_potential=crop["profit_potential"],
            reasons=reasons,
            warnings=warnings,
            sowing_tips=crop["sowing_tips"],
            fertilizer_advice=crop["fertilizer_advice"],
            soil_notes=crop["soil_notes"],
            companion_crops=crop.get("companion_crops", [])
        )
        evaluated.append(rec)

    # Sort primarily by suitability score descending
    evaluated.sort(key=lambda x: x.suitability_score, reverse=True)

    top_pick = evaluated[0] if evaluated else None

    return RecommendationResponse(
        total_crops_evaluated=len(all_crops),
        recommendations=evaluated,
        top_pick=top_pick,
        soil_summary={
            "soil_type": params["soil_type"],
            "description": params["soil_desc"],
            "drainage": params["drainage"],
            "benchmark_npk": f"N: {params['nitrogen']:.0f}, P: {params['phosphorus']:.0f}, K: {params['potassium']:.0f} kg/ha",
            "benchmark_ph": f"{params['ph']:.1f}"
        },
        applied_parameters=params
    )
