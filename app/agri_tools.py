"""AgriAssist Agronomic Tools & Calculators.
Provides:
1. Fertilizer Prescription (Urea, DAP, MOP stoichiometric bag calculator & pH amendments).
2. Farm Financials & MSP Profit Calculator (costs, yields, revenue, ROI).
3. 1-Year Multi-Crop Rotation & Sequencing Planner (Kharif -> Rabi -> Zaid).
"""

from typing import Dict, Any, List, Optional
import math
from datetime import datetime, timedelta, date


def calculate_fertilizer_prescription(
    soil_n: float,
    soil_p: float,
    soil_k: float,
    soil_ph: float,
    ideal_n: float,
    ideal_p: float,
    ideal_k: float,
    land_size_acres: float = 1.0
) -> Dict[str, Any]:
    """Calculates exact commercial fertilizer bags (Urea, DAP, MOP) and soil amendments.
    NPK are in kg/ha, converted for the farmer's land acreage (1 ha = 2.471 acres).
    """
    acre_factor = max(0.1, land_size_acres) / 2.471

    # Deficits in kg/ha
    delta_n = max(0.0, ideal_n - (soil_n or 0.0))
    delta_p = max(0.0, ideal_p - (soil_p or 0.0))
    delta_k = max(0.0, ideal_k - (soil_k or 0.0))

    # Total pure nutrient requirements in kg for the specified land area
    n_req_kg = delta_n * acre_factor
    p_req_kg = delta_p * acre_factor
    k_req_kg = delta_k * acre_factor

    # 1. DAP (18% N, 46% P2O5) to meet Phosphorus requirement
    if p_req_kg > 0:
        dap_kg = p_req_kg / 0.46
    else:
        # Maintenance baseline dose (10 kg/acre if soil P is already high)
        dap_kg = 10.0 * land_size_acres
    n_from_dap = dap_kg * 0.18

    # 2. Urea (46% N) to meet remaining Nitrogen requirement
    remaining_n_kg = max(0.0, n_req_kg - n_from_dap)
    if remaining_n_kg > 0:
        urea_kg = remaining_n_kg / 0.46
    else:
        # Minimum baseline dose for vegetative vigor
        urea_kg = 15.0 * land_size_acres

    # 3. MOP (Muriate of Potash, 60% K2O) to meet Potassium requirement
    if k_req_kg > 0:
        mop_kg = k_req_kg / 0.60
    else:
        mop_kg = 10.0 * land_size_acres

    # 50 kg bags
    urea_bags = round(urea_kg / 50.0, 1)
    dap_bags = round(dap_kg / 50.0, 1)
    mop_bags = round(mop_kg / 50.0, 1)

    # Approximate market cost of fertilizers in India (subsidized rates: Urea ~₹270/bag, DAP ~₹1350/bag, MOP ~₹1700/bag)
    approx_fertilizer_cost = round((urea_bags * 270.0) + (dap_bags * 1350.0) + (mop_bags * 1700.0), 0)

    # Soil amendment calculation
    lime_kg = 0.0
    gypsum_kg = 0.0
    amendment_type = "None Required"
    amendment_advice = "Soil pH is within healthy agronomic limits (6.0 - 8.0). No chemical amendment needed."

    if soil_ph is not None:
        if soil_ph < 6.0:
            lime_kg = round((6.5 - soil_ph) * 350.0 * land_size_acres, 0)
            amendment_type = "Agricultural Lime (CaCO3)"
            amendment_advice = (
                f"Soil is acidic (pH {soil_ph:.1f}). Broadcast {lime_kg:.0f} kg Agricultural Lime "
                f"3-4 weeks before sowing to buffer acidity and unlock Phosphorus availability."
            )
        elif soil_ph > 8.0:
            gypsum_kg = round((soil_ph - 7.5) * 450.0 * land_size_acres, 0)
            amendment_type = "Agricultural Gypsum (CaSO4.2H2O)"
            amendment_advice = (
                f"Soil is alkaline / sodic (pH {soil_ph:.1f}). Apply {gypsum_kg:.0f} kg Gypsum "
                f"before deep tillage, followed by heavy irrigation to flush out displaced Sodium."
            )

    return {
        "urea_kg": round(urea_kg, 1),
        "urea_bags_50kg": urea_bags,
        "dap_kg": round(dap_kg, 1),
        "dap_bags_50kg": dap_bags,
        "mop_kg": round(mop_kg, 1),
        "mop_bags_50kg": mop_bags,
        "approx_fertilizer_cost_inr": approx_fertilizer_cost,
        "application_schedule": [
            {"stage": "Basal (At Sowing)", "advice": f"Full DAP ({dap_bags} bags) + Full MOP ({mop_bags} bags) + 1/3rd Urea ({(urea_bags/3):.1f} bags)."},
            {"stage": "First Top Dressing (Vegetative / 20-30 Days)", "advice": f"1/3rd Urea ({(urea_bags/3):.1f} bags) during weeding/first irrigation."},
            {"stage": "Second Top Dressing (Flowering / 45-60 Days)", "advice": f"Remaining 1/3rd Urea ({(urea_bags/3):.1f} bags). Avoid late application."}
        ],
        "amendment_type": amendment_type,
        "lime_kg": lime_kg,
        "gypsum_kg": gypsum_kg,
        "amendment_advice": amendment_advice
    }


def calculate_crop_financials(crop: Dict[str, Any], land_size_acres: float = 1.0) -> Dict[str, Any]:
    """Calculates detailed cultivation costs, yield, gross revenue, net profit, and ROI based on Indian MSP."""
    acres = max(0.1, land_size_acres)

    # Defaults if missing from database
    seed_rate = crop.get("seed_rate_kg_acre", 15.0)
    seed_cost_kg = crop.get("seed_cost_per_kg", 80.0)
    cultivation_cost_acre = crop.get("cultivation_cost_per_acre", 14000.0)
    yield_min = crop.get("yield_quintal_min", 12.0)
    yield_max = crop.get("yield_quintal_max", 18.0)
    msp_price = crop.get("msp_per_quintal", 2300.0)

    # Input costs
    seed_cost_total = round(seed_rate * seed_cost_kg * acres, 0)
    operations_cost_total = round(cultivation_cost_acre * acres, 0)
    # Fertilizer standard estimate (approx ₹3500/acre)
    fert_cost_total = round(3500.0 * acres, 0)

    total_cost = seed_cost_total + operations_cost_total + fert_cost_total

    # Production & Revenue
    avg_yield_per_acre = (yield_min + yield_max) / 2.0
    total_yield_quintals = round(avg_yield_per_acre * acres, 1)
    gross_revenue = round(total_yield_quintals * msp_price, 0)

    net_profit = round(gross_revenue - total_cost, 0)
    roi_pct = round((net_profit / total_cost * 100.0), 1) if total_cost > 0 else 0.0

    return {
        "land_size_acres": acres,
        "msp_or_market_price_per_quintal": msp_price,
        "avg_yield_per_acre_quintal": avg_yield_per_acre,
        "total_estimated_yield_quintals": total_yield_quintals,
        "seed_cost_inr": seed_cost_total,
        "fertilizer_cost_inr": fert_cost_total,
        "operations_and_labor_cost_inr": operations_cost_total,
        "total_investment_cost_inr": total_cost,
        "gross_revenue_inr": gross_revenue,
        "net_profit_inr": net_profit,
        "roi_percentage": roi_pct,
        "profit_per_acre_inr": round(net_profit / acres, 0)
    }


def generate_crop_rotation_plans(
    soil_type: str,
    water_availability: str,
    budget_preference: str = "Balanced",
    land_size_acres: float = 1.0
) -> List[Dict[str, Any]]:
    """Generates ranked 1-Year Multi-Crop Rotation Plans (Kharif -> Rabi -> Zaid).
    Balances profitability, soil health (nitrogen-fixing legumes), and water security.
    """
    acres = max(0.1, float(land_size_acres or 1.0))
    is_rainfed = "Low" in water_availability
    is_moderate = "Moderate" in water_availability
    is_high_water = "High" in water_availability

    plans: List[Dict[str, Any]] = []

    # System 1: Sustainable Grain-Pulse Rotation (Classic high-nitrogen, low-risk)
    if is_rainfed:
        c1 = {"season": "Kharif", "crop_id": "pearl_millet", "crop_name": "Pearl Millet (Bajra)", "role": "Drought-hardy cereal feed & grain", "duration": "80 days", "water": "Low", "net_profit_per_acre": 16000}
        c2 = {"season": "Rabi", "crop_id": "chickpea", "crop_name": "Chickpea (Desi Chana)", "role": "Nitrogen-fixing pulse, soil restorer", "duration": "105 days", "water": "Low", "net_profit_per_acre": 28000}
        c3 = {"season": "Zaid", "crop_id": "cowpea", "crop_name": "Cowpea / Fallow Green Manure", "role": "Bio-mulch & soil organic carbon", "duration": "60 days", "water": "Low", "net_profit_per_acre": 8000}
        desc = "Drought-Resilient Arid Cycle: Conserves moisture, enriches sandy/loam soil with deep-rooted legume rotation."
        soil_score = 92
    elif is_high_water:
        c1 = {"season": "Kharif", "crop_id": "rice", "crop_name": "Paddy (Rice)", "role": "High-yield staple cereal", "duration": "125 days", "water": "High", "net_profit_per_acre": 32000}
        c2 = {"season": "Rabi", "crop_id": "wheat", "crop_name": "Wheat", "role": "Food security & assured MSP cereal", "duration": "120 days", "water": "Medium", "net_profit_per_acre": 34000}
        c3 = {"season": "Zaid", "crop_id": "green_gram", "crop_name": "Green Gram (Moong)", "role": "Short-window pulse fixing 35-40 kg N/ha", "duration": "65 days", "water": "Low to Medium", "net_profit_per_acre": 19000}
        desc = "Intensive High-Yield Cereal-Legume Triplet: Maximizes biomass with third-crop Moong rejuvenating soil after heavy cereal extraction."
        soil_score = 88
    else: # Moderate
        c1 = {"season": "Kharif", "crop_id": "maize", "crop_name": "Maize (Corn)", "role": "Nutrient-efficient commercial cereal", "duration": "95 days", "water": "Medium", "net_profit_per_acre": 31000}
        c2 = {"season": "Rabi", "crop_id": "mustard", "crop_name": "Mustard / Rapeseed", "role": "High-oil cash crop with modest water need", "duration": "115 days", "water": "Low to Medium", "net_profit_per_acre": 36000}
        c3 = {"season": "Zaid", "crop_id": "green_gram", "crop_name": "Green Gram (Moong)", "role": "Legume pulse restoring microbial soil health", "duration": "65 days", "water": "Low", "net_profit_per_acre": 19000}
        desc = "Balanced Maize-Mustard-Moong Trilogy: Exceptional economic return with low pumping cost and biological pest interruption."
        soil_score = 95

    annual_profit_1 = (c1["net_profit_per_acre"] + c2["net_profit_per_acre"] + c3["net_profit_per_acre"]) * acres
    plans.append({
        "plan_id": "plan_balanced_soil_health",
        "title": "Soil-Restorative Cereal & Legume Rotation",
        "badge": "Highest Soil Health Index",
        "description": desc,
        "soil_health_index": soil_score,
        "nitrogen_fixation_benefit": "Fixes ~30-45 kg biological Nitrogen/ha naturally, reducing subsequent Urea need by 25%.",
        "pest_break_benefit": "Alternating grass cereals with broadleaf legumes disrupts monophagous insect pupation in soil.",
        "crops": [c1, c2, c3],
        "total_annual_net_profit_inr": round(annual_profit_1, 0),
        "annual_net_profit_per_acre_inr": round(annual_profit_1 / acres, 0)
    })

    # System 2: High-Value Commercial Cash Crop Rotation
    if "Black" in soil_type or "Alluvial" in soil_type:
        c1_b = {"season": "Kharif", "crop_id": "cotton", "crop_name": "Cotton", "role": "High-profit fiber crop", "duration": "160 days", "water": "Medium to High", "net_profit_per_acre": 46000}
        c2_b = {"season": "Rabi", "crop_id": "chickpea", "crop_name": "Chickpea (Kabuli / Desi)", "role": "Late sown pulse recovering soil structure", "duration": "95 days", "water": "Low", "net_profit_per_acre": 29000}
        c3_b = {"season": "Zaid", "crop_id": "watermelon", "crop_name": "Summer Watermelon", "role": "Quick-turnaround commercial cash fruit", "duration": "75 days", "water": "Medium", "net_profit_per_acre": 35000}
        desc_b = "Cotton-Pulse-Melon High Income Cycle: Optimized for heavy soils with strong market price appreciation."
        soil_score_b = 82
    else:
        c1_b = {"season": "Kharif", "crop_id": "groundnut", "crop_name": "Groundnut (Peanut)", "role": "Nitrogen-fixing oilseed & valuable fodder", "duration": "105 days", "water": "Medium", "net_profit_per_acre": 38000}
        c2_b = {"season": "Rabi", "crop_id": "potato", "crop_name": "Potato", "role": "High-tonnage commercial tuber crop", "duration": "90 days", "water": "Medium", "net_profit_per_acre": 52000}
        c3_b = {"season": "Zaid", "crop_id": "green_gram", "crop_name": "Green Gram (Moong)", "role": "Restores soil fertility post intensive potato", "duration": "65 days", "water": "Low", "net_profit_per_acre": 19000}
        desc_b = "Groundnut-Potato-Moong Commercial Triplet: High return per acre with balanced tuber and legume dynamics."
        soil_score_b = 85

    annual_profit_2 = (c1_b["net_profit_per_acre"] + c2_b["net_profit_per_acre"] + c3_b["net_profit_per_acre"]) * acres
    plans.append({
        "plan_id": "plan_commercial_maximizer",
        "title": "Commercial High-Revenue Market Rotation",
        "badge": "Maximum Market Profit",
        "description": desc_b,
        "soil_health_index": soil_score_b,
        "nitrogen_fixation_benefit": "Legume integration supplies early organic nitrogen and maintains organic matter levels.",
        "pest_break_benefit": "Deep root crop followed by shallow vegetable disrupts soil compaction and nematode infestation.",
        "crops": [c1_b, c2_b, c3_b],
        "total_annual_net_profit_inr": round(annual_profit_2, 0),
        "annual_net_profit_per_acre_inr": round(annual_profit_2 / acres, 0)
    })

    # System 3: Oilseed & Pulse Resilient Rotation (Low Water & Stable Return)
    c1_c = {"season": "Kharif", "crop_id": "soybean", "crop_name": "Soybean", "role": "Rich protein/oil legume adding soil nitrogen", "duration": "95 days", "water": "Medium", "net_profit_per_acre": 32000}
    c2_c = {"season": "Rabi", "crop_id": "mustard", "crop_name": "Mustard / Rapeseed", "role": "Low input cost, high oil return", "duration": "110 days", "water": "Low to Medium", "net_profit_per_acre": 36000}
    c3_c = {"season": "Zaid", "crop_id": "green_gram", "crop_name": "Summer Moong", "role": "Protects topsoil from summer scorching & fixes nitrogen", "duration": "60 days", "water": "Low", "net_profit_per_acre": 18000}
    
    annual_profit_3 = (c1_c["net_profit_per_acre"] + c2_c["net_profit_per_acre"] + c3_c["net_profit_per_acre"]) * acres
    plans.append({
        "plan_id": "plan_oilseed_resilience",
        "title": "Dual-Legume & Oilseed Climate-Resilient Cycle",
        "badge": "Low Pumping & Water Risk",
        "description": "Soybean-Mustard-Moong: Dual legume cycle providing two natural soil replenishment windows with minimal irrigation stress.",
        "soil_health_index": 96,
        "nitrogen_fixation_benefit": "Provides up to 60 kg biological Nitrogen across 2 legume rotations, substantially cutting synthetic fertilizer overhead.",
        "pest_break_benefit": "Zero shared fungal or viral pathogens between mustard and soybean.",
        "crops": [c1_c, c2_c, c3_c],
        "total_annual_net_profit_inr": round(annual_profit_3, 0),
        "annual_net_profit_per_acre_inr": round(annual_profit_3 / acres, 0)
    })

    # Sort primarily by annual net profit
    plans.sort(key=lambda p: p["total_annual_net_profit_inr"], reverse=True)
    return plans


