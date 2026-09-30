# AgriAssist Backend

A robust Python & FastAPI agronomic decision-support engine providing high-performance REST endpoints and an interactive CLI for recommending optimal crops, calculating stoichiometric fertilizer prescriptions, and designing 1-year multi-crop rotations.

## 🚀 Key Highlights
- **100-Crop Agronomic Knowledge Base**: Comprehensive profiles with official MSP (Minimum Support Price), water requirements, 4-stage phenological growth calendars, and pest susceptibility.
- **Zero-Cost Engineering ($0 Recurring / ₹0 API Spend)**: Complete agronomic capability without dependency on paid external LLMs or proprietary cloud APIs.
- **Sub-Millisecond Engine Latency**: Deterministic calculation engines profiled to run in microseconds with on-demand `/api/benchmarks` diagnostics.
- **Dual-Mode Architectural Parity**: Every server engine has an identical mathematical equivalent on the client-side PWA for 100% offline capability.

---

## 📂 Project Structure
```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py          # FastAPI application with REST endpoints & CORS
│   ├── engine.py        # Multi-factor agronomic scoring algorithm
│   ├── agri_tools.py    # Precision calculation engines (fertilizer, silage, ZECC, SPNF, GDD)
│   ├── benchmarks.py    # Latency & throughput performance profiler
│   ├── database.py      # Knowledge base of 100 crops with MSP & growth stages
│   ├── soil_presets.py  # Regional soil benchmarks & season metadata
│   └── models.py        # Pydantic v2 schemas (Request / Response validation)
├── docs/
│   └── API_REFERENCE.md # Mathematical formulations, physics models & full API catalog
├── tests/
│   ├── test_engine.py                # Core recommendation engine tests
│   ├── test_all_features.py          # General feature tests
│   ├── test_zero_cost_features.py    # Zero-cost agronomic suite tests
│   ├── test_benchmarks.py            # Latency profiling & throughput tests
│   └── test_contingency_protocol.py  # Ownership verification tests
├── cli.py               # Interactive terminal wizard with economics & rotation
├── requirements.txt     # Python dependencies
├── Dockerfile           # Production container definition
└── README.md
```

---

## 🛠️ Complete REST API Endpoints Catalog

### 1. Core Diagnostics & Reference
- `GET /api/health` - Service health status & engine version.
- `GET /api/benchmarks` - On-demand latency (mean, median, p95) and throughput benchmarking.
- `GET /api/metadata` - Soil presets, agricultural seasons, and farming budget options.
- `GET /api/crops` - Complete 100-crop directory.
- `GET /api/crops/{crop_id}` - Detailed agronomic profile with 4-stage growth timeline.

### 2. Decision Support & Agronomic Prescriptions
- `POST /api/recommend` - Multi-factor crop ranking with net profit, investment cost & fertilizer bags.
- `POST /api/rotation-plan` - 1-Year Multi-Crop Rotation Plans (Kharif $\to$ Rabi $\to$ Zaid).
- `POST /api/fertilizer-prescription` - Stoichiometric Urea/DAP/MOP bags & Lime/Gypsum dosage.
- `POST /api/plant-doctor/diagnose` - Rule-based IPM diagnosis for 30+ crop diseases.

### 3. Precision Ag-Tech Engines
- `POST /api/drip-fertigation` - Venturi injection rates, N-P-K concentration ppm & water volume.
- `POST /api/carbon-credits` - Soil organic carbon (SOC) sequestration MRV & carbon credits revenue.
- `POST /api/integrated-farming/plan` - ICAR circular bio-resource recycling and multi-enterprise modeling.
- `POST /api/post-harvest-aeration` - Grain drying, moisture removal, fan airflow CFM & shelf-life.
- `POST /api/polyhouse-climate` - Greenhouse ventilation, evaporative cooling pad, VPD & MIDH subsidy.
- `POST /api/stubble-biochar` - Parali crop residue pyrolysis yield, C:N composting & emission abatement.

### 4. Zero-Cost Agronomic Suite ($0 API Spend)
- `POST /api/mandi-fair-payout` - FCI / APMC Fair Average Quality (FAQ) statutory moisture deduction auditor.
- `POST /api/weed-management` - ICAR-DWR weed management and 15L knapsack tank dilution calculator.
- `POST /api/zecc-storage` - IARI Pusa Zero Energy Cool Chamber (ZECC) DIY storage planner & shelf-life extension.
- `POST /api/natural-farming/formulation` - Subhash Palekar Natural Farming (SPNF/ZBNF) drum batch scaler.
- `POST /api/fodder-silage/plan` - NDRI 365-day green fodder budget and 90-day lean silage trench sizing.
- `POST /api/nasa-power/gdd` - NASA POWER open agroclimatology & cumulative GDD thermal time tracker.

### 5. Security & Ownership Contingency Protocol (Plastic Man)
- `GET /api/contingency-protocol` (and `/api/plastic-man`) - Master ownership verification endpoint validating 21 author secret codes for **MegaTron alias Mohammed Razin H**.
- `cli.py` includes automatic interceptors for registered secret author codes.

---

## ⚡ How to Run

### 1. Setup Virtual Environment & Install Dependencies
```bash
# From the backend directory:
python -m venv .venv

# On Windows:
.\.venv\Scripts\pip install -r requirements.txt

# On Linux/macOS:
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Run the REST API Server
```bash
.\.venv\Scripts\python -m uvicorn app.main:app --reload --port 4343
```
- API Endpoint: `http://localhost:4343`
- Interactive Swagger API Docs: `http://localhost:4343/docs`
- Performance Benchmarks: `http://localhost:4343/api/benchmarks`

### 3. Run the Interactive CLI Wizard
```bash
.\.venv\Scripts\python cli.py
```

### 4. Run Automated Pytest Suite
```bash
.\.venv\Scripts\pytest -v tests/
```
All **74 automated unit, integration, and stress tests** pass in $< 2.0\text{s}$.
