"""Interactive Command Line Interface for AgriAssist Crop Decision System.
Allows farmers or agricultural officers to get crop recommendations directly in the terminal.
"""

import sys

# Ensure UTF-8 stdout on Windows terminals
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from app.models import RecommendationRequest
from app.engine import recommend_crops
from app.soil_presets import SOIL_PRESETS, SEASON_METADATA, WATER_AVAILABILITY_LEVELS


def print_banner():
    print("=" * 65)
    print("           AgriAssist: Smart Crop Sowing Advisor           ")
    print("=" * 65)
    print("Empowering farmers with data-driven sowing decisions.\n")


def choose_option(prompt: str, options: list) -> str:
    print(f"\n{prompt}")
    for idx, opt in enumerate(options, 1):
        print(f"  [{idx}] {opt}")
    while True:
        choice = input(f"Select option (1-{len(options)}): ").strip()
        if choice.isdigit() and 1 <= int(choice) <= len(options):
            return options[int(choice) - 1]
        print("Invalid choice. Please try again.")


def run_cli():
    print_banner()

    mode_choice = choose_option(
        "Choose Assessment Mode:",
        ["Quick / Simple Mode (No soil test needed)", "Advanced Mode (Enter Lab NPK & Weather)"]
    )
    is_advanced = "Advanced" in mode_choice

    soil_list = list(SOIL_PRESETS.keys())
    soil_type = choose_option("Step 1: Select your Soil Type:", soil_list)

    season_list = ["Kharif", "Rabi", "Zaid", "All Season / Flexible"]
    season = choose_option("Step 2: Select Sowing Season:", season_list)

    water_list = list(WATER_AVAILABILITY_LEVELS.keys())
    water_availability = choose_option("Step 3: Select Water & Irrigation Availability:", water_list)

    land_size = input("\nEnter Land Size in Acres (default 1.0): ").strip()
    try:
        land_size_val = float(land_size) if land_size else 1.0
    except ValueError:
        land_size_val = 1.0

    n_val, p_val, k_val, ph_val, temp_val, rain_val = None, None, None, None, None, None

    if is_advanced:
        print("\n--- Advanced Soil & Weather Lab Parameters (Press Enter to use typical default) ---")
        n_input = input("Available Nitrogen (N kg/ha): ").strip()
        p_input = input("Available Phosphorus (P kg/ha): ").strip()
        k_input = input("Available Potassium (K kg/ha): ").strip()
        ph_input = input("Soil pH (e.g. 6.8): ").strip()
        temp_input = input("Avg Temperature (°C): ").strip()
        rain_input = input("Expected Seasonal Rainfall (mm): ").strip()

        n_val = float(n_input) if n_input else None
        p_val = float(p_input) if p_input else None
        k_val = float(k_input) if k_input else None
        ph_val = float(ph_input) if ph_input else None
        temp_val = float(temp_input) if temp_input else None
        rain_val = float(rain_input) if rain_input else None

    req = RecommendationRequest(
        mode="advanced" if is_advanced else "simple",
        soil_type=soil_type,
        season=season,
        water_availability=water_availability,
        land_size_acres=land_size_val,
        nitrogen=n_val,
        phosphorus=p_val,
        potassium=k_val,
        ph=ph_val,
        temperature_c=temp_val,
        rainfall_mm=rain_val
    )

    print("\nAnalyzing soil profile, water budget, and seasonal window...")
    res = recommend_crops(req)

    print("\n" + "=" * 65)
    print(f"  TOP RECOMMENDATIONS FOR {soil_type.upper()} IN {season.upper()}  ")
    print("=" * 65)

    for i, rec in enumerate(res.recommendations[:5], 1):
        hindi = f" ({rec.hindi_name})" if rec.hindi_name else ""
        print(f"\n#{i} {rec.name}{hindi} - [{rec.category.upper()}]")
        print(f"   * Suitability Score : {rec.suitability_score}% ({rec.suitability_level})")
        print(f"   * Growth Duration  : {rec.duration_days} | Water Need: {rec.water_requirement}")
        print(f"   * Est. Yield/Acre  : {rec.estimated_yield_per_acre} | Profit: {rec.profit_potential}")
        print(f"   * Sowing Window    : {rec.sowing_window}")
        
        if rec.financials:
            print(f"   * Net Profit (Est.) : ₹{rec.financials.net_profit_inr:,.0f} (ROI: {rec.financials.roi_percentage}%) [MSP: ₹{rec.financials.msp_or_market_price_per_quintal:.0f}/Qtl]")
        if rec.fertilizer_prescription:
            fp = rec.fertilizer_prescription
            print(f"   * Fertilizer Needs  : Urea: {fp.urea_bags_50kg} bags | DAP: {fp.dap_bags_50kg} bags | MOP: {fp.mop_bags_50kg} bags (50kg)")
            if fp.lime_kg > 0 or fp.gypsum_kg > 0:
                print(f"   * Soil Amendment    : {fp.amendment_type} ({fp.lime_kg or fp.gypsum_kg:.0f} kg for {land_size_val} acres)")

        if rec.reasons:
            print("   [+] Why Sow This:")
            for r in rec.reasons[:2]:
                print(f"       - {r}")
                
        if rec.warnings:
            print("   [!] Cautions & Risks:")
            for w in rec.warnings[:2]:
                print(f"       - {w}")

        print(f"   [i] Agronomic Tip: {rec.sowing_tips}")
        print("-" * 65)

    # Optional 1-Year Multi-Crop Rotation
    from app.agri_tools import generate_crop_rotation_plans
    view_rot = input("\nWould you like to view a 1-Year Multi-Crop Rotation Plan? (y/n): ").strip().lower()
    if view_rot in ["y", "yes"]:
        rotations = generate_crop_rotation_plans(soil_type, water_availability, "Balanced", land_size_val)
        print("\n" + "=" * 65)
        print("          1-YEAR SUSTAINABLE MULTI-CROP ROTATION PLANS          ")
        print("=" * 65)
        for idx, plan in enumerate(rotations[:2], 1):
            print(f"\n[Plan #{idx}] {plan['title']} ({plan['badge']})")
            print(f"  * Soil Health Score   : {plan['soil_health_index']}/100")
            print(f"  * Total Annual Profit : ₹{plan['total_annual_net_profit_inr']:,.0f} (₹{plan['annual_net_profit_per_acre_inr']:,.0f}/acre)")
            print(f"  * Soil Benefit        : {plan['nitrogen_fixation_benefit']}")
            print("  * Crop Sequence:")
            for c in plan["crops"]:
                print(f"    - {c['season']}: {c['crop_name']} ({c['duration']}, {c['water']} water) -> Net: ₹{c['net_profit_per_acre'] * land_size_val:,.0f}")
            print("-" * 65)


if __name__ == "__main__":
    run_cli()