# ==============================================================================
# 4. PLANT DOCTOR & PEST DIAGNOSTIC ENGINE
# ==============================================================================
def diagnose_plant_issue(
    crop_id: str = None,
    plant_part: str = None,
    symptoms: List[str] = None,
    search_term: str = None
) -> List[Dict[str, Any]]:
    """Filters and ranks pest and disease diagnoses based on crop, affected plant part, and symptoms."""
    from app.database import get_all_pests_diseases, get_crop_by_id

    db = get_all_pests_diseases()
    matches: List[Dict[str, Any]] = []

    search_clean = (search_term or "").strip().lower()

    for item in db:
        # 1. Filter by crop if specified
        if crop_id and crop_id.lower() != "all" and item["crop_id"].lower() != crop_id.lower():
            continue

        # 2. Filter by affected part if specified
        if plant_part and plant_part.lower() != "all" and "whole plant" not in [p.lower() for p in item["affected_parts"]]:
            if plant_part.lower() not in [p.lower() for p in item["affected_parts"]]:
                continue

        # 3. Search query keyword match
        if search_clean:
            haystack = f"{item['name']} {item.get('hindi_name', '')} {item['crop_name']} {' '.join(item['symptoms'])} {' '.join(item['biological_control'])} {' '.join(item['chemical_control'])}".lower()
            if search_clean not in haystack:
                continue

        # 4. Symptom checklist match
        if symptoms and len(symptoms) > 0:
            item_symptoms_str = " ".join(item["symptoms"]).lower()
            if not any(sym.lower() in item_symptoms_str for sym in symptoms):
                continue

        matches.append(item)

    # Sort by severity (Critical -> High -> Moderate -> Low)
    severity_rank = {"Critical": 4, "High": 3, "Moderate": 2, "Low": 1}
    matches.sort(key=lambda x: severity_rank.get(x.get("severity", "Moderate"), 2), reverse=True)
    return matches


# ==============================================================================
# 5. MANDI PRICE EXPLORER & VOLATILITY ANALYTICS
# ==============================================================================
def get_mandi_prices_filtered(
    crop_id: str = None,
    state: str = None,
    district: str = None
) -> List[Dict[str, Any]]:
    """Retrieves APMC mandi prices with 30-day historical trends and MSP differentials."""
    from app.database import get_mandi_prices_data

    records = get_mandi_prices_data()
    results = []

    for r in records:
        if crop_id and crop_id.lower() != "all" and r["crop_id"].lower() != crop_id.lower():
            continue
        if state and state.lower() != "all" and r["state"].lower() != state.lower():
            continue
        if district and district.lower() != "all" and r["district"].lower() != district.lower():
            continue

        item = dict(r)
        item["price_vs_msp_diff"] = round(item["modal_price_per_quintal"] - item["msp_price"], 0)
        results.append(item)

    # Sort with highest premium over MSP first
    results.sort(key=lambda x: x["price_vs_msp_diff"], reverse=True)
    return results


# ==============================================================================
# 6. SMART IRRIGATION & WATER BUDGETING SCHEDULER
# ==============================================================================
def calculate_smart_irrigation(
    crop_id: str,
    growth_stage: str,
    soil_type: str = "Alluvial Soil",
    land_size_acres: float = 1.0,
    pump_hp: float = 5.0,
    forecast_rain_mm: float = 0.0
) -> Dict[str, Any]:
    """Calculates water depth, volume (liters), pumping hours, and weather adjustments."""
    from app.database import get_crop_by_id

    crop = get_crop_by_id(crop_id)
    crop_name = crop.get("name", crop_id.title()) if crop else crop_id.title()
    water_req = crop.get("water_requirement", "Medium") if crop else "Medium"

    # Base water depth per irrigation in mm by crop type & stage sensitivity
    stage_lower = growth_stage.lower()
    base_depth_mm = 50.0

    if "germination" in stage_lower or "seedling" in stage_lower or "sowing" in stage_lower:
        base_depth_mm = 35.0
    elif "cri" in stage_lower or "tillering" in stage_lower or "branching" in stage_lower:
        base_depth_mm = 55.0
    elif "flowering" in stage_lower or "panicle" in stage_lower or "tasseling" in stage_lower or "boll" in stage_lower:
        base_depth_mm = 65.0  # Peak moisture sensitive
    elif "grain" in stage_lower or "milking" in stage_lower or "pod filling" in stage_lower or "tuber" in stage_lower:
        base_depth_mm = 50.0
    elif "maturity" in stage_lower or "harvest" in stage_lower:
        base_depth_mm = 25.0

    # Crop type baseline modifier
    if water_req == "High":
        base_depth_mm *= 1.25
    elif water_req == "Low":
        base_depth_mm *= 0.75

    # Soil texture adjustments:
    # Sandy soils hold less water -> lower depth per event, shorter interval
    # Clay / Black soils hold more water -> higher depth per event, longer interval
    soil_factor = 1.0
    interval_days = 10
    if "Sandy" in soil_type:
        soil_factor = 0.80
        interval_days = 6
    elif "Black" in soil_type or "Clay" in soil_type:
        soil_factor = 1.15
        interval_days = 14
    elif "Red" in soil_type or "Laterite" in soil_type:
        soil_factor = 0.90
        interval_days = 8

    final_depth_mm = round(base_depth_mm * soil_factor, 1)

    # 1 mm depth over 1 acre = 4,046.86 Liters
    acres = max(0.1, land_size_acres)
    water_volume_liters = round(final_depth_mm * 4046.86 * acres, 0)
    water_volume_acre_inches = round(final_depth_mm / 25.4 * acres, 2)

    # Pump runtime: 5 HP motor ~ 32,500 L/hr discharge
    pump_hp_safe = max(1.0, pump_hp)
    pump_lph = pump_hp_safe * 6500.0
    pump_runtime_hours = round(water_volume_liters / pump_lph, 1)

    # Total seasonal irrigations estimated
    total_irrigations = 5
    if water_req == "High":
        total_irrigations = 10 if "rice" in crop_id.lower() else 7
    elif water_req == "Low":
        total_irrigations = 2

    # Weather rain alert
    rain_warning = False
    postpone_alert = None
    advisory_notes = f"Provide standard irrigation of {final_depth_mm} mm ({pump_runtime_hours} hrs of 5 HP pump) every {interval_days} days."

    if forecast_rain_mm and forecast_rain_mm >= 15.0:
        rain_warning = True
        postpone_alert = (
            f"Open-Meteo predicts {forecast_rain_mm:.1f} mm rainfall in next 48-72h. "
            f"Postpone scheduled irrigation turn to conserve water and prevent root rot."
        )
        advisory_notes = (
            f"⚠️ WEATHER ALERT: Open-Meteo predicts {forecast_rain_mm:.1f} mm rainfall in the next 48-72h. "
            f"POSTPONE irrigation immediately! Natural precipitation will satisfy current root zone requirements "
            f"and prevent root rot or nitrogen leaching."
        )
    elif "flowering" in stage_lower or "cri" in stage_lower:
        advisory_notes += " ⚠️ CRITICAL STAGE: Do not allow soil to undergo water stress during this phase to prevent flower drop or aborted grain filling."

    critical_stages = [
        "CRI / Early Vegetative Stage (Root architecture establishment)",
        "Flowering / Panicle Emergence (Pollen viability & fertilization)",
        "Grain / Fruit / Pod Filling (Biomass trans-location)"
    ]

    water_saving_tips = [
        "Use drip or sprinkler irrigation to save 40-50% water over conventional flood furrow irrigation.",
        "Apply organic paddy straw or plastic mulch to reduce surface evaporation by up to 35%.",
        "Irrigate strictly during early morning (6-9 AM) or late evening to minimize convective heat losses.",
        "Maintain proper bunding and laser-level the field to guarantee uniform moisture infiltration."
    ]

    return {
        "crop_name": crop_name,
        "growth_stage": growth_stage,
        "soil_type": soil_type,
        "land_size_acres": acres,
        "water_depth_mm": final_depth_mm,
        "water_volume_liters": water_volume_liters,
        "total_water_volume_liters": water_volume_liters,
        "water_volume_acre_inches": water_volume_acre_inches,
        "pump_runtime_hours": pump_runtime_hours,
        "pump_run_hours": pump_runtime_hours,
        "irrigation_interval_days": interval_days,
        "interval_days": f"Every {interval_days} Days",
        "total_irrigations_needed": total_irrigations,
        "rain_warning": rain_warning,
        "postpone_irrigation_alert": postpone_alert,
        "advisory_notes": advisory_notes,
        "critical_stages": critical_stages,
        "water_saving_tips": water_saving_tips,
        "weather_rain_forecast_mm": forecast_rain_mm
    }


# ==============================================================================
# 7. ORGANIC & NATURAL FARMING (JAIVIK KHETI) PRESCRIPTIONS
# ==============================================================================
def calculate_organic_prescription(crop_id: str, land_size_acres: float = 1.0) -> Dict[str, Any]:
    """Calculates biological preparations, microbial inoculants, and organic recipes."""
    from app.database import get_crop_by_id, get_organic_recipes_data

    crop = get_crop_by_id(crop_id)
    crop_name = crop.get("name", crop_id.title()) if crop else crop_id.title()
    acres = max(0.1, float(land_size_acres or 1.0))

    # Calculate biological quantities for specified acreage
    jeevamrutha_liters = round(200.0 * acres * 2.0, 0)  # 2 applications of 200L/acre
    beejamrit_kg = round(10.0 * acres, 1)               # Seed treatment volume
    ghanjeevamrit_kg = round(150.0 * acres, 0)          # Basal dry cake
    vermicompost_tons = round(1.5 * acres, 1)           # Organic compost
    neemastra_liters = round(100.0 * acres, 0)          # Natural pest spray

    # Tailored biofertilizers
    category = crop.get("category", "Cereal") if crop else "Cereal"
    if category == "Pulse":
        bioferts = [
            "Rhizobium biofertilizer @ 250g per 10 kg seed (Symbiotic Nitrogen fixation)",
            "Phosphate Solubilizing Bacteria (PSB) @ 500g/acre (Releases locked soil phosphorus)",
            "Trichoderma viride @ 5g/kg seed (Biological wilt & root-rot protection)"
        ]
    else:
        bioferts = [
            "Azotobacter / Azospirillum @ 500g/acre (Free-living Nitrogen fixation)",
            "Phosphate Solubilizing Bacteria (PSB) @ 500g/acre (Releases soil phosphorus)",
            "Mycorrhiza (VAM) @ 4 kg/acre (Expands root surface area by 300%)"
        ]

    recipes = get_organic_recipes_data()

    return {
        "crop_id": crop_id,
        "crop_name": crop_name,
        "land_size_acres": acres,
        "total_jeevamrutha_liters": jeevamrutha_liters,
        "jeevamrutha_liters": jeevamrutha_liters,
        "beejamrit_kg": beejamrit_kg,
        "beejamrit_liters": beejamrit_kg,
        "ghanjeevamrit_kg": ghanjeevamrit_kg,
        "vermicompost_tons": vermicompost_tons,
        "neemastra_liters": neemastra_liters,
        "biofertilizers": bioferts,
        "recipes": recipes
    }


# ==============================================================================
# 8. GOVERNMENT SCHEMES, SUBSIDIES & KCC CALCULATOR
# ==============================================================================
def calculate_government_schemes_and_kcc(
    crop_id: str = "wheat",
    land_size_acres: float = 1.0,
    farmer_category: str = "Small / Marginal (< 2 Ha)",
    state: str = "All-India"
) -> Dict[str, Any]:
    """Calculates PMFBY crop insurance premiums, KCC loan limits, and PMKSY drip subsidies."""
    from app.database import get_crop_by_id, get_government_schemes_data

    crop = get_crop_by_id(crop_id)
    crop_name = crop.get("name", crop_id.title()) if crop else crop_id.title()
    category = crop.get("category", "Cereal") if crop else "Cereal"
    seasons = crop.get("seasons", ["Rabi"]) if crop else ["Rabi"]
    acres = max(0.1, float(land_size_acres or 1.0))
    farmer_cat_safe = str(farmer_category or "Small / Marginal (< 2 Ha)")

    db = get_government_schemes_data()

    # 1. Scale of Finance for KCC Crop Loan
    scale_dict = db.get("kcc_scale_of_finance_per_acre", {})
    scale_per_acre = scale_dict.get(crop_id.lower(), scale_dict.get("default", 30000.0))
    kcc_loan_limit = round(scale_per_acre * acres * 1.10, 0)  # 10% post-harvest maintenance buffer

    # 2. PMFBY Crop Insurance Premium Calculation
    sum_insured = round(scale_per_acre * acres, 0)
    is_commercial = category in ["Cash Crop", "Vegetable", "Spices", "Fiber"]
    is_kharif = "Kharif" in seasons

    if is_commercial:
        farmer_rate = 0.05
        season_cat_label = "Commercial / Horticultural"
    elif "Rabi" in seasons:
        farmer_rate = 0.015
        season_cat_label = "Rabi"
    else:
        farmer_rate = 0.02
        season_cat_label = "Kharif"

    actuarial_rate = 0.12  # Realistic commercial market insurance rate ~12%
    total_commercial_premium = sum_insured * actuarial_rate
    farmer_pmfby_premium = round(sum_insured * farmer_rate, 0)
    govt_pmfby_subsidy = round(total_commercial_premium - farmer_pmfby_premium, 0)

    # 3. Micro-Irrigation Drip Subsidy (PMKSY)
    is_small_marginal = "Small" in farmer_cat_safe or "Marginal" in farmer_cat_safe or acres <= 5.0
    sub_info = db["micro_irrigation_subsidies"]["small_marginal" if is_small_marginal else "general"]
    drip_pct = sub_info["drip_pct"]
    base_drip_cost_per_acre = 48000.0
    total_drip_cost = base_drip_cost_per_acre * acres
    drip_subsidy_amount = round(total_drip_cost * (drip_pct / 100.0), 0)

    # 4. PM-KISAN Annual Benefit
    pm_kisan_annual = 6000.0

    # 5. Populate specific scheme details
    schemes_list = []
    for s in db.get("schemes_list", []):
        detail = dict(s)
        if s["scheme_id"] == "pm_kisan":
            detail["calculated_benefit_inr"] = pm_kisan_annual
        elif s["scheme_id"] == "pmfby":
            detail["calculated_benefit_inr"] = govt_pmfby_subsidy
        elif s["scheme_id"] == "kcc":
            detail["calculated_benefit_inr"] = kcc_loan_limit
        elif s["scheme_id"] == "pmksy_drip":
            detail["calculated_benefit_inr"] = drip_subsidy_amount
        else:
            detail["calculated_benefit_inr"] = 25000.0
        schemes_list.append(detail)

    # Structured sub-objects for rich frontend rendering
    pmfby_structured = {
        "season_category": season_cat_label,
        "sum_insured_inr": sum_insured,
        "farmer_premium_rate_percent": round(farmer_rate * 100, 1),
        "farmer_share_premium_inr": farmer_pmfby_premium,
        "govt_subsidy_share_inr": govt_pmfby_subsidy,
        "official_portal": "https://pmfby.gov.in"
    }

    kcc_structured = {
        "scale_of_finance_per_acre_inr": scale_per_acre,
        "recommended_credit_limit_inr": kcc_loan_limit,
        "interest_rate_percent": 7.0,
        "prompt_repayment_incentive_percent": 3.0,
        "effective_interest_rate_percent": 4.0,
        "official_portal": "https://myscheme.gov.in"
    }

    pmksy_drip_structured = {
        "farmer_category": farmer_cat_safe,
        "subsidy_percentage": drip_pct,
        "approx_equipment_cost_inr": total_drip_cost,
        "eligible_subsidy_inr": drip_subsidy_amount,
        "farmer_payable_inr": total_drip_cost - drip_subsidy_amount
    }

    return {
        "farmer_category": farmer_cat_safe,
        "land_size_acres": acres,
        "crop_name": crop_name,
        "sum_insured_inr": sum_insured,
        "farmer_pmfby_premium_inr": farmer_pmfby_premium,
        "govt_pmfby_subsidy_inr": govt_pmfby_subsidy,
        "kcc_crop_loan_limit_inr": kcc_loan_limit,
        "drip_subsidy_pct": drip_pct,
        "drip_subsidy_amount_inr": drip_subsidy_amount,
        "pm_kisan_annual_inr": pm_kisan_annual,
        "pm_kisan_annual_cash_inr": pm_kisan_annual,
        "pmfby": pmfby_structured,
        "kcc": kcc_structured,
        "pmksy_drip": pmksy_drip_structured,
        "schemes": schemes_list
    }


