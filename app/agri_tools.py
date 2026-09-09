"""AgriAssist Agronomic Tools & Calculators.
Provides:
1. Fertilizer Prescription (Urea, DAP, MOP stoichiometric bag calculator & pH amendments).
2. Farm Financials & MSP Profit Calculator (costs, yields, revenue, ROI).
3. 1-Year Multi-Crop Rotation & Sequencing Planner (Kharif -> Rabi -> Zaid).
"""

from typing import Dict, Any, List
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

    annual_profit_1 = (c1["net_profit_per_acre"] + c2["net_profit_per_acre"] + c3["net_profit_per_acre"]) * land_size_acres
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
        "annual_net_profit_per_acre_inr": round(annual_profit_1 / land_size_acres, 0)
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

    annual_profit_2 = (c1_b["net_profit_per_acre"] + c2_b["net_profit_per_acre"] + c3_b["net_profit_per_acre"]) * land_size_acres
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
        "annual_net_profit_per_acre_inr": round(annual_profit_2 / land_size_acres, 0)
    })

    # System 3: Oilseed & Pulse Resilient Rotation (Low Water & Stable Return)
    c1_c = {"season": "Kharif", "crop_id": "soybean", "crop_name": "Soybean", "role": "Rich protein/oil legume adding soil nitrogen", "duration": "95 days", "water": "Medium", "net_profit_per_acre": 32000}
    c2_c = {"season": "Rabi", "crop_id": "mustard", "crop_name": "Mustard / Rapeseed", "role": "Low input cost, high oil return", "duration": "110 days", "water": "Low to Medium", "net_profit_per_acre": 36000}
    c3_c = {"season": "Zaid", "crop_id": "green_gram", "crop_name": "Summer Moong", "role": "Protects topsoil from summer scorching & fixes nitrogen", "duration": "60 days", "water": "Low", "net_profit_per_acre": 18000}
    
    annual_profit_3 = (c1_c["net_profit_per_acre"] + c2_c["net_profit_per_acre"] + c3_c["net_profit_per_acre"]) * land_size_acres
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
        "annual_net_profit_per_acre_inr": round(annual_profit_3 / land_size_acres, 0)
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


