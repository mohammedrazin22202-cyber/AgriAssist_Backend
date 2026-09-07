# AgriAssist Backend

A robust Python & FastAPI agronomic decision-support engine providing REST endpoints and an interactive CLI for recommending optimal crops, calculating fertilizer prescriptions, and designing 1-year multi-crop rotations.

## Project Structure
```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py          # FastAPI application with REST endpoints & CORS
│   ├── engine.py        # Multi-factor agronomic scoring algorithm
│   ├── agri_tools.py    # Fertilizer prescriber, farm economics & rotation planner
│   ├── database.py      # Knowledge base of 28+ crops with MSP & growth stages
│   ├── soil_presets.py  # Regional soil benchmarks & season metadata
│   └── models.py        # Pydantic schemas (Request / Response)
├── tests/
│   └── test_engine.py   # Automated pytest suite (100% passing)
├── cli.py               # Interactive terminal wizard with economics & rotation
├── requirements.txt     # Dependencies
├── Dockerfile           # Production container definition
└── README.md
```

## REST API Endpoints
- `GET /api/health` - Service health status
- `GET /api/metadata` - Soil presets, seasons, and farming budget options
- `POST /api/recommend` - Multi-factor crop ranking with net profit & fertilizer bags
- `POST /api/rotation-plan` - 1-Year Multi-Crop Rotation Plans (Kharif -> Rabi -> Zaid)
- `POST /api/fertilizer-prescription` - Stoichiometric Urea/DAP/MOP bags & Lime/Gypsum dosage
- `GET /api/crops` - Complete crop directory
- `GET /api/crops/{crop_id}` - Detailed agronomic profile with 4-stage growth timeline

## How to Run

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
- API will be accessible at: `http://localhost:4343`
- Interactive Swagger API docs: `http://localhost:4343/docs`
- Health check: `http://localhost:4343/api/health`

### 3. Run the Interactive CLI Wizard
```bash
.\.venv\Scripts\python cli.py
```

### 4. Run Automated Unit Tests
```bash
.\.venv\Scripts\pytest -v tests/
```