# ==============================================================================
# 9. STATE & DISTRICT AGRO-CLIMATIC PRESETS
# ==============================================================================
def get_district_presets(state: str = None) -> Dict[str, Any]:
    """Retrieves districts and agro-climatic profiles by state."""
    from app.database import get_state_district_data

    reg = get_state_district_data()
    if state and state.lower() != "all" and state in reg:
        return {state: reg[state]}
    return reg


# ==============================================================================
# 10. PRECISION SEED RATE & PLANTING GEOMETRY CALCULATOR
# ==============================================================================
CROP_SEED_GEOMETRY_CATALOG: Dict[str, Dict[str, Any]] = {
    "wheat": {
        "crop_name": "Wheat (गेहूं)",
        "base_seed_rate_kg_acre": 40.0,
        "standard_row_spacing_cm": 22.5,
        "standard_plant_spacing_cm": 5.0,
        "sowing_depth_cm": "4.0 - 5.0 cm",
        "sowing_method": "Zero-till Seed Drill / Line Sowing",
        "seed_treatment_protocol": "Carbendazim @ 2g/kg seed followed by Azotobacter and PSB bio-inoculants.",
        "certified_seed_rate_per_kg_inr": 42.0,
        "advisory": "Ensure sowing depth does not exceed 5 cm to promote rapid crown root initiation. Use certified seed with >85% germination."
    },
    "rice": {
        "crop_name": "Paddy / Rice (धान)",
        "base_seed_rate_kg_acre": 12.0,
        "standard_row_spacing_cm": 20.0,
        "standard_plant_spacing_cm": 15.0,
        "sowing_depth_cm": "2.0 - 3.0 cm",
        "sowing_method": "Transplanting / DSR (Direct Seeded Rice)",
        "seed_treatment_protocol": "Soak in 10% brine solution; treat viable seeds with Carbendazim 2g/kg + Pseudomonas fluorescens 10g/kg.",
        "certified_seed_rate_per_kg_inr": 55.0,
        "advisory": "Transplant 21-25 day old seedlings (2-3 seedlings per hill) for optimal tillering and panicle development."
    },
    "cotton": {
        "crop_name": "Cotton (कपास)",
        "base_seed_rate_kg_acre": 1.8,
        "standard_row_spacing_cm": 90.0,
        "standard_plant_spacing_cm": 60.0,
        "sowing_depth_cm": "3.0 - 4.0 cm",
        "sowing_method": "Dibbling on Ridges & Furrows",
        "seed_treatment_protocol": "Imidacloprid 70 WS @ 5g/kg for sucking pest protection + Trichoderma viride @ 4g/kg against root rot.",
        "certified_seed_rate_per_kg_inr": 850.0,
        "advisory": "Maintain proper square geometry (90x60 cm) to ensure aeration, reduce boll rot, and facilitate intercultural operations."
    },
    "soybean": {
        "crop_name": "Soybean (सोयाबीन)",
        "base_seed_rate_kg_acre": 28.0,
        "standard_row_spacing_cm": 45.0,
        "standard_plant_spacing_cm": 5.0,
        "sowing_depth_cm": "3.0 - 4.0 cm",
        "sowing_method": "Broad-Bed Furrow (BBF) / Line Sowing",
        "seed_treatment_protocol": "Bradyrhizobium japonicum @ 10g/kg + Trichoderma viride @ 5g/kg. Sowing within 48 hours of treatment.",
        "certified_seed_rate_per_kg_inr": 85.0,
        "advisory": "Do not sow deeper than 4 cm. Soybean hypocotyl is fragile and cannot emerge through crusted soil."
    },
    "chickpea": {
        "crop_name": "Chickpea / Gram (चना)",
        "base_seed_rate_kg_acre": 30.0,
        "standard_row_spacing_cm": 30.0,
        "standard_plant_spacing_cm": 10.0,
        "sowing_depth_cm": "5.0 - 7.0 cm",
        "sowing_method": "Line Sowing with Pora/Seed Drill",
        "seed_treatment_protocol": "Trichoderma harzianum @ 4g/kg + Mesorhizobium ciceri & PSB cultures.",
        "certified_seed_rate_per_kg_inr": 92.0,
        "advisory": "Deep sowing (6-7 cm) places seeds into residual moisture and protects seedlings against wilt and collar rot."
    },
    "mustard": {
        "crop_name": "Mustard / Rapeseed (सरसों)",
        "base_seed_rate_kg_acre": 2.0,
        "standard_row_spacing_cm": 30.0,
        "standard_plant_spacing_cm": 10.0,
        "sowing_depth_cm": "2.0 - 3.0 cm",
        "sowing_method": "Line Sowing with Ridge Seeder",
        "seed_treatment_protocol": "Apron 35 SD @ 6g/kg or Trichoderma viride @ 6g/kg seed.",
        "certified_seed_rate_per_kg_inr": 120.0,
        "advisory": "Thinning at 15-20 days after sowing is mandatory to leave single healthy plants spaced 10 cm apart."
    },
    "maize": {
        "crop_name": "Maize / Corn (मक्का)",
        "base_seed_rate_kg_acre": 8.0,
        "standard_row_spacing_cm": 60.0,
        "standard_plant_spacing_cm": 20.0,
        "sowing_depth_cm": "4.0 - 5.0 cm",
        "sowing_method": "Ridge Sowing / Bed Planting",
        "seed_treatment_protocol": "Cyantraniliprole 19.8% + Thiamethoxam 19.8% @ 6ml/kg against Fall Armyworm + Azospirillum culture.",
        "certified_seed_rate_per_kg_inr": 190.0,
        "advisory": "Maintain 60x20 cm spacing (~33,000 plants/acre) to maximize cob size, grain filling, and prevent barren stalks."
    },
    "potato": {
        "crop_name": "Potato (आलू)",
        "base_seed_rate_kg_acre": 850.0,
        "standard_row_spacing_cm": 60.0,
        "standard_plant_spacing_cm": 20.0,
        "sowing_depth_cm": "5.0 - 8.0 cm",
        "sowing_method": "Ridge and Furrow planting (well-sprouted tubers)",
        "seed_treatment_protocol": "Dip whole seed tubers in Mancozeb (0.25%) or Trichoderma for 10 minutes; shade dry before planting.",
        "certified_seed_rate_per_kg_inr": 28.0,
        "advisory": "Use certified disease-free medium-sized seed tubers (35-45 mm diameter, 40-50g weight with 2-3 sprouted eyes)."
    },
    "sugarcane": {
        "crop_name": "Sugarcane (गन्ना)",
        "base_seed_rate_kg_acre": 2500.0,
        "standard_row_spacing_cm": 90.0,
        "standard_plant_spacing_cm": 30.0,
        "sowing_depth_cm": "7.0 - 10.0 cm",
        "sowing_method": "Trench / Furrow Planting (3-budded setts)",
        "seed_treatment_protocol": "Dip setts in Carbendazim (0.1%) solution for 15 min + Acetobacter diazotrophicus slurry.",
        "certified_seed_rate_per_kg_inr": 4.5,
        "advisory": "Select disease-free setts from 8-10 month old crop. Maintain paired row or wide trench planting (120 cm) for sunlight."
    },
    "groundnut": {
        "crop_name": "Groundnut / Peanut (मूंगफली)",
        "base_seed_rate_kg_acre": 45.0,
        "standard_row_spacing_cm": 30.0,
        "standard_plant_spacing_cm": 10.0,
        "sowing_depth_cm": "4.0 - 5.0 cm",
        "sowing_method": "Line Sowing using Seed-cum-Fertilizer Drill",
        "seed_treatment_protocol": "Trichoderma viride @ 4g/kg + Rhizobium and Phosphobacteria biofertilizers.",
        "certified_seed_rate_per_kg_inr": 115.0,
        "advisory": "Shell pods only 1-2 days before sowing to retain seed viability. Sowing into moist soil is critical for peg entry."
    }
}


def calculate_seed_rate_and_population(
    crop_id: str,
    land_size_acres: float = 1.0,
    row_spacing_cm: float = None,
    plant_spacing_cm: float = None,
    germination_rate_pct: float = 85.0,
    sowing_method: str = "Line Sowing"
) -> Dict[str, Any]:
    """Calculates precision seed quantity, planting geometry, and estimated plant population."""
    from app.database import get_crop_by_id

    acres = max(0.1, float(land_size_acres or 1.0))
    germ_pct = max(50.0, min(100.0, float(germination_rate_pct or 85.0)))

    # Fetch profile from catalog or fallback
    profile = CROP_SEED_GEOMETRY_CATALOG.get(crop_id)
    if not profile:
        crop_db = get_crop_by_id(crop_id)
        crop_name = crop_db["name"] if crop_db else crop_id.title()
        profile = {
            "crop_name": crop_name,
            "base_seed_rate_kg_acre": 15.0,
            "standard_row_spacing_cm": 30.0,
            "standard_plant_spacing_cm": 15.0,
            "sowing_depth_cm": "3.0 - 4.0 cm",
            "sowing_method": sowing_method or "Line Sowing",
            "seed_treatment_protocol": "General seed treatment with Trichoderma viride @ 5g/kg seed.",
            "certified_seed_rate_per_kg_inr": 60.0,
            "advisory": f"Adhere to recommended seed rate and proper plant spacing for {crop_name}."
        }

    std_row = profile["standard_row_spacing_cm"]
    std_plant = profile["standard_plant_spacing_cm"]

    eff_row = max(5.0, float(row_spacing_cm)) if row_spacing_cm and row_spacing_cm > 0 else std_row
    eff_plant = max(2.0, float(plant_spacing_cm)) if plant_spacing_cm and plant_spacing_cm > 0 else std_plant

    # Plant population formula: 1 acre = 4,046.86 sq meters = 40,468,600 sq cm
    area_sq_cm_per_acre = 40468600.0
    plant_area_sq_cm = eff_row * eff_plant
    population_per_acre = int(area_sq_cm_per_acre / plant_area_sq_cm)
    total_population = int(population_per_acre * acres)

    # Seed rate adjustment based on germination rate and acreage
    # If germination is lower than benchmark 85%, seed quantity must be increased
    germ_factor = 85.0 / germ_pct
    base_rate = profile["base_seed_rate_kg_acre"]
    adjusted_rate_per_acre = round(base_rate * germ_factor, 2)
    total_seed_kg = round(adjusted_rate_per_acre * acres, 2)

    seed_rate_inr = profile["certified_seed_rate_per_kg_inr"]
    estimated_cost = round(total_seed_kg * seed_rate_inr, 2)

    return {
        "crop_id": crop_id,
        "crop_name": profile["crop_name"],
        "land_size_acres": acres,
        "recommended_seed_rate_kg_per_acre": adjusted_rate_per_acre,
        "total_seed_required_kg": total_seed_kg,
        "standard_row_spacing_cm": std_row,
        "standard_plant_spacing_cm": std_plant,
        "effective_row_spacing_cm": eff_row,
        "effective_plant_spacing_cm": eff_plant,
        "estimated_plant_population": total_population,
        "population_per_acre": population_per_acre,
        "sowing_depth_cm": profile["sowing_depth_cm"],
        "sowing_method": sowing_method or profile["sowing_method"],
        "seed_treatment_protocol": profile["seed_treatment_protocol"],
        "certified_seed_rate_per_kg_inr": seed_rate_inr,
        "estimated_seed_cost_inr": estimated_cost,
        "agronomic_advisory": profile["advisory"]
    }


def get_all_seed_crop_guidelines() -> List[Dict[str, Any]]:
    """Returns catalog of all seed rates, spacing and treatment guidelines."""
    res = []
    for k, v in CROP_SEED_GEOMETRY_CATALOG.items():
        res.append({
            "crop_id": k,
            "crop_name": v["crop_name"],
            "seed_rate_kg_acre": v["base_seed_rate_kg_acre"],
            "row_spacing_cm": v["standard_row_spacing_cm"],
            "plant_spacing_cm": v["standard_plant_spacing_cm"],
            "sowing_depth_cm": v["sowing_depth_cm"],
            "seed_treatment": v["seed_treatment_protocol"]
        })
    return res


# ---------------- Knapsack Sprayer & Dilution Calculator ----------------
def calculate_sprayer_dilution(
    tank_capacity_liters: float = 16.0,
    land_size_acres: float = 1.0,
    dosage_mode: str = "per_liter",
    dosage_amount: float = 2.0,
    chemical_form: str = "Liquid (ml)",
    spray_volume_liters_per_acre: float = 150.0
) -> Dict[str, Any]:
    """Calculates chemical dosage per tank, total tanks needed, and safety guidance."""
    tank_cap = max(1.0, float(tank_capacity_liters or 16.0))
    acres = max(0.05, float(land_size_acres or 1.0))
    dose = max(0.01, float(dosage_amount or 2.0))
    water_rate = max(50.0, float(spray_volume_liters_per_acre or 150.0))

    total_water = round(acres * water_rate, 1)
    tanks_needed = round(total_water / tank_cap, 1)

    unit = "ml" if "liquid" in chemical_form.lower() or "ml" in chemical_form.lower() else "grams"

    if dosage_mode == "per_acre":
        total_chem = round(dose * acres, 1)
        chem_per_tank = round(total_chem / (total_water / tank_cap), 1)
    else:  # "per_liter"
        chem_per_tank = round(dose * tank_cap, 1)
        total_chem = round(dose * total_water, 1)

    nozzle = (
        "Hollow Cone Nozzle (ideal for insecticide & fungicide canopy coverage with fine mist)"
        if "liquid" in chemical_form.lower() else
        "Flat Fan Nozzle (uniform swath width, ideal for weedicide and systemic sprays)"
    )

    safety = [
        "Wear rubber gloves, eye goggles, and a clean N95 or carbon-filter mask while measuring and pouring.",
        "Always prepare a mother solution in a 2-liter bucket before adding to the full spray tank.",
        "Never spray facing the wind; spray across or with the gentle breeze to avoid inhalation.",
        "Spray during early morning (6:30 - 9:30 AM) or late afternoon (4:00 - 6:30 PM) to prevent thermal evaporation.",
        "Keep children and livestock away from sprayed fields for at least 24 to 48 hours."
    ]

    tips = [
        f"For your {acres} acre field, prepare {tanks_needed} tanks of {tank_cap}L capacity.",
        f"Add exactly {chem_per_tank} {unit} into each {tank_cap}L tank.",
        "Maintain a steady walking speed of approx 1 pace per second with the spray lance 45 cm above crop foliage.",
        "Triple-rinse the empty pesticide container with water and pour rinse-water into the spray tank before container disposal."
    ]

    return {
        "tank_capacity_liters": tank_cap,
        "land_size_acres": acres,
        "chemical_per_tank": chem_per_tank,
        "chemical_unit": unit,
        "tanks_needed_total": tanks_needed,
        "total_spray_tanks": tanks_needed,
        "total_water_liters": total_water,
        "total_chemical_needed": total_chem,
        "total_chemical_required": total_chem,
        "total_chemical_unit": unit,
        "nozzle_recommendation": nozzle,
        "safety_checklist": safety,
        "application_tips": tips,
        "recommendations": tips + safety[:2]
    }


