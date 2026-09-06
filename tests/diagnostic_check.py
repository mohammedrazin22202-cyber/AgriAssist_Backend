"""Automated end-to-end diagnostic test suite for AgriAssist.
Verifies backend REST endpoints, frontend assets, CORS, and recommendation edge cases.
"""

import sys
import json
import httpx

BACKEND_URL = "http://localhost:4343"
FRONTEND_URL = "http://localhost:3434"

def run_diagnostics():
    print("=" * 70)
    print("        AgriAssist End-to-End Diagnostic Suite")
    print("=" * 70)

    client = httpx.Client(timeout=10.0)
    results = []

    def check(name, condition, details=""):
        status = "PASS" if condition else "FAIL"
        symbol = "[OK]" if condition else "[X]"
        results.append((name, condition))
        print(f" {symbol} {name:<45} : {status} {details}")
        return condition

    # --- 1. Backend Connectivity & Health ---
    try:
        r = client.get(f"{BACKEND_URL}/api/health")
        data = r.json()
        check("1.1 Backend /api/health responding", r.status_code == 200 and data.get("status") == "online")
    except Exception as e:
        check("1.1 Backend /api/health responding", False, f"Error: {e}")

    # --- 2. API Metadata Inspection ---
    try:
        r = client.get(f"{BACKEND_URL}/api/metadata")
        data = r.json()
        soil_count = len(data.get("soil_types", []))
        season_count = len(data.get("seasons", []))
        water_count = len(data.get("water_availability", []))
        check("2.1 /api/metadata soil presets (>=6)", soil_count >= 6, f"({soil_count} presets found)")
        check("2.2 /api/metadata seasons (>=3)", season_count >= 3, f"({season_count} seasons found)")
        check("2.3 /api/metadata water levels (>=3)", water_count >= 3, f"({water_count} options found)")
    except Exception as e:
        check("2.1 /api/metadata schema verification", False, f"Error: {e}")

    # --- 3. Crop Knowledge Base ---
    try:
        r = client.get(f"{BACKEND_URL}/api/crops")
        crops = r.json()
        check("3.1 /api/crops directory loaded (>=20)", len(crops) >= 20, f"({len(crops)} crops found)")

        r_wheat = client.get(f"{BACKEND_URL}/api/crops/wheat")
        wheat_data = r_wheat.json()
        check("3.2 /api/crops/wheat detail retrieval", r_wheat.status_code == 200 and wheat_data.get("id") == "wheat")
    except Exception as e:
        check("3.1 Crop database inspection", False, f"Error: {e}")

    # --- 4. Sowing Decision Engine Scenarios ---
    try:
        # Scenario A: Black Soil + Kharif + Moderate water
        payload_a = {
            "mode": "simple",
            "soil_type": "Black Soil (Regur)",
            "season": "Kharif",
            "water_availability": "Moderate (Canal / Tube-well / Seasonal)",
            "budget_preference": "Commercial / High Value"
        }
        r_a = client.post(f"{BACKEND_URL}/api/recommend", json=payload_a)
        res_a = r_a.json()
        top_a = res_a.get("top_pick", {})
        top_recs_a = [c["crop_id"] for c in res_a.get("recommendations", [])[:5]]
        check("4.1 Scenario A: Black Soil + Kharif ranking", 
              r_a.status_code == 200 and any(c in top_recs_a for c in ["cotton", "soybean", "pigeon_pea", "sorghum"]),
              f"Top pick: {top_a.get('name')} ({top_a.get('suitability_score')}%)")

        # Scenario B: Low Water / Drought scenario
        payload_b = {
            "mode": "simple",
            "soil_type": "Sandy Loam Soil",
            "season": "Kharif",
            "water_availability": "Low (Rainfed / Drought-prone)"
        }
        r_b = client.post(f"{BACKEND_URL}/api/recommend", json=payload_b)
        res_b = r_b.json()
        recs_b = {c["crop_id"]: c for c in res_b.get("recommendations", [])}
        bajra = recs_b.get("pearl_millet")
        rice = recs_b.get("rice")
        drought_test = (bajra and rice and bajra["suitability_score"] > rice["suitability_score"])
        has_warning = any("demands high water" in w.lower() or "risk" in w.lower() for w in (rice.get("warnings", []) if rice else []))
        check("4.2 Scenario B: Drought penalties & Bajra priority", 
              drought_test and has_warning,
              f"Bajra: {bajra['suitability_score']}%, Rice: {rice['suitability_score']}%")

        # Scenario C: Rabi Season in Alluvial Soil
        payload_c = {
            "mode": "simple",
            "soil_type": "Alluvial Soil",
            "season": "Rabi",
            "water_availability": "Moderate (Canal / Tube-well / Seasonal)"
        }
        r_c = client.post(f"{BACKEND_URL}/api/recommend", json=payload_c)
        res_c = r_c.json()
        top_c = [c["crop_id"] for c in res_c.get("recommendations", [])[:4]]
        check("4.3 Scenario C: Rabi season (Wheat/Gram/Mustard)", 
              any(c in top_c for c in ["wheat", "mustard", "chickpea", "potato"]),
              f"Top crops: {', '.join(top_c)}")

        # Scenario D: Advanced Soil Health Card input
        payload_d = {
            "mode": "advanced",
            "soil_type": "Red Soil",
            "season": "Kharif",
            "water_availability": "Moderate (Canal / Tube-well / Seasonal)",
            "nitrogen": 140.0,
            "phosphorus": 30.0,
            "potassium": 160.0,
            "ph": 5.0,  # Acidic pH
            "temperature_c": 28.0,
            "rainfall_mm": 900.0
        }
        r_d = client.post(f"{BACKEND_URL}/api/recommend", json=payload_d)
        res_d = r_d.json()
        applied = res_d.get("applied_parameters", {})
        recs_d = res_d.get("recommendations", [])
        # Acidic soil should generate warnings about lime
        lime_warning_found = False
        for c in recs_d:
            for w in c.get("warnings", []):
                if "acidic" in w.lower() or "lime" in w.lower():
                    lime_warning_found = True
                    break
            if lime_warning_found:
                break
        check("4.4 Scenario D: Advanced Mode & Acidic pH advisory", 
              applied.get("ph") == 5.0 and lime_warning_found,
              "Soil acidity advisory generated")

    except Exception as e:
        check("4.1-4.4 Sowing Decision Engine Scenarios", False, f"Error: {e}")

    # --- 5. Frontend Assets & Config ---
    try:
        r_front = client.get(f"{FRONTEND_URL}/")
        check("5.1 Frontend HTTP server active (port 3434)", r_front.status_code == 200)

        r_js = client.get(f"{FRONTEND_URL}/app.js")
        js_content = r_js.text
        has_correct_port = "http://localhost:4343/api" in js_content
        check("5.2 Frontend app.js loaded & points to port 4343", r_js.status_code == 200 and has_correct_port)

        r_css = client.get(f"{FRONTEND_URL}/style.css")
        check("5.3 Frontend style.css active", r_css.status_code == 200)
    except Exception as e:
        check("5.1 Frontend Verification", False, f"Error: {e}")

    # --- 6. CORS Verification ---
    try:
        r_cors = client.options(
            f"{BACKEND_URL}/api/recommend",
            headers={
                "Origin": "http://localhost:3434",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "content-type"
            }
        )
        cors_ok = r_cors.headers.get("access-control-allow-origin") in ["*", "http://localhost:3434"]
        check("6.1 CORS headers enabled for Frontend", cors_ok, f"(Status: {r_cors.status_code})")
    except Exception as e:
        check("6.1 CORS headers verification", False, f"Error: {e}")

    # --- Summary ---
    print("=" * 70)
    passed_count = sum(1 for _, ok in results if ok)
    total_count = len(results)
    print(f" Diagnostic Summary: {passed_count}/{total_count} checks passed ({passed_count/total_count*100:.1f}%)")
    print("=" * 70)
    return passed_count == total_count

if __name__ == "__main__":
    success = run_diagnostics()
    sys.exit(0 if success else 1)
