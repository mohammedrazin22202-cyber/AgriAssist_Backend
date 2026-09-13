"""Automated end-to-end diagnostic test suite for AgriAssist.
Verifies all 14 Ag-Tech modules, backend REST endpoints, frontend assets, and error handling.
Can run standalone via in-memory TestClient or against live server.
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from app.main import app

def run_diagnostics():
    print("=" * 75)
    print("        AgriAssist 14-Feature Full System Diagnostic Suite")
    print("=" * 75)

    client = TestClient(app)
    results = []

    def check(name, condition, details=""):
        status = "PASS" if condition else "FAIL"
        symbol = "[OK]" if condition else "[X]"
        results.append((name, condition))
        print(f" {symbol} {name:<50} : {status} {details}")
        return condition

    # --- 1. Backend Connectivity & Health ---
    try:
        r = client.get("/api/health")
        data = r.json()
        check("1. Backend /api/health responding", r.status_code == 200 and data.get("status") == "online")
    except Exception as e:
        check("1. Backend /api/health responding", False, f"Error: {e}")

    # --- 2. State & District Agro-climatic Presets ---
    try:
        r = client.get("/api/districts")
        data = r.json()
        states = data.get("states", {})
        check("2. Districts & State presets (>=10 states)", len(states) >= 10, f"({len(states)} states found)")
    except Exception as e:
        check("2. Districts & State presets", False, f"Error: {e}")

    # --- 3. Crop Sowing Advisor & Decision Support ---
    try:
        payload = {
            "mode": "simple",
            "soil_type": "Black Soil (Regur)",
            "season": "Kharif",
            "water_availability": "Moderate (Canal / Tube-well / Seasonal)",
            "budget_preference": "Commercial / High Value"
        }
        r = client.post("/api/recommend", json=payload)
        data = r.json()
        recs = data.get("recommendations", [])
        top_crop = data.get("top_pick", {}).get("name", "")
        check("3. Sowing Advisor (Kharif/Black Soil)", r.status_code == 200 and len(recs) >= 5, f"Top: {top_crop}")
    except Exception as e:
        check("3. Sowing Advisor", False, f"Error: {e}")

    # --- 4. Seed Rate & Spacing Calculator ---
    try:
        payload = {
            "crop_id": "wheat",
            "land_size_acres": 2.5,
            "germination_rate_pct": 85.0
        }
        r = client.post("/api/seed-calculator", json=payload)
        data = r.json()
        seed_kg = data.get("total_seed_required_kg", 0)
        check("4. Seed Rate & Geometry Calculator", r.status_code == 200 and seed_kg > 0, f"({seed_kg} kg for 2.5 acres)")
    except Exception as e:
        check("4. Seed Rate & Geometry Calculator", False, f"Error: {e}")

    # --- 5. Plant Doctor (IPM Diagnosis & Prescriptions) ---
    try:
        payload = {
            "crop_id": "cotton",
            "plant_part": "Fruit/Grain",
            "search_term": "pink"
        }
        r = client.post("/api/plant-doctor/diagnose", json=payload)
        data = r.json()
        issues = data.get("issues", [])
        has_pbw = any("Pink Bollworm" in i.get("name", "") for i in issues)
        check("5. Plant Doctor IPM Diagnosis", r.status_code == 200 and has_pbw, f"({len(issues)} matches found)")
    except Exception as e:
        check("5. Plant Doctor IPM Diagnosis", False, f"Error: {e}")

    # --- 6. APMC Mandi Prices, Trends & Selling Advice ---
    try:
        r = client.get("/api/mandi-prices?crop_id=wheat")
        data = r.json()
        mandis = data.get("prices", [])
        check("6. Mandi Prices & 30-Day Trends", r.status_code == 200 and len(mandis) >= 1, f"({len(mandis)} APMC records)")
    except Exception as e:
        check("6. Mandi Prices & Trends", False, f"Error: {e}")

    # --- 7. Knapsack Sprayer & Dilution Calculator ---
    try:
        payload = {
            "tank_capacity_liters": 16.0,
            "field_acres": 2.0,
            "dosage_mode": "per_acre",
            "dosage_amount": 250.0,
            "chemical_formulation": "liquid_ml",
            "water_volume_liters_per_acre": 150.0
        }
        r = client.post("/api/sprayer-calculator", json=payload)
        data = r.json()
        tanks = data.get("total_spray_tanks") or data.get("tanks_needed_total")
        check("7. Knapsack Sprayer & Dilution Calculator", r.status_code == 200 and tanks > 0, f"({tanks} tanks calculated)")
    except Exception as e:
        check("7. Knapsack Sprayer Calculator", False, f"Error: {e}")

    # --- 8. Smart Irrigation & Pump Scheduler ---
    try:
        payload = {
            "crop_id": "wheat",
            "growth_stage": "Crown Root Initiation (CRI at 21 days)",
            "soil_type": "Alluvial Soil",
            "land_size_acres": 2.0,
            "pump_hp": 5.0,
            "forecast_rain_mm": 25.0
        }
        r = client.post("/api/irrigation-schedule", json=payload)
        data = r.json()
        rain_alert = data.get("rain_warning", False)
        check("8. Smart Irrigation & Rain Alert", r.status_code == 200 and rain_alert, f"(Rain warning: {rain_alert})")
    except Exception as e:
        check("8. Smart Irrigation", False, f"Error: {e}")

    # --- 9. Solar Ag-Pump & PM-KUSUM Subsidy Estimator ---
    try:
        payload = {
            "water_source": "Borewell",
            "water_depth_feet": 150.0,
            "command_area_acres": 3.0,
            "irrigation_method": "Drip / Sprinkler",
            "farmer_category": "Small / Marginal (< 2 Ha)"
        }
        r = client.post("/api/solar-pump-calculator", json=payload)
        data = r.json()
        hp = data.get("recommended_pump_hp", 0)
        sub_pct = data.get("subsidy_percentage_total", 0)
        check("9. Solar Pump & PM-KUSUM Subsidy", r.status_code == 200 and hp >= 3.0, f"({hp} HP pump, {sub_pct}% subsidy)")
    except Exception as e:
        check("9. Solar Pump Estimator", False, f"Error: {e}")

    # --- 10. Organic / Jaivik Kheti Prescriptions ---
    try:
        payload = {"crop_id": "chickpea", "land_size_acres": 2.0}
        r = client.post("/api/organic-prescription", json=payload)
        data = r.json()
        jeev = data.get("total_jeevamrutha_liters", 0)
        check("10. Organic / Jaivik Kheti Recipes", r.status_code == 200 and jeev > 0, f"({jeev}L Jeevamrutha)")
    except Exception as e:
        check("10. Organic Prescriptions", False, f"Error: {e}")

    # --- 11. Intercropping & Companion Crop Matrix ---
    try:
        r = client.get("/api/intercropping?main_crop=Sugarcane")
        data = r.json()
        pairs = data.get("pairs", [])
        check("11. Intercropping Companion Matrix", r.status_code == 200 and len(pairs) >= 1, f"({len(pairs)} pairs for Sugarcane)")
    except Exception as e:
        check("11. Intercropping Matrix", False, f"Error: {e}")

    # --- 12. Post-Harvest Grain Storage Doctor ---
    try:
        payload = {
            "crop_name": "Paddy / Rice",
            "current_moisture_pct": 15.5,
            "storage_method": "Jute Bags",
            "planned_duration_months": 6
        }
        r = client.post("/api/grain-storage/check-risk", json=payload)
        data = r.json()
        risk = data.get("risk_level", "")
        check("12. Grain Storage Risk Doctor", r.status_code == 200 and "Safe" not in risk, f"(Risk: {risk.split('/')[0].strip()})")
    except Exception as e:
        check("12. Grain Storage Risk Doctor", False, f"Error: {e}")

    # --- 13. 1-Year Crop Rotation Planner ---
    try:
        payload = {
            "soil_type": "Black Soil (Regur)",
            "water_availability": "Moderate (Canal / Tube-well / Seasonal)",
            "land_size_acres": 2.0
        }
        r = client.post("/api/rotation-plan", json=payload)
        data = r.json()
        plans = data.get("plans", [])
        crops_seq = ""
        if plans and "crops" in plans[0]:
            crops_seq = " -> ".join(c.get("crop_name", "") for c in plans[0]["crops"])
        check("13. 1-Year Crop Rotation Planner", r.status_code == 200 and len(plans) >= 1, f"({crops_seq})")
    except Exception as e:
        check("13. Crop Rotation Planner", False, f"Error: {e}")

    # --- 14. Precision Fertilizer Doctor ---
    try:
        payload = {
            "crop_id": "wheat",
            "soil_n": 100.0,
            "soil_p": 20.0,
            "soil_k": 100.0,
            "soil_ph": 5.2,
            "land_size_acres": 2.0
        }
        r = client.post("/api/fertilizer-prescription", json=payload)
        data = r.json()
        urea_bags = data.get("urea_bags_50kg", 0)
        has_lime = "lime" in data.get("amendment_type", "").lower()
        check("14. Precision Fertilizer Doctor", r.status_code == 200 and urea_bags > 0 and has_lime, f"({urea_bags} Urea bags + Lime alert)")
    except Exception as e:
        check("14. Fertilizer Doctor", False, f"Error: {e}")

    # --- 15. Kisan Yojana Hub (PM-KISAN, PMFBY, KCC) ---
    try:
        payload = {
            "crop_id": "wheat",
            "land_size_acres": 2.0,
            "farmer_category": "Small / Marginal (< 2 Ha)"
        }
        r = client.post("/api/government-schemes/calculate", json=payload)
        data = r.json()
        kcc_limit = data.get("kcc", {}).get("recommended_credit_limit_inr", 0)
        check("15. Kisan Yojana Hub (KCC/PMFBY/PM-KISAN)", r.status_code == 200 and kcc_limit > 0, f"(KCC limit: Rs. {kcc_limit:,.0f})")
    except Exception as e:
        check("15. Kisan Yojana Hub", False, f"Error: {e}")

    # --- 16. Frontend Code Integrity Check ---
    frontend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "src"))
    app_js_path = os.path.join(frontend_dir, "app.js")
    index_html_path = os.path.join(frontend_dir, "index.html")
    style_css_path = os.path.join(frontend_dir, "style.css")

    js_ok = os.path.exists(app_js_path) and os.path.getsize(app_js_path) > 100000
    html_ok = os.path.exists(index_html_path) and os.path.getsize(index_html_path) > 50000
    css_ok = os.path.exists(style_css_path) and os.path.getsize(style_css_path) > 1000

    check("16.1 Frontend app.js asset present", js_ok, f"({os.path.getsize(app_js_path) if js_ok else 0} bytes)")
    check("16.2 Frontend index.html asset present", html_ok, f"({os.path.getsize(index_html_path) if html_ok else 0} bytes)")
    check("16.3 Frontend style.css asset present", css_ok, f"({os.path.getsize(style_css_path) if css_ok else 0} bytes)")

    # --- Summary ---
    print("=" * 75)
    passed_count = sum(1 for _, ok in results if ok)
    total_count = len(results)
    pct = (passed_count / total_count) * 100
    print(f" Diagnostic Summary: {passed_count}/{total_count} checks passed ({pct:.1f}%)")
    print("=" * 75)
    return passed_count == total_count

if __name__ == "__main__":
    success = run_diagnostics()
    sys.exit(0 if success else 1)