# ---------------- Solar Ag-Pump & PM-KUSUM Sizing Engine ----------------
def calculate_solar_pump_kusum(
    water_source: str = "Borewell",
    water_depth_feet: float = 150.0,
    land_size_acres: float = 2.0,
    irrigation_type: str = "Drip / Sprinkler",
    farmer_category: str = "Small / Marginal (< 2 Ha)",
    state: str = "All-India"
) -> Dict[str, Any]:
    """Calculates solar agricultural pump HP, solar array kW, PM-KUSUM subsidy, and diesel savings."""
    depth = max(10.0, float(water_depth_feet or 150.0))
    acres = max(0.2, float(land_size_acres or 2.0))

    # Hydraulic sizing rules
    is_surface = "canal" in water_source.lower() or "surface" in water_source.lower() or (depth <= 25.0 and "open" in water_source.lower())
    
    if is_surface:
        pump_type = "Surface Monoblock (DC / AC)"
        if acres <= 2.5:
            hp = 2.0
            kw = 1.8
            base_cost = 125000.0
        elif acres <= 5.0:
            hp = 3.0
            kw = 3.0
            base_cost = 175000.0
        else:
            hp = 5.0
            kw = 4.8
            base_cost = 250000.0
    else:
        pump_type = "Submersible DC Brushless"
        if depth <= 120.0 and acres <= 2.0:
            hp = 2.0
            kw = 2.0
            base_cost = 145000.0
        elif depth <= 220.0 and acres <= 4.0:
            hp = 3.0
            kw = 3.0
            base_cost = 195000.0
        elif depth <= 350.0 or acres <= 8.0:
            hp = 5.0
            kw = 5.0
            base_cost = 285000.0
        else:
            hp = 7.5
            kw = 7.5
            base_cost = 385000.0

    # PM-KUSUM Component B Subsidies:
    # 30% Central Subsidy + 30% to 50% State Subsidy
    central_pct = 30.0
    is_marginal = "small" in farmer_category.lower() or "marginal" in farmer_category.lower()
    state_pct = 40.0 if is_marginal else 30.0
    total_sub_pct = central_pct + state_pct
    farmer_share_pct = 100.0 - total_sub_pct

    central_sub_inr = round(base_cost * (central_pct / 100.0), 2)
    state_sub_inr = round(base_cost * (state_pct / 100.0), 2)
    farmer_share_inr = round(base_cost * (farmer_share_pct / 100.0), 2)

    # Diesel replacement economics:
    # A diesel pump uses ~1.3 L diesel/hour. Diesel = ~₹90/L. 450 irrigation hours/year.
    annual_diesel_liters = round(hp * 120.0 * min(5.0, acres), 0)
    annual_diesel_savings = round(annual_diesel_liters * 90.0, 2)
    payback_years = round(farmer_share_inr / max(1000.0, annual_diesel_savings), 1)
    tdh_meters = round(depth * 0.3048 * 1.25)
    co2_tons = round(annual_diesel_liters * 0.00268, 1)

    advisory = (
        f"A {hp} HP {pump_type} with a {kw} kWp solar panel array will reliably deliver approx "
        f"{int(hp * 22000)} to {int(hp * 35000)} liters/day under standard 5.5 sun hours. "
        f"Under PM-KUSUM Component-B, you receive a {int(total_sub_pct)}% combined government subsidy. "
        f"Farmer share of ₹{farmer_share_inr:,.0f} is eligible for low-interest bank finance via KCC with 10% down payment."
    )

    return {
        "water_source": water_source,
        "water_depth_feet": depth,
        "land_size_acres": acres,
        "recommended_pump_hp": hp,
        "recommended_solar_array_kw": kw,
        "solar_array_kwp": kw,
        "pump_type": pump_type,
        "total_dynamic_head_meters": tdh_meters,
        "total_estimated_cost_inr": base_cost,
        "estimated_total_cost": base_cost,
        "central_subsidy_inr": central_sub_inr,
        "central_subsidy": central_sub_inr,
        "state_subsidy_inr": state_sub_inr,
        "state_subsidy": state_sub_inr,
        "farmer_share_inr": farmer_share_inr,
        "farmer_share": farmer_share_inr,
        "bank_loan_available": round(base_cost * 0.30, 2),
        "subsidy_percentage_total": total_sub_pct,
        "annual_diesel_savings_inr": annual_diesel_savings,
        "annual_diesel_cost_savings_rs": annual_diesel_savings,
        "annual_diesel_saved_liters": annual_diesel_liters,
        "co2_reduction_tons_per_year": co2_tons,
        "payback_period_years": payback_years,
        "advisory_notes": advisory,
        "pm_kusum_portal": "https://pmkusum.mnre.gov.in"
    }


# ---------------- Intercropping & Companion Planting Catalog ----------------
INTERCROPPING_PAIRS_CATALOG: List[Dict[str, Any]] = [
    {
        "id": "sugarcane_mustard",
        "main_crop_id": "sugarcane",
        "main_crop_name": "Sugarcane",
        "companion_crop_id": "mustard",
        "companion_crop_name": "Mustard",
        "row_ratio": "1 : 2 (1 Cane trench : 2 Mustard rows)",
        "synergy_type": "Canopy & Temporal Space Optimization",
        "land_equivalent_ratio": 1.38,
        "nitrogen_fixation_kg_acre": 0.0,
        "weed_suppression_pct": 45.0,
        "pest_repellent_benefit": "Mustard glucosinolates suppress soil nematodes and early shoot borer in young cane.",
        "economic_advisory": "Mustard matures in 85-90 days before sugarcane forms canopy, giving early cash flow of ₹22,000 - ₹30,000/acre."
    },
    {
        "id": "sugarcane_potato",
        "main_crop_id": "sugarcane",
        "main_crop_name": "Sugarcane",
        "companion_crop_id": "potato",
        "companion_crop_name": "Potato",
        "row_ratio": "1 : 2 (Wide furrow planting)",
        "synergy_type": "Winter Season Inter-space Utilization",
        "land_equivalent_ratio": 1.42,
        "nitrogen_fixation_kg_acre": 0.0,
        "weed_suppression_pct": 60.0,
        "pest_repellent_benefit": "Dense potato foliage smothers winter weeds in slow-germinating autumn sugarcane.",
        "economic_advisory": "High net cash return of ₹45,000 - ₹65,000/acre from potato tubers within 90 days of planting."
    },
    {
        "id": "cotton_green_gram",
        "main_crop_id": "cotton",
        "main_crop_name": "Cotton",
        "companion_crop_id": "green_gram",
        "companion_crop_name": "Green Gram (Moong)",
        "row_ratio": "1 : 1 or 1 : 2 (Between cotton rows)",
        "synergy_type": "Biological Nitrogen Fixation & Weed Cover",
        "land_equivalent_ratio": 1.28,
        "nitrogen_fixation_kg_acre": 30.0,
        "weed_suppression_pct": 55.0,
        "pest_repellent_benefit": "Moong acts as a refuge for ladybird beetles and spiders that prey on early cotton aphids and jassids.",
        "economic_advisory": "Moong is harvested in 65 days yielding 2-3 quintals pulse, while contributing 30 kg soil Nitrogen for peak boll formation."
    },
    {
        "id": "cotton_soybean",
        "main_crop_id": "cotton",
        "main_crop_name": "Cotton",
        "companion_crop_id": "soybean",
        "companion_crop_name": "Soybean",
        "row_ratio": "1 : 1 or 1 : 2",
        "synergy_type": "Dual Cash & Protein Hedge",
        "land_equivalent_ratio": 1.22,
        "nitrogen_fixation_kg_acre": 35.0,
        "weed_suppression_pct": 50.0,
        "pest_repellent_benefit": "Provides microclimate humidity and reduces whitefly build-up in early cotton vegetative stages.",
        "economic_advisory": "Soybean harvests in September, providing interim working capital before first cotton picking."
    },
    {
        "id": "maize_pigeon_pea",
        "main_crop_id": "maize",
        "main_crop_name": "Maize (Corn)",
        "companion_crop_id": "pigeon_pea",
        "companion_crop_name": "Pigeon Pea (Arhar / Tur)",
        "row_ratio": "2 : 1 (2 Maize : 1 Arhar)",
        "synergy_type": "Root Depth & Temporal Growth Complementarity",
        "land_equivalent_ratio": 1.35,
        "nitrogen_fixation_kg_acre": 40.0,
        "weed_suppression_pct": 40.0,
        "pest_repellent_benefit": "Maize shields young Pigeon pea plants from wind stress and early pod borer infestation.",
        "economic_advisory": "Maize is harvested at 90 days; Pigeon pea deep taproots continue utilizing subsoil moisture through winter until 160 days."
    },
    {
        "id": "maize_cowpea",
        "main_crop_id": "maize",
        "main_crop_name": "Maize (Corn)",
        "companion_crop_id": "cowpea",
        "companion_crop_name": "Cowpea (Lobia)",
        "row_ratio": "2 : 2 (Alternate strips)",
        "synergy_type": "Erosion Control & Green Fodder Synergy",
        "land_equivalent_ratio": 1.25,
        "nitrogen_fixation_kg_acre": 35.0,
        "weed_suppression_pct": 70.0,
        "pest_repellent_benefit": "Dense spreading cowpea vine acts as living mulch, keeping soil temperature 3°C cooler.",
        "economic_advisory": "Provides continuous nutritious green fodder for farm cattle while boosting maize cob weight."
    },
    {
        "id": "wheat_mustard",
        "main_crop_id": "wheat",
        "main_crop_name": "Wheat",
        "companion_crop_id": "mustard",
        "companion_crop_name": "Mustard",
        "row_ratio": "9 : 1 (Every 10th row is Mustard)",
        "synergy_type": "Pest Trap Crop & Climate Risk Buffer",
        "land_equivalent_ratio": 1.18,
        "nitrogen_fixation_kg_acre": 0.0,
        "weed_suppression_pct": 30.0,
        "pest_repellent_benefit": "Mustard plants trap wheat aphids and attract beneficial honeybee pollinators.",
        "economic_advisory": "Traditional North Indian security system against winter frost or market price dip in wheat."
    },
    {
        "id": "wheat_chickpea",
        "main_crop_id": "wheat",
        "main_crop_name": "Wheat",
        "companion_crop_id": "chickpea",
        "companion_crop_name": "Chickpea (Gram)",
        "row_ratio": "4 : 2 (4 Wheat : 2 Gram)",
        "synergy_type": "Nitrogen Synergy in Semi-Arid Soils",
        "land_equivalent_ratio": 1.24,
        "nitrogen_fixation_kg_acre": 25.0,
        "weed_suppression_pct": 35.0,
        "pest_repellent_benefit": "Gram rhizosphere organic acids mobilize insoluble soil phosphorus for adjacent wheat roots.",
        "economic_advisory": "Cuts synthetic Urea requirement by 20% while producing high-protein pulse grains."
    },
    {
        "id": "tomato_marigold",
        "main_crop_id": "tomato",
        "main_crop_name": "Tomato",
        "companion_crop_id": "marigold",
        "companion_crop_name": "African Marigold (Genda)",
        "row_ratio": "16 : 1 or Border Trap rows",
        "synergy_type": "Biological Nematode & Borer Trap Crop",
        "land_equivalent_ratio": 1.20,
        "nitrogen_fixation_kg_acre": 0.0,
        "weed_suppression_pct": 25.0,
        "pest_repellent_benefit": "Marigold roots produce alpha-terthienyl that annihilates Root-Knot Nematodes (Meloidogyne); flowers attract fruit borer moths away from tomatoes.",
        "economic_advisory": "Marigold flowers yield 15-20 quintals/acre for festive flower markets, earning ₹30,000+ extra revenue."
    }
]


