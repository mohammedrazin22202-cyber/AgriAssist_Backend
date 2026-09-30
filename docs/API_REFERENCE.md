# AgriAssist Backend: Comprehensive API Reference & Agronomic Engine Specifications

## System Architectural Overview
AgriAssist is a zero-latency agronomic decision-support engine engineered using FastAPI, Pydantic v2, and deterministic agronomic algorithms. It models soil chemistry, crop phenology, post-harvest thermodynamics, market regulation standards, and dairy livestock bio-energetics across 100 Indian agricultural crops.

```
                              ┌────────────────────────────────────────┐
                              │           FastAPI REST API             │
                              │     (CORS Enabled / Localhost:4343)    │
                              └───────────────────┬────────────────────┘
                                                  │
             ┌────────────────────────────────────┼───────────────────────────────────┐
             │                                    │                                   │
             ▼                                    ▼                                   ▼
┌─────────────────────────┐          ┌─────────────────────────┐         ┌─────────────────────────┐
│ Crop Scoring Core       │          │ Precision Ag-Tech Suite │         │ Zero-Cost Engine Suite  │
│ - 100 Crops DB          │          │ - Drip Fertigation      │         │ - APMC Mandi FAQ Audit  │
│ - Soil Nutrient Balancing│         │ - Carbon Credit MRV     │         │ - ICAR-DWR Weed Doctor  │
│ - NPK Stoichiometry     │          │ - Integrated Farming    │         │ - Pusa ZECC Cool Chamber│
│ - 1-Year Crop Rotation  │          │ - Micro-climate VPD     │         │ - SPNF / ZBNF Scaler    │
│ - Financial Economics   │          │ - Parali Biochar Model  │         │ - NDRI Fodder & Silage  │
└─────────────────────────┘          └─────────────────────────┘         │ - NASA POWER GDD Thermal│
                                                                         └─────────────────────────┘
```

---

## 1. Mathematical & Scientific Formulations

### 1.1 Crop Suitability Index ($CSI$)
For each crop $c \in \mathcal{C}$ in the 100-crop repository:
$$CSI_c = w_{soil} S_{soil}(c) + w_{season} S_{season}(c) + w_{water} S_{water}(c) + w_{ph} S_{ph}(c) + w_{npk} S_{npk}(c)$$
Where:
- $S_{soil}(c) \in [0, 100]$: Evaluates physical soil texture compatibility (Alluvial, Black Regur, Red Laterite, Loamy, Clay).
- $S_{season}(c) \in [0, 100]$: Matches seasonal photoperiod & thermal windows (Kharif, Rabi, Zaid).
- $S_{water}(c) \in [0, 100]$: Water availability penalization factor (heavily penalizes high-irrigation crops like Sugarcane/Paddy during low-water drought regimes).

### 1.2 Stoichiometric Fertilizer Dosage
Given soil available nutrients $(N, P, K)$ and crop target requirements $(N_{req}, P_{req}, K_{req})$ in kg/ha:
$$\Delta N = \max(0, N_{req} - N_{soil})$$
$$\Delta P = \max(0, P_{req} - P_{soil})$$
$$\Delta K = \max(0, K_{req} - K_{soil})$$

Using commercial chemical grades:
- **DAP (18-46-0)** supplies all required Phosphorus:
  $$\text{DAP (kg)} = \frac{\Delta P}{0.46}$$
  $$\text{Nitrogen supplied by DAP} = \text{DAP (kg)} \times 0.18$$
- **Urea (46-0-0)** supplies remaining Nitrogen:
  $$\text{Urea (kg)} = \frac{\max(0, \Delta N - \text{N}_{DAP})}{0.46}$$
- **MOP / Muriate of Potash (0-0-60)** supplies Potassium:
  $$\text{MOP (kg)} = \frac{\Delta K}{0.60}$$

