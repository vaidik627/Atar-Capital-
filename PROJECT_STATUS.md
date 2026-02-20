# Project Status (Current)

## Goal

Generate an Excel output that matches the “Pre‑Bid Analysis / Model” layout (Actual years + 5-year projections) like the provided screenshots. The UI is currently rendering extracted + calculated + forecasted values that are intended to map into that Excel.

## Current State (What Works Today)

- Upload a PDF/image in the UI → backend runs OCR → backend extracts structured JSON → UI renders the analysis.
- Core extraction produces a single JSON object following the schema in `backend/schema.py`.
- Some metrics are extracted via dedicated model calls (to reduce prompt load and improve reliability):
  - Free Cash Flow (FCF): extracted + normalized + forecasted.
  - CAPEX: extracted via separate call and merged into `tale_of_the_tape.capex`.
  - Change in Working Capital: extracted via separate call and merged into `tale_of_the_tape.change_in_working_capital`.
- A CSV export exists (not Excel): backend can generate a simple CSV report from extracted JSON.

## High-Level Architecture

### Components

- **Frontend**: Static HTML/CSS/JS dashboard
  - Entry: `index.html`
  - UI logic: `js/dashboard.js`
  - Styling: `css/main.css`
- **Backend API**: Python Flask server
  - App + endpoints: `backend/app.py`
  - OCR: `backend/ocr_service.py`
  - Extraction + normalization + saving/loading: `backend/extraction.py`
  - Schema definition: `backend/schema.py`
  - CSV report export: `backend/report_generator.py`

### Tech Stack

- **Backend**
  - Python + Flask (`flask`, `flask-cors`)
  - OCR: Google Document AI (`google-cloud-documentai`) with fallback to `pypdf`
  - LLM extraction: `openai` (OpenAI SDK) with configurable base URL/model
  - Env config: `python-dotenv`
- **Frontend**
  - Vanilla JS (no framework)
  - HTML + CSS

### Data Flow (End-to-End)

1. **Upload**
   - UI uploads a file to `POST /api/documents/upload` (alias: `POST /api/extract`).
2. **OCR**
   - `backend/ocr_service.py` attempts Google Document AI (chunked for PDFs).
   - If credentials are missing or OCR fails → fallback text extraction using `pypdf`.
   - OCR text is saved to `backend/parsed_text/`.
3. **Extraction**
   - `backend/extraction.py` runs LLM-based extraction into the JSON schema.
   - Dedicated extractions are run for some sections (FCF/CAPEX/WC), then merged into the primary output.
4. **Normalization**
   - Extracted data is normalized into consistent formats (e.g., `free_cash_flow.historical` structure, forecast presence).
5. **Persistence**
   - Extracted JSON is saved to `backend/extracted_data/` (and a secondary copy next to OCR text, if available).
6. **Read / Render**
   - UI calls `GET /api/analysis/<deal_id>`.
   - Backend maps extracted JSON to the frontend format (header, revenue, profitMetrics, risks, etc.).
   - UI renders it inside the dashboard.
7. **Export (Current)**
   - `POST /api/reports/generate/<deal_id>` generates a CSV in `backend/reports/`.
   - `GET /api/reports/download/<filename>` downloads it.

## Backend Details

### OCR (Google Document AI + fallback)

- Config env vars:
  - `GOOGLE_PROJECT_ID`, `GOOGLE_LOCATION`, `GOOGLE_PROCESSOR_ID`
  - Credentials expected at `backend/credentials.json`
- PDF handling:
  - PDFs are split into chunks (15 pages each) before sending to Document AI.

### Extraction Strategy

The extraction pipeline is a hybrid:

- **LLM extraction** is used to convert OCR text into structured JSON.
- **Deterministic post-processing** is used to normalize outputs and to compute/ensure forecasts where possible (e.g., ensuring a 5-year FCF forecast is present).

#### Dedicated Extraction Calls

To improve consistency and reduce “prompt overload”, some metrics are extracted separately and merged:

- **FCF**: extracted separately into `free_cash_flow`, normalized, then forecasted.
- **CAPEX**: extracted separately into `tale_of_the_tape.capex`.
- **Change in Working Capital**: extracted separately into `tale_of_the_tape.change_in_working_capital`.

This pattern is used to keep the main extraction prompt smaller and to isolate difficult financial items.

### Storage

- `backend/parsed_text/`: OCR `.txt` output per upload
- `backend/extracted_data/`: extracted JSON per deal (timestamped)
- `backend/reports/`: generated CSV reports

## Frontend Details

- The UI is a dashboard that renders:
  - Header + company summary
  - Revenue (history/present/future)
  - Profit metrics table
  - Market intelligence + risks
  - Tale of the tape (CAPEX / ΔWC / 1x costs)
  - Free cash flow analysis with 5-year forecast

The UI is currently “data-driven”: it renders whatever is present in the extracted/normalized JSON.

## Mapping to Target Excel (What the Screenshots Imply)

The target Excel layout typically needs:

- **Financial statement lines by year** (Actual + Projections):
  - Revenue, COGS, Gross Profit, Operating Expenses, EBITDA, Adjustments, Adj. EBITDA, margins, etc.
- **Tale of the Tape by year**:
  - Adj. EBITDA, CAPEX, Change in WC, 1x Costs, Free Cash Flow
- **Below-EBITDA items** (often needed for a full model):
  - Interest, debt service, amortization schedules, revolver drawdowns, cash balances, etc.
- **Sources & Uses**:
  - Purchase price, transaction fees, equity, debt, seller note, etc.
- **Returns / distribution**:
  - MOIC, IRR, exit assumptions, equity bridge

Right now, the project focuses on “extract + show on UI”. The Excel requires a more rigid and complete “model representation” and far more derived calculations.

## Known Constraints / Risks

- OCR text can be noisy and lose table structure, which hurts year-by-year extraction.
- A single “giant prompt” approach will become fragile as Excel requirements expand.
- Year alignment, units, and sign conventions must be consistent for Excel math to work.
- Financial models require balancing checks (e.g., Revenue − COGS = Gross Profit) and cross-line validation.

## Configuration / Running

### Backend env vars

- LLM
  - `OPENAI_API_KEY`
  - `LLM_MODEL` (defaults in code)
  - `LLM_BASE_URL` (optional; enables non-default OpenAI-compatible providers)
- OCR (Google Document AI)
  - `GOOGLE_PROJECT_ID`
  - `GOOGLE_LOCATION`
  - `GOOGLE_PROCESSOR_ID`

### Run backend

- `python -m backend.app` (serves UI + API; default port 8000)

### Key API endpoints

- `POST /api/documents/upload` (file upload + OCR + extraction)
- `GET /api/analysis/<deal_id>` (frontend analysis payload)
- `POST /api/reports/generate/<deal_id>` (CSV report generation)
- `GET /api/reports/download/<filename>` (download report)