def get_intercropping_recommendations(crop_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """Returns curated companion and intercropping pairs filtered by crop if requested."""
    pairs = INTERCROPPING_PAIRS_CATALOG
    if crop_id and crop_id != "all":
        cid = crop_id.lower()
        pairs = [
            p for p in INTERCROPPING_PAIRS_CATALOG
            if p["main_crop_id"] == cid or p["companion_crop_id"] == cid
        ]
    
    enriched = []
    for p in pairs:
        item = dict(p)
        item["main_crop"] = p["main_crop_name"]
        item["companion_crop"] = p["companion_crop_name"]
        item["spatial_ratio"] = p["row_ratio"]
        item["ler"] = p["land_equivalent_ratio"]
        item["biological_benefit"] = p["pest_repellent_benefit"]
        item["recommended_season"] = "Rabi" if "wheat" in p["main_crop_id"] or "mustard" in p["main_crop_id"] or "potato" in p["companion_crop_id"] else ("All seasons" if "tomato" in p["main_crop_id"] else "Kharif")
        item["water_compatibility"] = "Drip / Conserved moisture"
        enriched.append(item)
    return enriched


# ---------------- Post-Harvest Grain Storage & Moisture Engine ----------------
GRAIN_STORAGE_CATALOG: Dict[str, Dict[str, Any]] = {
    "wheat": {
        "crop_name": "Wheat (गेहूं)",
        "safe_moisture_limit_pct": 12.0,
        "max_shelf_life_months": 12,
        "common_storage_pests": ["Khapra Beetle (Trogoderma granarium)", "Rice Weevil (Sitophilus oryzae)", "Lesser Grain Borer"],
        "natural_protectants": [
            "Mix 1.5 kg clean, shade-dried Neem leaves per 100 kg grain.",
            "Apply a 2-cm dry inert wood ash layer at the top of grain bins.",
            "Sun-dry grain on tarpaulins for 6 hours before packing."
        ],
        "stacking_and_storage_guidelines": "Stack bags on wooden pallets 15 cm above ground and 45 cm away from damp walls to prevent capillary moisture seepage."
    },
    "rice": {
        "crop_name": "Paddy / Rice (धान / चावल)",
        "safe_moisture_limit_pct": 13.0,
        "max_shelf_life_months": 10,
        "common_storage_pests": ["Angoumois Grain Moth (Sitotroga cerealella)", "Rice Weevil", "Rust Red Flour Beetle"],
        "natural_protectants": [
            "Mix dried mint (Pudina) or Nirgundi leaves at 2% weight in storage bags.",
            "Store in hermetic multi-layer HDPE SuperGrain bags to suffocate insects organically."
        ],
        "stacking_and_storage_guidelines": "Maintain bag moisture strictly below 13.5% to avoid yellowing of kernels and yellow fungal mold."
    },
    "maize": {
        "crop_name": "Maize / Corn (मक्का)",
        "safe_moisture_limit_pct": 13.0,
        "max_shelf_life_months": 8,
        "common_storage_pests": ["Maize Weevil (Sitophilus zeamais)", "Larger Grain Borer", "Aspergillus flavus"],
        "natural_protectants": [
            "Sun dry shelled kernels in thin layers (3-4 cm) turning every 2 hours.",
            "Mix coarse wood ash at 3% weight for seed maize storage."
        ],
        "stacking_and_storage_guidelines": "Maize is highly susceptible to Aflatoxin mold if moisture exceeds 14%. Must be dry and ventilated."
    },
    "pearl_millet": {
        "crop_name": "Pearl Millet / Bajra (बाजरा)",
        "safe_moisture_limit_pct": 11.0,
        "max_shelf_life_months": 9,
        "common_storage_pests": ["Tribolium castaneum (Flour beetle)", "Grain moth"],
        "natural_protectants": [
            "Store in traditional mud-silos (kothi) sealed with cow-dung and clay plaster.",
            "Place dried camphor (Karpur) cubes in cloth pouches in storage bins."
        ],
        "stacking_and_storage_guidelines": "Bajra fat oxidizes quickly if moist, leading to bitterness and rancidity within 60 days."
    },
    "chickpea": {
        "crop_name": "Chickpea / Chana (चना)",
        "safe_moisture_limit_pct": 9.5,
        "max_shelf_life_months": 12,
        "common_storage_pests": ["Pulse Beetle / Dhora (Callosobruchus chinensis)"],
        "natural_protectants": [
            "Coat seeds with 250 ml Castor oil or Mustard oil per 100 kg pulse. The oil film asphyxiates beetle eggs without affecting germination.",
            "Mix dry turmeric powder (Haldi) @ 200g/quintal as an organic disinfectant."
        ],
        "stacking_and_storage_guidelines": "Keep in airtight containers. Pulse beetle attacks start from the field and multiply rapidly in warm bins."
    },
    "pigeon_pea": {
        "crop_name": "Pigeon Pea / Arhar (तुअर / अरहर)",
        "safe_moisture_limit_pct": 10.0,
        "max_shelf_life_months": 12,
        "common_storage_pests": ["Pulse Beetle (Callosobruchus maculatus)"],
        "natural_protectants": [
            "Mix edible vegetable oil (Castor / Sesame) at 3 ml/kg seed.",
            "Hermetic bag sealing creates high CO2 environment, killing all stages of Dhora beetles in 14 days."
        ],
        "stacking_and_storage_guidelines": "Dry pods thoroughly before threshing. Store split dal in clean metal bins with tight lids."
    },
    "mustard": {
        "crop_name": "Mustard / Rapeseed (सरसों)",
        "safe_moisture_limit_pct": 8.0,
        "max_shelf_life_months": 10,
        "common_storage_pests": ["Oryzaephilus surinamensis (Saw-toothed beetle)", "Mold"],
        "natural_protectants": [
            "Sun dry seeds for 3 consecutive days until moisture is below 8%.",
            "Store in new or formalin-disinfected gunny bags."
        ],
        "stacking_and_storage_guidelines": "Oilseed moisture above 9% triggers enzyme lipolysis, turning seed oil dark and acidic."
    },
    "soybean": {
        "crop_name": "Soybean (सोयाबीन)",
        "safe_moisture_limit_pct": 10.0,
        "max_shelf_life_months": 8,
        "common_storage_pests": ["Bruchid beetles", "Fungal rot"],
        "natural_protectants": [
            "Handle gently to prevent mechanical damage to seed coat.",
            "Do not stack more than 5-6 bags high to prevent crushing and pressure heating."
        ],
        "stacking_and_storage_guidelines": "Soybean seed viability drops rapidly in hot storage. Maintain cool (below 25°C) shaded storage."
    }
}


def get_grain_storage_catalog_list() -> List[Dict[str, Any]]:
    """Returns storage guidelines for all crops."""
    res = []
    for k, v in GRAIN_STORAGE_CATALOG.items():
        pests_str = ", ".join(v.get("common_storage_pests", []))
        practices_str = " ".join(v.get("natural_protectants", []))
        res.append({
            "crop_id": k,
            "crop_name": v["crop_name"],
            "crop": v["crop_name"],
            "safe_moisture_limit_pct": v["safe_moisture_limit_pct"],
            "safe_moisture_pct": v["safe_moisture_limit_pct"],
            "max_shelf_life_months": v["max_shelf_life_months"],
            "max_safe_duration_months": v["max_shelf_life_months"],
            "common_storage_pests": v["common_storage_pests"],
            "major_pests": pests_str,
            "natural_protectants": v["natural_protectants"],
            "safe_practices": practices_str,
            "stacking_and_storage_guidelines": v["stacking_and_storage_guidelines"]
        })
    return res


def evaluate_grain_storage_risk(
    crop_id: str = "wheat",
    measured_moisture_pct: float = 12.0,
    storage_method: str = "Jute Gunny Bags",
    intended_duration_months: int = 6
) -> Dict[str, Any]:
    """Evaluates grain moisture, assigns risk tier, and prescribes sun-drying and preservation steps."""
    cid = (crop_id or "wheat").lower().strip()
    profile = GRAIN_STORAGE_CATALOG.get(cid)
    if not profile:
        for k, v in GRAIN_STORAGE_CATALOG.items():
            k_lower = k.lower()
            v_name_lower = v["crop_name"].lower()
            if (k_lower in cid or cid in k_lower or 
                any(token in cid for token in k_lower.split("_")) or
                any(token in v_name_lower for token in cid.split() if len(token) > 2)):
                profile = v
                cid = k
                break
    if not profile:
        profile = {
            "crop_name": cid.title(),
            "safe_moisture_limit_pct": 11.0,
            "max_shelf_life_months": 8,
            "common_storage_pests": ["Storage weevils", "Grain moths"],
            "natural_protectants": ["Sun-dry thoroughly", "Mix dry neem leaves @ 1.5 kg/quintal"],
            "stacking_and_storage_guidelines": "Keep on wooden dunnage in dry ventilated area."
        }

    safe_limit = profile["safe_moisture_limit_pct"]
    moisture = max(4.0, min(30.0, float(measured_moisture_pct or 12.0)))
    diff = moisture - safe_limit

    if diff <= 0:
        risk_level = "Safe / Green (Surakshit)"
        explanation = (
            f"Your measured moisture of {moisture}% is at or below the safe ceiling ({safe_limit}%). "
            f"Grain is in prime condition for long-term storage (up to {intended_duration_months} months) with negligible risk of fungus."
        )
        drying_hours = 0.0
    elif diff <= 2.5:
        risk_level = "Moderate Risk / Yellow (Madhyam Khatra)"
        explanation = (
            f"Moisture ({moisture}%) exceeds the safe threshold by {round(diff, 1)}%. "
            "Storage weevils and latent fungal spores will become active within 30-45 days, causing grain heating and weight loss."
        )
        drying_hours = round(diff * 3.0, 1)
    else:
        risk_level = "Critical Spoilage / Red (Gambhir Khatra)"
        explanation = (
            f"DANGER: Moisture ({moisture}%) is dangerously high (+{round(diff, 1)}% above safe limit). "
            "High risk of Aspergillus aflatoxins, bag caking, and complete germination failure. Immediate action required!"
        )
        drying_hours = round(diff * 4.0, 1)

    enwr_benefit = (
        "Deposit safe grain in WDRA-registered warehouses to get an electronic Negotiable Warehouse Receipt (e-NWR). "
        "You can pledge the e-NWR with public banks for a 70% advance loan at subsidized 7% interest, avoiding post-harvest distress sales!"
    )

    action_plan = []
    if drying_hours > 0:
        action_plan.append(f"Spread grain on clean tarpaulin for intensive sun-drying (approx {drying_hours} total hours across sunny days).")
    else:
        action_plan.append("Grain moisture is within safe physiological thresholds for storage.")
    action_plan.extend(profile["natural_protectants"])
    action_plan.append(profile["stacking_and_storage_guidelines"])

    return {
        "crop_id": cid,
        "crop_name": profile["crop_name"],
        "measured_moisture_pct": moisture,
        "current_moisture_pct": moisture,
        "safe_moisture_limit_pct": safe_limit,
        "safe_moisture_pct": safe_limit,
        "risk_level": risk_level,
        "risk_explanation": explanation,
        "sun_drying_hours_needed": drying_hours,
        "traditional_preservation_tips": profile["natural_protectants"],
        "enwr_warehouse_pledge_benefit": enwr_benefit,
        "spoilage_warnings": [explanation],
        "drying_action_plan": action_plan
    }


# =======================================================================
# 1. Livestock & Dairy Advisory Logic
# =======================================================================
def calculate_livestock_ration(
    animal_type: str = "Cow (Crossbred HF/Jersey)",
    body_weight_kg: float = 400.0,
    daily_milk_liters: float = 10.0,
    milk_fat_pct: float = 4.0,
    pregnancy_stage: str = "None"
) -> Dict[str, Any]:
    wt = max(15.0, body_weight_kg)
    milk = max(0.0, daily_milk_liters)
    fat = max(2.5, milk_fat_pct or 4.0)
    anim_lower = animal_type.lower()

    if "goat" in anim_lower:
        dm_pct = 0.038
        maint_concentrate = 0.15
        conc_per_liter = 0.35
        mineral_mix = 15.0
        salt = 10.0
        water_base = 6.0 + (milk * 1.5)
    elif "buffalo" in anim_lower:
        dm_pct = 0.030
        maint_concentrate = 1.5
        conc_per_liter = 0.50
        mineral_mix = 55.0
        salt = 35.0
        water_base = 50.0 + (milk * 3.5)
    elif "desi" in anim_lower or "indigenous" in anim_lower:
        dm_pct = 0.026
        maint_concentrate = 1.0
        conc_per_liter = 0.40
        mineral_mix = 50.0
        salt = 30.0
        water_base = 40.0 + (milk * 3.0)
    else:
        dm_pct = 0.030
        maint_concentrate = 1.2
        conc_per_liter = 0.38
        mineral_mix = 50.0
        salt = 30.0
        water_base = 45.0 + (milk * 3.2)

    total_dm = round(wt * dm_pct, 2)
    preg_conc = 1.25 if "last" in pregnancy_stage.lower() or "advance" in pregnancy_stage.lower() else (0.5 if "early" in pregnancy_stage.lower() or "mid" in pregnancy_stage.lower() else 0.0)

    concentrate_kg = round(maint_concentrate + (milk * conc_per_liter) + preg_conc, 2)
    conc_dm = concentrate_kg * 0.90
    remaining_dm = max(1.0, total_dm - conc_dm)

    green_dm = remaining_dm * 0.65
    dry_dm = remaining_dm * 0.35

    green_fodder_fresh_kg = round(green_dm / 0.20, 1)
    dry_straw_fresh_kg = round(dry_dm / 0.90, 1)

    daily_cost = round((green_fodder_fresh_kg * 2.0) + (dry_straw_fresh_kg * 6.0) + (concentrate_kg * 28.0) + 5.0, 1)

    tips = [
        "Chaff (Kutti) all green and dry fodder to 1-2 inch pieces to reduce feed wastage by 20-30%.",
        "Offer clean, fresh drinking water ad-libitum at least 3-4 times a day (clean water boosts milk yield by 10%).",
        "Mix 50g area-specific mineral mixture and 30g iodized salt in concentrate daily to ensure regular heat cycles.",
        "Provide leguminous green fodder (Berseem/Lucerne) alongside cereal fodder (Napier/Maize) for optimal crude protein."
    ]
    if "last" in pregnancy_stage.lower():
        tips.append("Advance pregnancy: Avoid sudden feed changes, provide comfortable dry bedding, and supplement with Calcium boosters.")

    return {
        "animal_type": animal_type,
        "body_weight_kg": wt,
        "daily_milk_liters": milk,
        "dry_matter_requirement_kg": total_dm,
        "green_fodder_kg": green_fodder_fresh_kg,
        "dry_straw_bhusa_kg": dry_straw_fresh_kg,
        "concentrate_feed_kg": concentrate_kg,
        "mineral_mixture_grams": mineral_mix,
        "salt_grams": salt,
        "water_requirement_liters": round(water_base, 1),
        "estimated_daily_feed_cost_inr": daily_cost,
        "feeding_tips": tips
    }


def calculate_gestation_calendar(animal_type: str, insemination_date: str) -> Dict[str, Any]:
    try:
        s_date = datetime.strptime(insemination_date.strip(), "%Y-%m-%d").date()
    except Exception:
        s_date = date.today()

    anim_lower = animal_type.lower()
    if "buffalo" in anim_lower:
        gestation_days = 310
        species = "Buffalo"
    elif "goat" in anim_lower:
        gestation_days = 150
        species = "Goat"
    else:
        gestation_days = 280
        species = "Cow"

    heat_check_date = s_date + timedelta(days=21)
    pd_date = s_date + timedelta(days=60 if species != "Goat" else 45)
    dry_off_days = 210 if species == "Buffalo" else (180 if species == "Cow" else 100)
    dry_off_date = s_date + timedelta(days=dry_off_days)
    calving_date = s_date + timedelta(days=gestation_days)
    steaming_up_days = gestation_days - 30
    steaming_date = s_date + timedelta(days=steaming_up_days)

    milestones = [
        {
            "days_after_insemination": 21,
            "milestone_date": heat_check_date.strftime("%Y-%m-%d"),
            "title": "First Heat Check (1st Estrus Cycle)",
            "action_notes": "Carefully observe the animal at morning and evening for signs of repeat heat (mucus discharge, bellowing). If observed in heat, re-inseminate immediately."
        },
        {
            "days_after_insemination": 60 if species != "Goat" else 45,
            "milestone_date": pd_date.strftime("%Y-%m-%d"),
            "title": "Veterinary Pregnancy Diagnosis (PD)",
            "action_notes": "Have a certified veterinarian or livestock assistant perform rectal palpation or ultrasound to confirm successful conception."
        },
        {
            "days_after_insemination": dry_off_days,
            "milestone_date": dry_off_date.strftime("%Y-%m-%d"),
            "title": "Drying-Off Milestone",
            "action_notes": "Gradually cease milking to allow the mammary glands to regenerate and build colostrum for the upcoming calf. Apply dry cow intramammary antibiotic infusion if needed."
        },
        {
            "days_after_insemination": steaming_up_days,
            "milestone_date": steaming_date.strftime("%Y-%m-%d"),
            "title": "Steaming-Up & Transition Feeding",
            "action_notes": "Increase concentrate feed by +1.5 kg/day. Provide Vitamin AD3E and anionic mineral salts to prevent hypocalcemia (milk fever) post-calving."
        },
        {
            "days_after_insemination": gestation_days,
            "milestone_date": calving_date.strftime("%Y-%m-%d"),
            "title": f"Expected Calving / Delivery Date ({species})",
            "action_notes": "Prepare a clean, sanitized, straw-bedded maternity stall. Feed lukewarm colostrum (10% of body weight) to the newborn calf within 1 hour of delivery."
        }
    ]

    return {
        "animal_type": animal_type,
        "insemination_date": s_date.strftime("%Y-%m-%d"),
        "gestation_period_days": gestation_days,
        "heat_check_date_21d": heat_check_date.strftime("%Y-%m-%d"),
        "pregnancy_diagnosis_date_60d": pd_date.strftime("%Y-%m-%d"),
        "dry_off_date": dry_off_date.strftime("%Y-%m-%d"),
        "expected_calving_date": calving_date.strftime("%Y-%m-%d"),
        "milestones": milestones,
        "advisory_notes": f"Standard gestation period for {species} is {gestation_days} days. Expected delivery date: {calving_date.strftime('%d %B %Y')}."
    }


def get_livestock_evm_remedies() -> List[Dict[str, Any]]:
    return [
        {
            "id": "mastitis",
            "condition": "Sub-clinical & Clinical Mastitis (थनैला रोग / Udder Swelling)",
            "symptoms": ["Swollen, hot, painful udder", "Yellowish, curd-like or watery milk clots", "Cow resists milking"],
            "evm_formulation_name": "NDDB Haldi-Ghritkumari Lep (Turmeric-Aloe Udder Paste)",
            "ingredients": ["Fresh Aloe Vera leaf: 250 g", "Turmeric rhizome/powder: 50 g", "Slaked Lime (Chuna): 15 g"],
            "preparation_method": "Grind Aloe Vera, Turmeric, and Chuna into a smooth reddish-yellow paste. Dilute slightly with clean water to spreadable consistency.",
            "dosage_and_application": "Milk out the affected quarter completely. Wash udder with clean water, dry, and apply paste generously over the entire udder 3-4 times daily for 5 consecutive days.",
            "prevention_guidelines": "Dip teats in 0.5% povidone-iodine after every milking. Never allow cattle to lie down on wet mud for 30 minutes after milking."
        },
        {
            "id": "bloat",
            "condition": "Bloat & Ruminal Tympany (अफारा / Pet Phulna)",
            "symptoms": ["Tense, drum-like swollen left flank", "Difficulty breathing, open mouth panting", "Restlessness and kicking at belly"],
            "evm_formulation_name": "Sarson Tel-Hing Kadha (Mustard-Asafoetida Drench)",
            "ingredients": ["Pure Mustard Oil: 100-150 ml", "Asafoetida (Hing): 10 g", "Garlic (Lahsun): 50 g", "Ginger (Adrak): 50 g", "Black salt: 25 g"],
            "preparation_method": "Crush garlic and ginger into paste. Dissolve hing and black salt in lukewarm water (250 ml), then mix thoroughly with mustard oil.",
            "dosage_and_application": "Drench orally slowly using a clean bottle. Keep animal's head elevated. Massage the left flank upward. Repeat in 4 hours if gas is not released.",
            "prevention_guidelines": "Never feed excessively wet, dew-covered young legume fodder (Berseem/Lucerne) on an empty stomach. Always feed dry bhusa first."
        },
        {
            "id": "fmd_mouth_foot",
            "condition": "Foot & Mouth Disease (FMD) Lesions (खुरपका-मुंहपका छाले)",
            "symptoms": ["Painful blisters/sores on tongue and gums", "Excessive frothy salivation", "Lameness and wounds between hooves"],
            "evm_formulation_name": "Neem-Haldi Ghee Balm (Ethno-Veterinary Antiseptic)",
            "ingredients": ["Turmeric powder: 50 g", "Neem oil or boiled neem leaf paste: 100 ml", "Pure desi ghee or coconut oil: 50 g", "Camphor (Kapur): 5 g"],
            "preparation_method": "Warm ghee/neem oil lightly and blend in turmeric powder and crushed camphor to create an antibacterial antiseptic balm.",
            "dosage_and_application": "Wash mouth ulcers with mild baking soda or alum water. Apply the soothing balm gently onto tongue and hoof fissures twice daily.",
            "prevention_guidelines": "Get cattle vaccinated bi-annually under the National Animal Disease Control Programme (NADCP). Quarantine infected animals."
        },
        {
            "id": "diarrhea_scours",
            "condition": "Calf Scours & Simple Diarrhea (दस्त / Calf Diarrhea)",
            "symptoms": ["Watery profuse feces", "Sunken eyes, weakness, dehydration", "Rough hair coat"],
            "evm_formulation_name": "Methi-Dahi Rehydration Paste (Fenugreek-Curd Electuary)",
            "ingredients": ["Fenugreek seeds (Methi): 50 g", "Pomegranate rind powder: 25 g", "Fresh Curd/Buttermilk: 200 ml", "Common salt: 5 g", "Jaggery: 50 g"],
            "preparation_method": "Roast fenugreek seeds slightly, powder finely, and blend into buttermilk with pomegranate rind and jaggery.",
            "dosage_and_application": "Administer orally twice daily for 2-3 days. Supplement with Oral Rehydration Solution (clean water + sugar + salt) to maintain hydration.",
            "prevention_guidelines": "Feed maternal colostrum within the first hour of birth. Keep calf pens dry and bedded with clean straw."
        },
        {
            "id": "deworming",
            "condition": "Internal Parasites & Worms (पेट के कीड़े / Helminthiasis)",
            "symptoms": ["Pot belly in calves", "Dull coat, emaciation despite feeding", "Diarrhea or bottle jaw swelling under chin"],
            "evm_formulation_name": "Kaduwa Neem-Nirgundi Dewormer (Botanical Anthelmintic)",
            "ingredients": ["Neem leaves (Azadirachta indica): 100 g", "Nirgundi leaves: 50 g", "Karela / Bitter gourd pulp: 50 g", "Jaggery: 50 g"],
            "preparation_method": "Pound leaves into a thick paste with jaggery to form a sweet-bitter bolus.",
            "dosage_and_application": "Feed orally in morning on an empty stomach once a month.",
            "prevention_guidelines": "Rotate pastures and avoid grazing on marshy waterlogged riverbanks where snail hosts thrive."
        }
    ]


# =======================================================================
# 2. Mandi Distance & Profit Arbitrage Logic
# =======================================================================
def calculate_mandi_arbitrage(
    crop_id: str,
    quantity_quintals: float,
    local_mandi_name: str,
    local_mandi_price: float,
    local_mandi_distance_km: float,
    distant_mandi_name: str,
    distant_mandi_price: float,
    distant_mandi_distance_km: float,
    vehicle_type: str = "Tractor Trolley",
    diesel_price_per_liter: float = 90.0
) -> Dict[str, Any]:
    qty = max(0.5, quantity_quintals)
    local_p = max(100.0, local_mandi_price)
    dist_p = max(100.0, distant_mandi_price)
    local_d = max(1.0, local_mandi_distance_km)
    dist_d = max(1.0, distant_mandi_distance_km)
    fuel_p = max(50.0, diesel_price_per_liter)

    v_lower = vehicle_type.lower()
    if "tractor" in v_lower:
        mileage = 4.0
        loading_unloading = 400.0
        mandi_cess_pct = 0.01
    elif "pickup" in v_lower or "bolero" in v_lower or "ace" in v_lower:
        mileage = 9.0
        loading_unloading = 300.0
        mandi_cess_pct = 0.01
    elif "loader" in v_lower or "3-wheeler" in v_lower or "auto" in v_lower:
        mileage = 18.0
        loading_unloading = 200.0
        mandi_cess_pct = 0.01
    else:
        mileage = 3.5
        loading_unloading = 800.0
        mandi_cess_pct = 0.01

    local_rt_km = round(local_d * 2.0, 1)
    local_fuel_liters = round(local_rt_km / mileage, 1)
    local_fuel_cost = local_fuel_liters * fuel_p
    local_mandi_fee = (qty * local_p) * mandi_cess_pct
    local_transport_total = round(local_fuel_cost + (loading_unloading * 0.5) + local_mandi_fee, 0)
    local_gross = round(qty * local_p, 0)
    local_net = round(local_gross - local_transport_total, 0)

    dist_rt_km = round(dist_d * 2.0, 1)
    dist_fuel_liters = round(dist_rt_km / mileage, 1)
    dist_fuel_cost = dist_fuel_liters * fuel_p
    dist_mandi_fee = (qty * dist_p) * mandi_cess_pct
    toll_charges = 100.0 if dist_d > 35.0 else 0.0
    distant_transport_total = round(dist_fuel_cost + loading_unloading + dist_mandi_fee + toll_charges, 0)
    distant_gross = round(qty * dist_p, 0)
    distant_net = round(distant_gross - distant_transport_total, 0)

    net_diff = round(distant_net - local_net, 0)
    is_worth_it = net_diff > 0

    break_even_p = round((local_net + distant_transport_total) / qty, 1)

    if is_worth_it:
        rec = (
            f"✅ GO TO DISTANT MANDI: You will earn an extra net in-hand profit of ₹{net_diff:,.0f} "
            f"after accounting for ₹{distant_transport_total:,.0f} in round-trip diesel ({dist_fuel_liters} L) and transport."
        )
    else:
        rec = (
            f"🛑 SELL LOCALLY: Distant price appears higher by ₹{round(dist_p - local_p, 0)}/quintal, "
            f"but diesel, tolls, and transport will cause a NET LOSS of ₹{abs(net_diff):,.0f}! "
            f"Distant mandi rate must be at least ₹{break_even_p:,.0f}/quintal to be worthwhile."
        )

    return {
        "crop_id": crop_id,
        "quantity_quintals": qty,
        "local_gross_revenue": local_gross,
        "local_transport_cost": local_transport_total,
        "local_net_revenue": local_net,
        "distant_gross_revenue": distant_gross,
        "distant_transport_cost": distant_transport_total,
        "distant_net_revenue": distant_net,
        "net_profit_difference": net_diff,
        "is_distant_mandi_worth_it": is_worth_it,
        "break_even_price_per_quintal": break_even_p,
        "recommendation": rec,
        "round_trip_km_distant": dist_rt_km,
        "fuel_liters_consumed_distant": dist_fuel_liters
    }


# =======================================================================
# 3. Soil Health Card Micronutrient Doctor Logic
# =======================================================================
def calculate_micronutrient_prescription(
    crop_id: Optional[str] = "wheat",
    land_size_acres: float = 1.0,
    zinc_ppm: Optional[float] = None,
    iron_ppm: Optional[float] = None,
    sulfur_ppm: Optional[float] = None,
    boron_ppm: Optional[float] = None,
    organic_carbon_pct: Optional[float] = None
) -> Dict[str, Any]:
    acres = max(0.1, land_size_acres)
    cid = (crop_id or "wheat").lower()
    prescriptions: List[Dict[str, Any]] = []
    total_cost = 0.0

    # 1. Zinc (Zn) - Critical threshold 0.6 ppm
    zn_val = zinc_ppm if zinc_ppm is not None else 0.45
    if zn_val < 0.6:
        status = "Critical Deficient" if zn_val < 0.4 else "Low / Deficient"
        dosage_acre = 10.0
        tot_kg = round(dosage_acre * acres, 1)
        cost = round(tot_kg * 45.0, 0)
        total_cost += cost
        prescriptions.append({
            "nutrient": "Zinc (Zn)",
            "soil_status": status,
            "measured_value": zn_val,
            "critical_threshold": "0.60 ppm (DTPA extractable)",
            "recommended_fertilizer": "Zinc Sulfate Heptahydrate (ZnSO4 21% Zn)",
            "dosage_kg_per_acre": dosage_acre,
            "total_dosage_kg": tot_kg,
            "application_method": "Broadcast as basal dose before final plowing. DO NOT mix directly with DAP to avoid Zinc Phosphate precipitation.",
            "visual_deficiency_symptom": "Khaira disease in paddy (rusty brown patches on middle leaves); white bud in maize; bleached interveinal bands in wheat."
        })
    else:
        prescriptions.append({
            "nutrient": "Zinc (Zn)",
            "soil_status": "Optimal / Sufficient",
            "measured_value": zn_val,
            "critical_threshold": "0.60 ppm",
            "recommended_fertilizer": "Maintenance baseline (optional)",
            "dosage_kg_per_acre": 0.0,
            "total_dosage_kg": 0.0,
            "application_method": "Soil Zinc is sufficient. No chemical application required this season.",
            "visual_deficiency_symptom": "Healthy green canopy with normal leaf expansion."
        })

    # 2. Sulfur (S) - Critical threshold 10.0 ppm
    s_val = sulfur_ppm if sulfur_ppm is not None else 8.0
    if s_val < 10.0:
        status = "Critical Deficient" if s_val < 6.0 else "Low / Deficient"
        dosage_acre = 12.0 if any(k in cid for k in ["mustard", "groundnut", "soybean", "sunflower", "sesame", "gram", "pigeonpea", "lentil"]) else 8.0
        tot_kg = round(dosage_acre * acres, 1)
        cost = round(tot_kg * 38.0, 0)
        total_cost += cost
        prescriptions.append({
            "nutrient": "Sulfur (S)",
            "soil_status": status,
            "measured_value": s_val,
            "critical_threshold": "10.0 ppm (Available Sulfate-S)",
            "recommended_fertilizer": "Agricultural Bentonite Sulfur (90% S) or Gypsum",
            "dosage_kg_per_acre": dosage_acre,
            "total_dosage_kg": tot_kg,
            "application_method": "Broadcast at sowing. In alkaline soils, agricultural Gypsum (50 kg/acre) also provides available calcium and sulfur.",
            "visual_deficiency_symptom": "Uniform chlorosis (pale yellowing) appearing first on young top leaves; lower seed oil content."
        })
    else:
        prescriptions.append({
            "nutrient": "Sulfur (S)",
            "soil_status": "Optimal / Sufficient",
            "measured_value": s_val,
            "critical_threshold": "10.0 ppm",
            "recommended_fertilizer": "None required",
            "dosage_kg_per_acre": 0.0,
            "total_dosage_kg": 0.0,
            "application_method": "Soil Sulfur level is adequate.",
            "visual_deficiency_symptom": "Normal protein synthesis and oil yield."
        })

    # 3. Boron (B) - Critical threshold 0.5 ppm
    b_val = boron_ppm if boron_ppm is not None else 0.35
    if b_val < 0.5:
        status = "Low / Deficient"
        dosage_acre = 1.5
        tot_kg = round(dosage_acre * acres, 1)
        cost = round(tot_kg * 120.0, 0)
        total_cost += cost
        prescriptions.append({
            "nutrient": "Boron (B)",
            "soil_status": status,
            "measured_value": b_val,
            "critical_threshold": "0.50 ppm (Hot water extractable)",
            "recommended_fertilizer": "Agricultural Borax (10.5% B) or Disodium Octaborate",
            "dosage_kg_per_acre": dosage_acre,
            "total_dosage_kg": tot_kg,
            "application_method": "Soil application with sand/FYM at sowing, or 2 foliar sprays of Solubor (0.1% = 1g/L) before flowering.",
            "visual_deficiency_symptom": "Hollow heart in cauliflower; fruit cracking in tomato; poor pollen viability and seed setting in mustard/sunflower."
        })
    else:
        prescriptions.append({
            "nutrient": "Boron (B)",
            "soil_status": "Optimal / Sufficient",
            "measured_value": b_val,
            "critical_threshold": "0.50 ppm",
            "recommended_fertilizer": "None required",
            "dosage_kg_per_acre": 0.0,
            "total_dosage_kg": 0.0,
            "application_method": "Boron is sufficient. Avoid over-application as the safety margin is narrow.",
            "visual_deficiency_symptom": "Normal flowering and fruit/pod set."
        })

    # 4. Iron (Fe) - Critical threshold 4.5 ppm
    fe_val = iron_ppm if iron_ppm is not None else 3.8
    if fe_val < 4.5:
        dosage_acre = 8.0
        tot_kg = round(dosage_acre * acres, 1)
        cost = round(tot_kg * 30.0, 0)
        total_cost += cost
        prescriptions.append({
            "nutrient": "Iron (Fe)",
            "soil_status": "Low / Deficient",
            "measured_value": fe_val,
            "critical_threshold": "4.50 ppm (DTPA extractable)",
            "recommended_fertilizer": "Ferrous Sulfate (FeSO4 19% Fe)",
            "dosage_kg_per_acre": dosage_acre,
            "total_dosage_kg": tot_kg,
            "application_method": "Foliar spray recommended: Dissolve 0.5% FeSO4 (5g/L) + 0.1% Citric Acid (1g/L) in water and spray at 30-40 days.",
            "visual_deficiency_symptom": "Interveinal chlorosis on young emerging leaves; veins remain sharply dark green while leaf blades turn ivory yellow."
        })

    # 5. Organic Carbon (OC %)
    oc_val = organic_carbon_pct if organic_carbon_pct is not None else 0.42
    if oc_val < 0.5:
        fym_tons = round(2.5 * acres, 1)
        organic_advice = (
            f"CRITICAL: Soil Organic Carbon is low ({oc_val:.2f}% < 0.50%). Soil biological activity and nutrient retention are depressed. "
            f"Incorporate {fym_tons} Tons of well-rotted Farm Yard Manure (FYM) or 1.0 Ton Vermicompost before sowing. "
            "Adopt green manuring with Dhaincha (Sesbania) or Sunnhemp during summer."
        )
    elif oc_val < 0.75:
        fym_tons = round(1.5 * acres, 1)
        organic_advice = (
            f"MODERATE: Soil Organic Carbon is {oc_val:.2f}%. Maintain humus by applying {fym_tons} Tons FYM per acre "
            "and avoiding burning crop residues."
        )
    else:
        organic_advice = (
            f"EXCELLENT: Soil Organic Carbon is high ({oc_val:.2f}% >= 0.75%). Strong microbial diversity, cation exchange, and soil moisture buffering."
        )

    foliar_sprays = [
        "Zinc Emergency Spray: Dissolve 500g ZnSO4 (21%) + 250g unslaked Lime in 100 Liters of water per acre. Spray at 30 & 45 days after sowing.",
        "Boron Foliar Spray: Dissolve 100g to 150g Solubor (20% B) in 100 Liters of water per acre during vegetative and pre-flowering stage.",
        "Iron Emergency Spray: Dissolve 500g FeSO4 + 100g Citric Acid in 100 Liters of water per acre for rapid recovery from chlorosis."
    ]

    return {
        "land_size_acres": acres,
        "crop_id": cid,
        "prescriptions": prescriptions,
        "organic_manure_advice": organic_advice,
        "foliar_spray_options": foliar_sprays,
        "approx_total_cost_inr": total_cost
    }


# =======================================================================
# 4. Farm Pond (Khet Talab) & Rainwater Sizer Logic
# =======================================================================
def calculate_farm_pond_sizing(
    catchment_acres: float = 5.0,
    annual_rainfall_mm: float = 800.0,
    catchment_soil_type: str = "Loam",
    supplementary_irrigation_acres: float = 2.0,
    dry_spell_days_target: int = 30
) -> Dict[str, Any]:
    acres = max(0.5, catchment_acres)
    rain_mm = max(200.0, annual_rainfall_mm)
    irrig_acres = max(0.5, min(supplementary_irrigation_acres, acres))
    soil_lower = catchment_soil_type.lower()

    if "clay" in soil_lower:
        c_runoff = 0.32
    elif "sandy" in soil_lower:
        c_runoff = 0.15
    else:
        c_runoff = 0.22

    catchment_sqm = acres * 4046.86
    runoff_cu_m = catchment_sqm * (rain_mm / 1000.0) * c_runoff

    req_cu_m = irrig_acres * 4046.86 * 0.05 * 2.0
    target_capacity_cu_m = round(min(runoff_cu_m * 0.6, max(300.0, req_cu_m)), 0)

    depth = 3.0
    slope = 1.5
    top_area_approx = target_capacity_cu_m / (depth * 0.75)
    top_w = round(math.sqrt(top_area_approx / 1.3), 1)
    top_l = round(top_w * 1.3, 1)

    bottom_l = round(max(5.0, top_l - (2 * slope * depth)), 1)
    bottom_w = round(max(4.0, top_w - (2 * slope * depth)), 1)

    a_top = top_l * top_w
    a_bot = bottom_l * bottom_w
    a_mid = ((top_l + bottom_l) / 2.0) * ((top_w + bottom_w) / 2.0)
    actual_volume_cu_m = round((depth / 6.0) * (a_top + a_bot + 4 * a_mid), 0)
    storage_liters = round(actual_volume_cu_m * 1000.0, 0)
    storage_lakh_liters = round(storage_liters / 100000.0, 2)

    slant_height = math.sqrt((depth ** 2) + ((depth * slope) ** 2))
    lining_area_sqm = round(a_bot + (2 * (top_l + bottom_l) / 2.0 * slant_height) + (2 * (top_w + bottom_w) / 2.0 * slant_height) + ((2 * (top_l + top_w)) * 1.0), 0)

    earthwork_cost = round(actual_volume_cu_m * 65.0, 0)
    hdpe_cost = round(lining_area_sqm * 85.0, 0)
    total_cost = round(earthwork_cost + hdpe_cost, 0)

    subsidy_inr = round(min(total_cost * 0.50, 105000.0), 0)
    net_farmer = round(max(0.0, total_cost - subsidy_inr), 0)

    advisory = (
        f"A {top_l:.0f}m x {top_w:.0f}m farm pond ({depth}m deep) will safely impound {storage_lakh_liters} Lakh Liters of rainwater. "
        f"This guarantees {dry_spell_days_target} days of drought buffer, sufficient to provide 2 lifesaver irrigations to {irrig_acres:.1f} acres of standing crop."
    )

    return {
        "catchment_acres": acres,
        "annual_rainfall_mm": rain_mm,
        "runoff_volume_cu_meters": round(runoff_cu_m, 0),
        "storage_capacity_liters": storage_liters,
        "storage_capacity_lakh_liters": storage_lakh_liters,
        "recommended_top_length_m": top_l,
        "recommended_top_width_m": top_w,
        "recommended_bottom_length_m": bottom_l,
        "recommended_bottom_width_m": bottom_w,
        "recommended_depth_m": depth,
        "side_slope_ratio": "1:1.5 (V:H)",
        "geomembrane_lining_area_sqm": lining_area_sqm,
        "estimated_earthwork_cost_inr": earthwork_cost,
        "estimated_hdpe_lining_cost_inr": hdpe_cost,
        "estimated_total_cost_inr": total_cost,
        "pmksy_khet_talab_subsidy_inr": subsidy_inr,
        "net_farmer_cost_inr": net_farmer,
        "water_security_advisory": advisory
    }


# =======================================================================
# 5. Machinery Rent vs Buy Logic
# =======================================================================
def calculate_machinery_rent_vs_buy(
    machine_type: str = "Tractor 45-50 HP",
    farm_size_acres: float = 8.0,
    purchase_price_inr: Optional[float] = None,
    custom_hire_rate_per_acre_or_hr: Optional[float] = None,
    commercial_rental_acres_to_others: Optional[float] = 0.0
) -> Dict[str, Any]:
    acres = max(0.5, farm_size_acres)
    comm_acres = max(0.0, commercial_rental_acres_to_others or 0.0)
    total_operated_acres = acres + comm_acres
    m_lower = machine_type.lower()

    is_tractor = "tractor" in m_lower
    hours_per_acre = 4.0 if is_tractor else 1.0

    if "rotavator" in m_lower:
        price = purchase_price_inr or 120000.0
        custom_rate = custom_hire_rate_per_acre_or_hr or 900.0
        diesel_burn_per_acre = 4.5
        economic_life_years = 8
    elif "drill" in m_lower:
        price = purchase_price_inr or 85000.0
        custom_rate = custom_hire_rate_per_acre_or_hr or 700.0
        diesel_burn_per_acre = 2.8
        economic_life_years = 8
    elif "laser" in m_lower:
        price = purchase_price_inr or 350000.0
        custom_rate = custom_hire_rate_per_acre_or_hr or 1100.0
        diesel_burn_per_acre = 6.0
        economic_life_years = 10
    elif "harvester" in m_lower or "combine" in m_lower:
        price = purchase_price_inr or 2400000.0
        custom_rate = custom_hire_rate_per_acre_or_hr or 2200.0
        diesel_burn_per_acre = 8.0
        economic_life_years = 8
    else:
        # Default: 45-50 HP Tractor (used for multiple passes across crop season)
        price = purchase_price_inr or 720000.0
        custom_rate = (custom_hire_rate_per_acre_or_hr or 950.0) * hours_per_acre
        diesel_burn_per_acre = 3.8 * hours_per_acre
        economic_life_years = 10

    annual_hiring_cost = round(acres * custom_rate, 0)
    annual_depreciation = price / economic_life_years
    annual_interest = price * 0.08 * 0.5  # average outstanding loan interest
    annual_insurance = price * 0.015
    annual_fixed_cost = annual_depreciation + annual_interest + annual_insurance

    total_fuel_liters = round(total_operated_acres * diesel_burn_per_acre, 1)
    annual_fuel_cost = round(total_fuel_liters * 90.0, 0)
    annual_maintenance = round(price * 0.025, 0)
    annual_labor = round(total_operated_acres * 150.0 * (hours_per_acre if is_tractor else 1.0), 0)
    annual_variable_cost = annual_fuel_cost + annual_maintenance + annual_labor

    annual_ownership_total = round(annual_fixed_cost + annual_variable_cost, 0)
    commercial_income = round(comm_acres * custom_rate, 0)
    net_ownership_cost = annual_ownership_total - commercial_income
    net_saving_or_loss = round(annual_hiring_cost - net_ownership_cost, 0)

    var_cost_per_acre = (diesel_burn_per_acre * 90.0) + (150.0 * (hours_per_acre if is_tractor else 1.0))
    margin_per_acre = max(100.0, custom_rate - var_cost_per_acre)
    break_even_acres = round(annual_fixed_cost / margin_per_acre, 1)
    payback_years = round(price / max(1000.0, annual_hiring_cost + commercial_income - annual_variable_cost), 1)

    if net_saving_or_loss > 0 or total_operated_acres >= break_even_acres:
        rec = (
            f"✅ BUY RECOMMENDED: With {total_operated_acres:.1f} total operated acres (including {comm_acres:.1f} custom rental acres to neighbors), "
            f"owning this machine saves you ₹{net_saving_or_loss:,.0f}/year over hiring. Break-even threshold is {break_even_acres:.1f} acres."
        )
    else:
        rec = (
            f"🛑 RENT (CUSTOM HIRE) RECOMMENDED: For {acres:.1f} acres, custom hiring costs ₹{annual_hiring_cost:,.0f}/year, "
            f"whereas buying will incur ₹{annual_ownership_total:,.0f}/year in fixed depreciation, fuel, and loan interest. "
            f"Rent by the hour unless you expand custom hiring to neighbors up to at least {break_even_acres:.1f} acres."
        )

    factors = [
        f"Annual Fixed Depreciation & Interest: ₹{round(annual_fixed_cost, 0):,}",
        f"Operational Diesel Burn: {total_fuel_liters:.1f} Liters (₹{round(annual_fuel_cost, 0):,})",
        f"Break-Even Operational Area: {break_even_acres:.1f} acres/year",
        f"Estimated Payback Period: {payback_years} years"
    ]

    return {
        "machine_type": machine_type,
        "farm_size_acres": acres,
        "commercial_rental_acres_to_others": comm_acres,
        "total_operated_acres": total_operated_acres,
        "annual_hiring_cost_inr": annual_hiring_cost,
        "annual_ownership_cost_inr": annual_ownership_total,
        "annual_diesel_burn_liters": total_fuel_liters,
        "annual_fuel_cost_inr": annual_fuel_cost,
        "break_even_acres": break_even_acres,
        "commercial_rental_income_inr": commercial_income,
        "net_annual_saving_or_loss_inr": net_saving_or_loss,
        "recommendation": rec,
        "payback_period_years": payback_years,
        "key_decision_factors": factors
    }


# =======================================================================
# 6. Dynamic Crop Calendar & ICS Logic
# =======================================================================
def generate_crop_calendar_events(
    crop_id: str,
    sowing_date: str,
    land_size_acres: float = 1.0
) -> Dict[str, Any]:
    from app.database import get_crop_by_id
    crop = get_crop_by_id(crop_id)
    crop_name = crop["name"] if crop else crop_id.capitalize()

    try:
        s_date = datetime.strptime(sowing_date.strip(), "%Y-%m-%d").date()
    except Exception:
        s_date = date.today()

    total_days = 120
    if crop and "duration_days" in crop:
        try:
            parts = crop["duration_days"].split("-")
            total_days = int(parts[-1].strip().split()[0])
        except Exception:
            total_days = 120

    h_date = s_date + timedelta(days=total_days)

    events: List[Dict[str, Any]] = [
        {
            "day_offset": 0,
            "target_date": s_date.strftime("%Y-%m-%d"),
            "phase_name": "Sowing & Basal Nutrients",
            "activity_type": "Sowing",
            "action_required": f"Treat certified seed with bio-fungicide (Trichoderma 5g/kg). Broadcast full DAP & MOP bags + 1/3rd Urea basal dose. Plant at specified row depth.",
            "critical_alert": "Ensure adequate soil moisture before seed drilling; avoid sowing in dry soil.",
            "weather_sensitivity": "Rain within 24h will cause soil crusting and impede seedling emergence."
        },
        {
            "day_offset": min(21, int(total_days * 0.18)),
            "target_date": (s_date + timedelta(days=min(21, int(total_days * 0.18)))).strftime("%Y-%m-%d"),
            "phase_name": "Crown Root & Early Vegetative Initiation",
            "activity_type": "Irrigation",
            "action_required": "Provide 1st critical irrigation. Apply 1st top dressing of Urea (1/3rd dose) along with first weeding or intercultural hoeing.",
            "critical_alert": "Critical yield-determining stage! Water stress now permanently reduces tiller count.",
            "weather_sensitivity": "Postpone irrigation if rainfall > 15 mm is forecast."
        },
        {
            "day_offset": min(35, int(total_days * 0.30)),
            "target_date": (s_date + timedelta(days=min(35, int(total_days * 0.30)))).strftime("%Y-%m-%d"),
            "phase_name": "Active Tillering & Weed Management",
            "activity_type": "Weeding",
            "action_required": "Perform second weeding or apply selective post-emergence herbicide. Scout leaf undersides for aphid colonies or early fungal spots.",
            "critical_alert": "Weed competition during first 40 days causes up to 40% yield loss.",
            "weather_sensitivity": "Spray herbicides only when wind speed is < 12 km/h and rain is not expected for 6 hours."
        },
        {
            "day_offset": int(total_days * 0.50),
            "target_date": (s_date + timedelta(days=int(total_days * 0.50))).strftime("%Y-%m-%d"),
            "phase_name": "Stem Elongation & Panicle / Bud Initiation",
            "activity_type": "Nutrient",
            "action_required": "Apply final 1/3rd Urea split. Spray Micronutrient foliar booster (Zinc + Boron 0.1%) to enhance flower set.",
            "critical_alert": "Do not delay nitrogen application beyond this stage to avoid vegetative lodging.",
            "weather_sensitivity": "Avoid heavy irrigation during high wind gusts to prevent crop lodging."
        },
        {
            "day_offset": int(total_days * 0.70),
            "target_date": (s_date + timedelta(days=int(total_days * 0.70))).strftime("%Y-%m-%d"),
            "phase_name": "Flowering & Grain / Fruit Filling",
            "activity_type": "Pest Management",
            "action_required": "Maintain optimum soil moisture. Install yellow sticky traps and pheromone traps for pest monitoring. Apply bio-control if pest threshold is crossed.",
            "critical_alert": "Do not spray toxic synthetic insecticides during morning pollinator activity.",
            "weather_sensitivity": "High temperatures (> 38°C) cause pollen desiccation; light misting/sprinklers help."
        },
        {
            "day_offset": total_days,
            "target_date": h_date.strftime("%Y-%m-%d"),
            "phase_name": "Physiological Maturity & Harvest",
            "activity_type": "Harvesting",
            "action_required": "Harvest when 80-85% grains or pods turn golden brown. Sun-dry harvest immediately on clean tarpaulin to bring moisture under 12%.",
            "critical_alert": "Avoid delaying harvest to minimize shattering losses and unseasonal rain damage.",
            "weather_sensitivity": "Strict dry weather required for combining, threshing, and bagging."
        }
    ]

    ics_lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//AgriAssist//Dynamic Crop Sowing Calendar//EN",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH"
    ]
    for ev in events:
        d_clean = ev["target_date"].replace("-", "")
        ics_lines.extend([
            "BEGIN:VEVENT",
            f"SUMMARY:AgriAssist: {crop_name} - {ev['phase_name']}",
            f"DESCRIPTION:{ev['action_required']} | Alert: {ev['critical_alert']}",
            f"DTSTART;VALUE=DATE:{d_clean}",
            f"DTEND;VALUE=DATE:{d_clean}",
            "STATUS:CONFIRMED",
            "TRANSP:TRANSPARENT",
            "END:VEVENT"
        ])
    ics_lines.append("END:VCALENDAR")
    ics_text = "\r\n".join(ics_lines)

    return {
        "crop_id": crop_id,
        "crop_name": crop_name,
        "sowing_date": s_date.strftime("%Y-%m-%d"),
        "harvest_date": h_date.strftime("%Y-%m-%d"),
        "total_duration_days": total_days,
        "events": events,
        "ics_calendar_text": ics_text
    }