### 1.3 Cumulative Growing Degree Days ($GDD$) & Thermal Time
$$GDD = \sum_{t=t_{sowing}}^{t_{current}} \max\left(0, \frac{T_{max, t} + T_{min, t}}{2} - T_{base}\right)$$
Where $T_{base}$ is base temperature below which physiological development ceases ($5.0^\circ\text{C}$ for Wheat, $10.0^\circ\text{C}$ for Maize/Paddy, $15.0^\circ\text{C}$ for Cotton).

### 1.4 APMC Fair Average Quality (FAQ) Moisture Statutory Deduction
$$\text{Allowable Deduction (kg)} = W_{gross} \times \frac{\max(0, M_{measured} - M_{standard})}{100}$$
Excess moisture cut is strictly capped at FCI tolerances. Any deduction exceeding this limit is flagged as illegal under the APMC Model Act.

### 1.5 Pusa Zero Energy Cool Chamber (ZECC) Thermodynamics
$$\Delta T = \eta \cdot (T_{dry} - T_{wet})$$
Where evaporative saturation efficiency $\eta \approx 0.80 - 0.90$. The wet sand cavity drops ambient internal dry-bulb temperature by $10^\circ\text{C} - 15^\circ\text{C}$ while elevating relative humidity to $88\% - 95\%$, arresting fruit transpiration and chlorophyll degradation.

---

## 2. API Endpoints Catalog

### Core Diagnostics & Metadata
- `GET /api/health`: Returns API availability status and software engine version.
- `GET /api/benchmarks`: Real-time execution profiler assessing latency (mean, median, p95) and operations/second across 100 crops.
- `GET /api/metadata`: Returns supported soil classifications, agro-climatic zones, and seasonal parameters.
- `GET /api/crops`: Returns directory of all 100 mapped agricultural crops.
- `GET /api/crops/{crop_id}`: Comprehensive crop profile including MSP, 4-stage phenology, and disease susceptibility.

### Decision Support & Agronomic Prescriptions
- `POST /api/recommend`: Multi-factor crop ranking with net profit, investment cost, and fertilizer bag recommendations.
- `POST /api/fertilizer-prescription`: Stoichiometric Urea/DAP/MOP bag schedule with lime/gypsum pH amendments.
- `POST /api/rotation-plan`: Generates a balanced 1-year multi-crop rotation (Kharif $\to$ Rabi $\to$ Zaid) ensuring nitrogen recovery.
- `POST /api/plant-doctor/diagnose`: Rule-based Integrated Pest Management (IPM) symptoms diagnostic engine.

### Zero-Cost Agronomic Suite ($0 API Spend)
- `POST /api/mandi-fair-payout`: Audits APMC grain deductions against FCI Fair Average Quality statutory limits.
- `POST /api/weed-management`: Calibrates ICAR-DWR herbicide dosages, knapsack 15L spray dilution, and flat fan nozzle choices.
- `POST /api/zecc-storage`: Sizes Pusa Zero Energy Cool Chambers, bill of materials (bricks, sand, thatch), and produce shelf-life extension.
- `POST /api/natural-farming/formulation`: Dynamic drum batch scaler for Subhash Palekar recipes (Jeevamrut, Beejamrut, Agniastra, Neemastra).
- `POST /api/fodder-silage/plan`: Sizes NDRI 365-day green fodder budgets, 90-day lean silage trench pits, and 200L barrel silos.
- `POST /api/nasa-power/gdd`: Pulls NASA open agroclimatology reanalysis data to track cumulative thermal time and forecast harvest dates.

### Security Contingency Protocol (Plastic Man)
- `GET /api/contingency-protocol`: Cryptographic author verification endpoint protecting intellectual property and ownership integrity.

---

## 3. Data Integrity & Verification Standards
- **Zero-Cost Constraint**: No endpoint invokes billable third-party APIs (OpenAI, Google Maps Platform, Twilio).
- **Offline Readiness**: All algorithms support deterministic client-side fallbacks with exact formula parity.
- **Test Coverage**: Tested via automated pytest suite with $100\%$ pass rate across 74 unit, integration, and stress tests.
