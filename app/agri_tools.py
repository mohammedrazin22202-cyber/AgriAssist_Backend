"""AgriAssist Agronomic Tools & Calculators.
Provides:
1. Fertilizer Prescription (Urea, DAP, MOP stoichiometric bag calculator & pH amendments).
2. Farm Financials & MSP Profit Calculator (costs, yields, revenue, ROI).
3. 1-Year Multi-Crop Rotation & Sequencing Planner (Kharif -> Rabi -> Zaid).
"""

from typing import Dict, Any, List, Optional
import math


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
        "total_water_liters": total_water,
        "total_chemical_needed": total_chem,
        "nozzle_recommendation": nozzle,
        "safety_checklist": safety,
        "application_tips": tips
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
        "pump_type": pump_type,
        "total_estimated_cost_inr": base_cost,
        "central_subsidy_inr": central_sub_inr,
        "state_subsidy_inr": state_sub_inr,
        "farmer_share_inr": farmer_share_inr,
        "subsidy_percentage_total": total_sub_pct,
        "annual_diesel_savings_inr": annual_diesel_savings,
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
    if not crop_id or crop_id == "all":
        return INTERCROPPING_PAIRS_CATALOG
    cid = crop_id.lower()
    return [
        p for p in INTERCROPPING_PAIRS_CATALOG
        if p["main_crop_id"] == cid or p["companion_crop_id"] == cid
    ]


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
        res.append({
            "crop_id": k,
            "crop_name": v["crop_name"],
            "safe_moisture_limit_pct": v["safe_moisture_limit_pct"],
            "max_shelf_life_months": v["max_shelf_life_months"],
            "common_storage_pests": v["common_storage_pests"],
            "natural_protectants": v["natural_protectants"],
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
    cid = crop_id.lower()
    profile = GRAIN_STORAGE_CATALOG.get(cid)
    if not profile:
        profile = {
            "crop_name": crop_id.title(),
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

    return {
        "crop_id": cid,
        "crop_name": profile["crop_name"],
        "measured_moisture_pct": moisture,
        "safe_moisture_limit_pct": safe_limit,
        "risk_level": risk_level,
        "risk_explanation": explanation,
        "sun_drying_hours_needed": drying_hours,
        "traditional_preservation_tips": profile["natural_protectants"],
        "enwr_warehouse_pledge_benefit": enwr_benefit
    }