# =======================================================================
# Post-Harvest Grain Aeration, Drying & Safe Storage Sizer
# =======================================================================
def calculate_post_harvest_aeration(
    grain_type: str = "Paddy (Rice)",
    quantity_quintals: float = 100.0,
    initial_moisture_pct: float = 19.5,
    target_moisture_pct: Optional[float] = None,
    ambient_temp_c: Optional[float] = 28.0,
    ambient_rh_pct: Optional[float] = 65.0,
    storage_type: Optional[str] = "Bagged in Warehouse"
) -> Dict[str, Any]:
    """Calculates water removal requirement, fan aeration airflow (CFM), motor HP,
    and safe storage shelf-life to avoid Aspergillus flavus and mold damage.
    """
    qty_q = max(0.1, float(quantity_quintals or 100.0))
    m_init = max(5.0, min(40.0, float(initial_moisture_pct or 19.5)))
    temp_c = float(ambient_temp_c if ambient_temp_c is not None else 28.0)
    rh_pct = max(10.0, min(99.0, float(ambient_rh_pct if ambient_rh_pct is not None else 65.0)))
    storage = storage_type or "Bagged in Warehouse"

    # Default safe moisture limits by commodity
    safe_benchmarks = {
        "paddy": 13.0,
        "rice": 12.5,
        "wheat": 12.0,
        "maize": 13.0,
        "corn": 13.0,
        "soybean": 11.0,
        "mustard": 8.5,
        "chickpea": 10.5,
        "lentil": 11.0,
        "pearl_millet": 12.0,
        "sorghum": 12.0
    }
    key = grain_type.lower()
    default_target = 12.0
    for k_crop, lim in safe_benchmarks.items():
        if k_crop in key:
            default_target = lim
            break

    m_target = float(target_moisture_pct) if target_moisture_pct is not None else default_target
    m_target = min(m_init, max(5.0, m_target))

    # Moisture Removal Calculation
    initial_total_kg = qty_q * 100.0
    dry_matter_kg = initial_total_kg * (1.0 - m_init / 100.0)
    final_total_kg = dry_matter_kg / (1.0 - m_target / 100.0)
    water_to_remove_kg = max(0.0, round(initial_total_kg - final_total_kg, 1))
    final_q = round(final_total_kg / 100.0, 2)

    # Equilibrium Moisture Content (EMC) via modified Henderson formula approximation
    # Higher RH and lower temperature raise EMC
    emc = round(1.1 * math.log(1.0 / (1.0 - min(0.95, rh_pct / 100.0))) ** 0.5 * (300.0 / (temp_c + 273.15)) * 9.5, 1)
    emc = max(7.0, min(22.0, emc))

    # Aeration Airflow:
    # 2.0 CFM/quintal for active moisture drying; 0.5 CFM/quintal for temperature cooling maintenance
    if m_init > m_target + 1.0:
        cfm_rate = 2.5
    else:
        cfm_rate = 0.8
    total_cfm = round(qty_q * cfm_rate, 1)

    # Static pressure estimate (inches WG): ~1.8 in typical grain depth (2-3 meters)
    static_pressure_wg = 1.8
    fan_hp = round((total_cfm * static_pressure_wg) / (6356.0 * 0.55), 2)
    fan_hp = max(0.25, fan_hp)

    # Drying duration estimates
    # Sun drying: 1 acre poly-tarpaulin can dry ~50 quintals per day (6-8 hours sunny day)
    sun_hours = round((water_to_remove_kg / (qty_q * 1.8)) * 4.0, 1) if water_to_remove_kg > 0 else 0.0
    forced_air_hours = round(water_to_remove_kg / (max(10.0, total_cfm * 0.025)), 1) if water_to_remove_kg > 0 else 0.0

    # Shelf-life before mold / pest spoilage at initial moisture & temperature
    if m_init > 18.0:
        safe_days = max(2, int(15 - (m_init - 18.0) * 3 - max(0, temp_c - 25) * 0.3))
        risk_level = "Critical Hazard"
        aflatoxin_warning = "CRITICAL: Moisture exceeds 18%. Risk of Aspergillus flavus fungal growth, heating, and aflatoxin contamination within 48-72 hours. Immediate drying required."
    elif m_init > m_target + 1.5:
        safe_days = max(10, int(45 - (m_init - m_target) * 8 - max(0, temp_c - 25)))
        risk_level = "Moderate Warning"
        aflatoxin_warning = "WARNING: Grain is above safe storage limit. Insect reproduction (weevils/borers) and localized moisture migration possible within 2-4 weeks."
    else:
        safe_days = max(180, int(365 - max(0, temp_c - 28) * 10))
        risk_level = "Safe"
        aflatoxin_warning = "OPTIMAL: Moisture content is within safe international and FCI storage specifications. Grain is safe for prolonged storage if silo is sealed against moisture ingress."

    protocols = [
        f"Spread grain in thin layers (3 - 5 cm) on clean tarpaulin or drying floor. Rake every 2 hours to avoid uneven drying.",
        f"Ensure forced-air fans run only when ambient RH is below {round(emc * 5.2, 0)}% to prevent blowing moisture INTO the grain bed.",
        f"Target moisture for long-term storage is {m_target}% (Equilibrium moisture content with current air is ~{emc}%).",
        f"Apply food-grade Malathion 5% DP dusting on outer bag surfaces (25 g/m²) or place Pusa Bin hermetic liners to stop weevil attacks."
    ]

    return {
        "grain_type": grain_type,
        "quantity_quintals": qty_q,
        "initial_moisture_pct": m_init,
        "target_moisture_pct": m_target,
        "moisture_to_remove_kg": water_to_remove_kg,
        "final_quantity_quintals": final_q,
        "equilibrium_moisture_content_pct": emc,
        "aeration_fan_airflow_cfm": total_cfm,
        "fan_power_hp_estimate": fan_hp,
        "estimated_drying_hours_sun": sun_hours,
        "estimated_drying_hours_forced_air": forced_air_hours,
        "safe_storage_duration_days": safe_days,
        "storage_risk_level": risk_level,
        "aflatoxin_mold_warning": aflatoxin_warning,
        "recommended_protocols": protocols
    }


# =======================================================================
# Polyhouse, Greenhouse & Protected Horticulture Climate Control Sizer
# =======================================================================
def calculate_polyhouse_climate_control(
    structure_type: str = "Naturally Ventilated Polyhouse (NVPH)",
    covered_area_sqm: float = 1008.0,
    crop_type: str = "Bell Pepper (Colored Capsicum)",
    ambient_max_temp_c: Optional[float] = 40.0,
    ambient_min_rh_pct: Optional[float] = 30.0,
    roof_height_meters: Optional[float] = 4.5
) -> Dict[str, Any]:
    """Calculates ventilation fan capacity, evaporative cooling pad dimensions,
    Vapor Pressure Deficit (VPD in kPa), thermal drop, and MIDH government subsidy.
    """
    area = max(50.0, float(covered_area_sqm or 1008.0))
    height = max(3.0, min(8.0, float(roof_height_meters or 4.5)))
    temp_amb = float(ambient_max_temp_c if ambient_max_temp_c is not None else 40.0)
    rh_amb = max(10.0, min(95.0, float(ambient_min_rh_pct if ambient_min_rh_pct is not None else 30.0)))
    stype = structure_type or "Naturally Ventilated Polyhouse (NVPH)"
    crop = crop_type or "Bell Pepper (Colored Capsicum)"

    volume_m3 = round(area * (height * 0.85), 1)

    # Ridge and side vents (for natural ventilation)
    ridge_vent_sqm = round(area * 0.18, 1)
    side_vent_sqm = round(area * 0.28, 1)

    # Evaporative pad-and-fan airflow
    # 1.15 air exchanges per minute for tropical/subtropical climate
    airflow_m3_min = volume_m3 * 1.15
    airflow_cfm = round(airflow_m3_min * 35.315, 0)

    # 50-inch industrial cone exhaust fan delivers ~22,000 CFM (37,400 m³/hr)
    if "fan" in stype.lower() or "pad" in stype.lower() or "greenhouse" in stype.lower():
        num_fans = max(1, math.ceil(airflow_cfm / 22000.0))
        # Cellulose pad area based on 1.25 m/s face velocity
        pad_area_sqm = round((airflow_m3_min / 60.0) / 1.25, 1)
        cooling_water_lph = round(pad_area_sqm * 360.0, 0)
    else:
        num_fans = 0
        pad_area_sqm = 0.0
        cooling_water_lph = 0.0

    # Wet-bulb temperature estimation via Stull formula
    tw = (
        temp_amb * math.atan(0.151977 * (rh_amb + 8.313659) ** 0.5)
        + math.atan(temp_amb + rh_amb)
        - math.atan(rh_amb - 1.676331)
        + 0.00391838 * (rh_amb ** 1.5) * math.atan(0.023101 * rh_amb)
        - 4.686035
    )

    # Expected temperature inside
    if "fan" in stype.lower() or "pad" in stype.lower():
        # 75% pad saturation efficiency
        pad_eff = 0.75
        temp_inside = round(temp_amb - ((temp_amb - tw) * pad_eff), 1)
        inside_rh = min(85.0, round(rh_amb + (100.0 - rh_amb) * 0.65, 1))
    elif "shade" in stype.lower():
        temp_inside = round(temp_amb - 3.5, 1)
        inside_rh = min(90.0, round(rh_amb + 10.0, 1))
    else:
        # NVPH with top ridge vents and foggers
        temp_inside = round(temp_amb - 4.5, 1)
        inside_rh = min(80.0, round(rh_amb + 15.0, 1))

    # Shade net recommendation based on ambient temperature
    if temp_amb >= 42.0:
        shade_pct = 75
    elif temp_amb >= 37.0:
        shade_pct = 50
    else:
        shade_pct = 35

    # Vapor Pressure Deficit (VPD) in kPa:
    # SVP = 0.61078 * exp(17.27 * T / (T + 237.3))
    svp = 0.61078 * math.exp((17.27 * temp_inside) / (temp_inside + 237.3))
    avp = svp * (inside_rh / 100.0)
    vpd = round(svp - avp, 2)

    if vpd < 0.4:
        vpd_status = "Low Transpiration (Humid)"
        vpd_note = "High risk of fungal sporulation, powdery mildew, and calcium blossom-end deficiency due to poor transpiration flow."
    elif 0.8 <= vpd <= 1.25:
        vpd_status = "Optimal"
        vpd_note = "Perfect photosynthetic range: stomata remain open with maximum CO2 assimilation and calcium uptake."
    else:
        vpd_status = "High Transpiration Stress"
        vpd_note = "Extreme water pull causing partial stomatal closure, flower abortion, and leaf wilting. Activate foggers or thermal shade net."

    # Project Cost and MIDH Subsidy calculation
    # Rates under Mission for Integrated Development of Horticulture (MIDH)
    if "fan" in stype.lower() or "pad" in stype.lower():
        rate_per_sqm = 1465.0
    elif "shade" in stype.lower():
        rate_per_sqm = 710.0
    else:
        rate_per_sqm = 844.0

    total_cost = round(area * rate_per_sqm, 2)
    # Standard 50% MIDH subsidy for general areas
    subsidy_inr = round(total_cost * 0.50, 2)
    farmer_share = round(total_cost - subsidy_inr, 2)

    recommendations = [
        f"Maintain ridge and side ventilation insect-proof netting (40 mesh / 0.28mm aperture) to block whiteflies and thrips vectoring leaf curl virus.",
        f"Operate evaporative cooling / fogging when ambient VPD rises above 1.30 kPa (current inside estimated VPD is {vpd} kPa).",
        f"Apply thermal reflective aluminized shade net (movable curtain, {shade_pct}%) between 11:30 AM and 3:30 PM on hot summer days.",
        f"MIDH scheme provides 50% capital subsidy (₹{subsidy_inr:,.0f}) disbursed via State Horticulture Department upon field inspection."
    ]

    return {
        "structure_type": stype,
        "covered_area_sqm": area,
        "crop_type": crop,
        "polyhouse_volume_m3": volume_m3,
        "ridge_vent_area_sqm": ridge_vent_sqm,
        "side_vent_area_sqm": side_vent_sqm,
        "exhaust_fan_airflow_cfm": airflow_cfm,
        "number_of_exhaust_fans_50inch": num_fans,
        "cooling_pad_area_sqm": pad_area_sqm,
        "cooling_water_flow_rate_lph": cooling_water_lph,
        "shade_net_recommended_pct": shade_pct,
        "expected_inside_temp_c": temp_inside,
        "vapor_pressure_deficit_kpa": vpd,
        "vpd_status": vpd_status,
        "estimated_midh_subsidy_inr": subsidy_inr,
        "total_project_cost_inr": total_cost,
        "farmer_net_share_inr": farmer_share,
        "operational_recommendations": recommendations
    }


# =======================================================================
# Farm Stubble (Parali) Pyrolysis, Biochar Yield & Rapid Composting Tool
# =======================================================================
def calculate_biochar_and_stubble_management(
    residue_crop: str = "Paddy Straw (Parali)",
    land_size_acres: float = 5.0,
    current_disposal_method: Optional[str] = "In-Field Burning",
    target_technology: Optional[str] = "Kon-Tiki Pyrolysis Kiln (Biochar)"
) -> Dict[str, Any]:
    """Calculates crop residue biomass generation, on-farm biochar production yield,
    soil water retention boost, averted emissions (CO2 & PM2.5), and rapid composting recipes.
    """
    acres = max(0.1, float(land_size_acres or 5.0))
    crop_str = residue_crop.lower()

    # Biomass yield benchmark per acre (quintals)
    biomass_rates = {
        "paddy": 28.0,
        "rice": 28.0,
        "parali": 28.0,
        "wheat": 22.0,
        "turi": 22.0,
        "cotton": 18.0,
        "mustard": 14.0,
        "sugarcane": 35.0,
        "maize": 24.0
    }
    biomass_per_acre = 25.0
    for k, v in biomass_rates.items():
        if k in crop_str:
            biomass_per_acre = v
            break

    total_biomass_q = round(acres * biomass_per_acre, 1)
    total_biomass_kg = total_biomass_q * 100.0

    # Biochar Pyrolysis Yield (28% to 32% in flame-curtain / Kon-Tiki kilns)
    biochar_yield_pct = 0.30
    biochar_q = round(total_biomass_q * biochar_yield_pct, 1)
    biochar_kg = biochar_q * 100.0

    # Economic value @ ₹15 per kg granulated biochar (or soil conditioner retail)
    economic_val = round(biochar_kg * 15.0, 2)

    # Soil water retention improvement: biochar holds ~3.8x its dry weight in water
    water_retention_liters = round(biochar_kg * 3.8, 0)

    # Carbon sequestration: 1 kg biochar sequestered = ~2.6 kg CO2 equivalent
    co2_seq_kg = round(biochar_kg * 2.6, 1)

    # Emissions averted compared to open field burning:
    # 1.5 kg CO2 per kg straw burned; 7.5 kg PM2.5 per ton burned
    co2_averted_kg = round(total_biomass_kg * 1.48, 1)
    pm25_averted_kg = round((total_biomass_kg / 1000.0) * 7.5, 1)

    # NGT Burning Fine averted (₹2,500 for < 2 acres, ₹5,000 for 2-5 acres, ₹15,000 for > 5 acres)
    if acres < 2.0:
        ngt_fine = 2500.0
    elif acres <= 5.0:
        ngt_fine = 5000.0
    else:
        ngt_fine = 15000.0

    # C:N Balancing Recipe for Rapid Composting:
    # Raw straw C:N is ~80:1. Target C:N is 28:1.
    cow_dung_req_kg = round(total_biomass_kg * 0.20, 0)
    pusa_decomposer_capsules = max(4, int(acres * 4))
    jaggery_req_kg = round(acres * 2.0, 1)
    besan_req_kg = round(acres * 2.0, 1)

    recipe = {
        "raw_straw_c_n_ratio": "80:1 (Very High, decay takes 120+ days)",
        "balanced_compost_c_n_ratio": "28:1 (Optimal Humus within 35-45 days)",
        "cow_dung_slurry_required_kg": cow_dung_req_kg,
        "pusa_decomposer_capsules": pusa_decomposer_capsules,
        "fermentation_jaggery_kg": jaggery_req_kg,
        "chickpea_besan_kg": besan_req_kg,
        "water_moisture_target_pct": "55 - 60% (Squeeze test: droplet forms without dripping)",
        "pile_turning_schedule": "Turn on Day 7, Day 14, and Day 21 for aerobic oxygenation"
    }

    guidelines = [
        f"Generate {biochar_q} quintals of high-grade biochar using a low-cost pit or sheet-metal Kon-Tiki kiln (commercial value ₹{economic_val:,.0f}).",
        f"Quench glowing biochar with cow urine or compost tea to 'charge / activate' its pore structure before applying to soil.",
        f"Avert {pm25_averted_kg} kg of toxic PM2.5 smog and avoid ₹{ngt_fine:,.0f} in National Green Tribunal (NGT) burning penalties.",
        f"Increases farm soil moisture holding capacity by {water_retention_liters:,.0f} liters, buffering crops against summer heatwaves."
    ]

    return {
        "residue_crop": residue_crop,
        "land_size_acres": acres,
        "estimated_residue_biomass_quintals": total_biomass_q,
        "biochar_yield_quintals": biochar_q,
        "economic_value_biochar_inr": economic_val,
        "soil_water_retention_gain_liters": water_retention_liters,
        "carbon_sequestration_co2e_kg": co2_seq_kg,
        "co2_emissions_averted_kg": co2_averted_kg,
        "pm25_pollution_averted_kg": pm25_averted_kg,
        "composting_recipe": recipe,
        "ngt_fine_penalty_averted_inr": ngt_fine,
        "actionable_farmer_guidelines": guidelines
    }









