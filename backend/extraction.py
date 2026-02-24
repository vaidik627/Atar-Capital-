"""
REFINED FINANCIAL EXTRACTION ENGINE
Extracts financial metrics from OCR text and returns JSON schema
"""
import os
import json
import re
import time
import traceback
from typing import Optional, Dict, Any, List
from openai import OpenAI
from .config import (
    LLM_API_KEY, 
    LLM_MODEL, 
    LLM_BASE_URL,
    MAX_OCR_CHARS, 
    MAX_TOKENS, 
    TEMPERATURE,
    EXTRACTED_DATA_DIR
)
from .schema import (
    get_extraction_schema,
    get_free_cash_flow_schema,
    get_capex_schema,
    get_change_in_working_capital_schema,
    get_balance_sheet_schema,
    get_debt_profile_schema,
    get_transaction_assumptions_schema,
    validate_schema
)
from .fallback_resolver import apply_fallback_resolution

# ============================================================================
# MAIN EXTRACTION FUNCTION
# ============================================================================

def extract_financial_data(ocr_text: str, api_key: str = None, deal_id: str = None, source_path: str = None, user_deal_value: str = None) -> Dict[str, Any]:
    """
    Extract financial metrics from OCR text and return structured JSON schema.
    
    Process:
    1. Validate input (OCR text, API key)
    2. Prepare enhanced extraction prompt with schema
    3. Call LLM API with JSON mode
    4. Parse and validate response against schema
    5. Save to file system
    6. Return JSON data
    
    Args:
    ocr_text (str): Raw text extracted from PDF via OCR
    api_key (str, optional): LLM API key (defaults to config)
    deal_id (str, optional): Deal identifier for file naming
    source_path (str, optional): Path to the source text file
    user_deal_value (str, optional): The user-inputted deal value for AI context
    
    Returns:
    dict: Structured financial data matching schema.py format
    
    Raises:
    ValueError: Invalid input (empty text, missing API key)
    RuntimeError: API call or processing failure
    """
    print("\n" + "="*80)
    print("🤖 FINANCIAL EXTRACTION ENGINE - STARTED")
    print("="*80)
    
    # -------------------------------------------------------------------------
    # STEP 1: INPUT VALIDATION
    # -------------------------------------------------------------------------
    api_key = api_key or LLM_API_KEY
    
    if not api_key:
        raise ValueError("❌ No LLM API key provided. Set in config.py or pass as argument.")
    
    if not ocr_text or len(ocr_text.strip()) < 10:
        raise ValueError(f"❌ OCR text too short: {len(ocr_text) if ocr_text else 0} chars (min 10)")
    
    print(f"✓ Input validated")
    print(f"  Deal ID: {deal_id or 'Not specified'}")
    print(f"  OCR Text: {len(ocr_text):,} characters")
    print(f"  Model: {LLM_MODEL}")
    
    # -------------------------------------------------------------------------
    # STEP 2: INITIALIZE LLM CLIENT
    # -------------------------------------------------------------------------
    try:
        client_config = {"api_key": api_key}
        if LLM_BASE_URL:
            client_config["base_url"] = LLM_BASE_URL
            print(f"✓ Using custom endpoint: {LLM_BASE_URL}")
        
        client = OpenAI(**client_config)
        print(f"✓ LLM client initialized")
        
    except Exception as e:
        raise RuntimeError(f"❌ Failed to initialize LLM client: {e}")
    
    # -------------------------------------------------------------------------
    # STEP 3: PREPARE INPUT (TRUNCATE IF NEEDED)
    # -------------------------------------------------------------------------
    if len(ocr_text) > MAX_OCR_CHARS:
        print(f"⚠️  Truncating OCR text: {len(ocr_text):,} → {MAX_OCR_CHARS:,} chars")
        ocr_text = ocr_text[:MAX_OCR_CHARS]
    
    # -------------------------------------------------------------------------
    # STEP 4: CALL LLM API FOR EXTRACTION
    # -------------------------------------------------------------------------
    print(f"\n🔍 Analyzing document with AI...")
    
    try:
        start_time = time.time()
        
        user_context = ""
        if user_deal_value:
            user_context = f"\n\n**USER CONTEXT:**\nThe user is considering this deal at a valuation of: {user_deal_value}.\nPlease use this valuation when making your AI Recommendation (Buy/Hold/Sell) and determining if it's a good investment based on the extracted financial metrics."

        response = client.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {
                    "role": "system", 
                    "content": _build_extraction_prompt()
                },
                {
                    "role": "user", 
                    "content": f"Extract all financial metrics from this document:{user_context}\n\n{ocr_text}"
                }
            ],
            response_format={"type": "json_object"},  # Force JSON output
            temperature=TEMPERATURE,
            max_tokens=MAX_TOKENS
        )
        
        elapsed = time.time() - start_time
        print(f"✓ LLM response received ({elapsed:.2f}s)")
        
    except Exception as e:
        error_msg = f"LLM API call failed: {str(e)}"
        print(f"❌ {error_msg}")
        traceback.print_exc()
        
        # Save error log for debugging
        if deal_id:
            _save_error_log(deal_id, error_msg, "API_FAILURE")
        
        raise RuntimeError(error_msg)
    
    # -------------------------------------------------------------------------
    # STEP 5: PARSE AND VALIDATE JSON RESPONSE
    # -------------------------------------------------------------------------
    try:
        raw_content = response.choices[0].message.content
        
        if not raw_content:
            raise ValueError("LLM returned empty response")
        
        print(f"✓ Response size: {len(raw_content):,} characters")
        
        # Parse JSON (handle potential markdown wrapping)
        extracted_data = _parse_json_safely(raw_content)
        print(f"✓ JSON parsed successfully")

        extracted_data = _normalize_extracted_data(extracted_data)

        try:
            capex_only = _extract_capex_separately(
                client=client,
                ocr_text=ocr_text,
                deal_id=deal_id
            )
            capex_obj = None
            if isinstance(capex_only, dict):
                tot = capex_only.get("tale_of_the_tape")
                if isinstance(tot, dict):
                    capex_obj = tot.get("capex")

            if isinstance(capex_obj, dict):
                tale = extracted_data.get("tale_of_the_tape")
                if not isinstance(tale, dict):
                    tale = {}
                tale = dict(tale)
                tale["capex"] = capex_obj
                extracted_data["tale_of_the_tape"] = tale

            extracted_data["tale_of_the_tape"] = _normalize_tale_of_the_tape(
                extracted_data.get("tale_of_the_tape"),
                extracted_data
            )
        except Exception as e:
            print(f"⚠️  Separate CAPEX extraction failed: {e}")
            extracted_data["tale_of_the_tape"] = _normalize_tale_of_the_tape(
                extracted_data.get("tale_of_the_tape"),
                extracted_data
            )

        try:
            wc_only = _extract_change_in_working_capital_separately(
                client=client,
                ocr_text=ocr_text,
                deal_id=deal_id
            )
            wc_obj = None
            if isinstance(wc_only, dict):
                tot = wc_only.get("tale_of_the_tape")
                if isinstance(tot, dict):
                    wc_obj = tot.get("change_in_working_capital")

            if isinstance(wc_obj, dict):
                tale = extracted_data.get("tale_of_the_tape")
                if not isinstance(tale, dict):
                    tale = {}
                tale = dict(tale)
                tale["change_in_working_capital"] = wc_obj
                extracted_data["tale_of_the_tape"] = tale

            extracted_data["tale_of_the_tape"] = _normalize_tale_of_the_tape(
                extracted_data.get("tale_of_the_tape"),
                extracted_data
            )
        except Exception as e:
            print(f"⚠️  Separate WC extraction failed: {e}")
            extracted_data["tale_of_the_tape"] = _normalize_tale_of_the_tape(
                extracted_data.get("tale_of_the_tape"),
                extracted_data
            )

        try:
            free_cash_flow_only = _extract_free_cash_flow_separately(
                client=client,
                ocr_text=ocr_text,
                deal_id=deal_id
            )
            if isinstance(free_cash_flow_only, dict) and free_cash_flow_only:
                extracted_data["free_cash_flow"] = _normalize_free_cash_flow(
                    free_cash_flow_only.get("free_cash_flow"),
                    extracted_data
                )
        except Exception as e:
            print(f"⚠️  Separate FCF extraction failed: {e}")
            extracted_data["free_cash_flow"] = _normalize_free_cash_flow(
                extracted_data.get("free_cash_flow"),
                extracted_data
            )
            
        try:
            bs_only = _extract_balance_sheet_separately(
                client=client,
                ocr_text=ocr_text,
                deal_id=deal_id
            )
            if isinstance(bs_only, dict) and "balance_sheet" in bs_only:
                extracted_data["balance_sheet"] = bs_only["balance_sheet"]
        except Exception as e:
            print(f"⚠️  Separate Balance Sheet extraction failed: {e}")

        try:
            dp_only = _extract_debt_profile_separately(
                client=client,
                ocr_text=ocr_text,
                deal_id=deal_id
            )
            if isinstance(dp_only, dict) and "debt_profile" in dp_only:
                extracted_data["debt_profile"] = dp_only["debt_profile"]
        except Exception as e:
            print(f"⚠️  Separate Debt Profile extraction failed: {e}")

        try:
            ta_only = _extract_transaction_assumptions_separately(
                client=client,
                ocr_text=ocr_text,
                deal_id=deal_id
            )
            if isinstance(ta_only, dict) and "transaction_assumptions" in ta_only:
                extracted_data["transaction_assumptions"] = ta_only["transaction_assumptions"]
        except Exception as e:
            print(f"⚠️  Separate Transaction Assumptions extraction failed: {e}")

        try:
            is_only = _extract_interest_schedule_separately(
                client=client,
                ocr_text=ocr_text,
                deal_id=deal_id
            )
            if isinstance(is_only, dict) and "interest_schedule" in is_only:
                extracted_data["interest_schedule"] = is_only["interest_schedule"]
        except Exception as e:
            print(f"⚠️  Separate Interest Schedule extraction failed: {e}")
            
        # -------------------------------------------------------------------------
        # APPLY FALLBACK RESOLVER (4-Step Safety Net)
        # -------------------------------------------------------------------------
        try:
            extracted_data = apply_fallback_resolution(extracted_data, ocr_text)
        except Exception as e:
            print(f"⚠️  Fallback Resolver failed (Continuing with raw AI data): {e}")
            traceback.print_exc()
        
        # Validate against schema
        is_valid, errors = validate_schema(extracted_data)
        
        if not is_valid:
            print(f"⚠️  Schema validation warnings:")
            for err in errors[:5]:  # Show first 5
                print(f"   - {err}")
        else:
            print(f"✓ Schema validation passed")
        
        # Log extracted summary
        _log_extraction_summary(extracted_data)
        
    except json.JSONDecodeError as e:
        error_msg = f"Failed to parse JSON: {e}"
        print(f"❌ {error_msg}")
        print(f"Raw response preview: {raw_content[:500]}...")
        
        if deal_id:
            _save_error_log(deal_id, f"{error_msg}\n\nRaw: {raw_content}", "JSON_PARSE_ERROR")
        
        raise RuntimeError(error_msg)
    
    except Exception as e:
        print(f"❌ Validation error: {e}")
        traceback.print_exc()
        raise

    # -------------------------------------------------------------------------
    # STEP 6: SAVE TO FILE SYSTEM
    # -------------------------------------------------------------------------
    if deal_id:
        print(f"\n💾 Saving extracted data...")
        
        saved_path = save_extracted_data(deal_id, extracted_data, source_path)
        
        if saved_path:
            print(f"✓ Data saved: {os.path.basename(saved_path)}")
        else:
            print(f"⚠️  File save failed (data still returned)")
    
    # -------------------------------------------------------------------------
    # COMPLETE
    # -------------------------------------------------------------------------
    print("\n" + "="*80)
    print("✅ EXTRACTION COMPLETE")
    print("="*80 + "\n")
    
    return extracted_data


def _extract_capex_separately(
    client: OpenAI,
    ocr_text: str,
    deal_id: Optional[str] = None
) -> Dict[str, Any]:
    if len(ocr_text) > MAX_OCR_CHARS:
        ocr_text = ocr_text[:MAX_OCR_CHARS]

    try:
        response = client.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {"role": "system", "content": _build_capex_prompt()},
                {"role": "user", "content": f"Extract CAPEX from this OCR text:\n\n{ocr_text}"},
            ],
            response_format={"type": "json_object"},
            temperature=TEMPERATURE,
            max_tokens=MAX_TOKENS
        )
    except Exception as e:
        error_msg = f"CAPEX-only LLM API call failed: {str(e)}"
        print(f"❌ {error_msg}")
        if deal_id:
            _save_error_log(deal_id, error_msg, "CAPEX_API_FAILURE")
        raise

    raw_content = response.choices[0].message.content
    if not raw_content:
        raise ValueError("CAPEX-only LLM returned empty response")

    capex_only = _parse_json_safely(raw_content)
    if not isinstance(capex_only, dict):
        raise ValueError("CAPEX-only LLM returned non-object JSON")
    return capex_only


def _build_capex_prompt() -> str:
    capex_schema = json.dumps(get_capex_schema(), indent=2)
    return f"""
You are a financial data extraction assistant.

Your task is to determine CAPEX for all available years from the provided OCR financial text.

You MUST follow the hierarchy strictly.
DO NOT hallucinate.
DO NOT assume missing values.
DO NOT fabricate inputs.

Return ONLY valid JSON matching this schema exactly:
{capex_schema}

General Rules (Strict):
- Extract values exactly as written.
- Preserve units and signs.
- Preserve year labels exactly (FY24, FY25, FY26B, FY27F, 2025E, etc.). Do NOT create missing years.
- If inputs are insufficient, return "-" for that year.

Step 1 — Direct Search (Priority)
- Search for: Capital Expenditure, Capital Expenditures, CAPEX, Purchase of PPE, Additions to Fixed Assets.
- If found: extract year-wise as written. source="direct".

Step 2 — Calculate ONLY IF ALL PRESENT
- Only calculate if BOTH years have:
  - Opening Net PPE
  - Closing Net PPE
  - Depreciation is explicitly given
- Formula: CAPEX = Closing PPE - Opening PPE + Depreciation
- If depreciation is missing: DO NOT CALCULATE. Return "-".
- source="calculated".

Output Format (Strict)
- Populate `tale_of_the_tape.capex.year_wise`.
- For each year key: {{ "value": "<exact>", "source": "<source>" }}.
- Allowed sources: direct | calculated | not_found
- Do NOT include keys like "change", "total", "average" inside `year_wise`. Only specific years.
"""


def _extract_change_in_working_capital_separately(
    client: OpenAI,
    ocr_text: str,
    deal_id: Optional[str] = None
) -> Dict[str, Any]:
    if len(ocr_text) > MAX_OCR_CHARS:
        ocr_text = ocr_text[:MAX_OCR_CHARS]

    try:
        response = client.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {"role": "system", "content": _build_change_in_working_capital_prompt()},
                {"role": "user", "content": f"Extract Change in Working Capital (ΔWC) from this OCR text:\n\n{ocr_text}"},
            ],
            response_format={"type": "json_object"},
            temperature=TEMPERATURE,
            max_tokens=MAX_TOKENS
        )
    except Exception as e:
        error_msg = f"WC-only LLM API call failed: {str(e)}"
        print(f"❌ {error_msg}")
        if deal_id:
            _save_error_log(deal_id, error_msg, "WC_API_FAILURE")
        raise

    raw_content = response.choices[0].message.content
    if not raw_content:
        raise ValueError("WC-only LLM returned empty response")

    wc_only = _parse_json_safely(raw_content)
    if not isinstance(wc_only, dict):
        raise ValueError("WC-only LLM returned non-object JSON")
    return wc_only


def _build_change_in_working_capital_prompt() -> str:
    wc_schema = json.dumps(get_change_in_working_capital_schema(), indent=2)
    return f"""
You are a financial data extraction assistant.

Your task is to determine Change in Working Capital (ΔWC) for all available years from the provided OCR financial text.

You MUST follow the hierarchy strictly.
DO NOT hallucinate.
DO NOT assume missing values.
DO NOT fabricate inputs.

Return ONLY valid JSON matching this schema exactly:
{wc_schema}

General Rules (Strict):
- Extract values exactly as written in the OCR text.
- Preserve units and sign (e.g., $1.2M, (3.4), -5,000).
- Preserve year labels exactly (FY24, 2025E, FY26B, FY27F, etc.). Do NOT create missing years.
- If data is insufficient -> return "-" and source="not_found".
- Return pure mathematical result; do NOT flip sign for cash flow interpretation.

Step 1 — Direct Extraction (Highest Priority)
- Search for explicit mentions of:
  - Change in Working Capital
  - Change in Net Working Capital
  - Change in NWC
  - Net change in working capital
  - Increase (Decrease) in Working Capital
- If found:
  - Extract values year-wise exactly as written.
  - Do NOT calculate.
  - source="direct"

Step 2 — Calculate using Net Working Capital
- If direct ΔWC is NOT found, search for:
  - Net Working Capital
  - Adjusted Net Working Capital
- If Net Working Capital values exist for at least two consecutive years:
  - For each year N (except the first available year):
    - Change in WC (Year N) = NWC (Year N) − NWC (Year N-1)
  - STRICT:
    - Only calculate when BOTH years are available.
    - Do NOT calculate if only one year exists.
    - Do NOT interpolate missing years.
    - Preserve sign exactly.
    - source="calculated"

Step 3 — Calculate using components (if NWC not given)
- If Net Working Capital is NOT directly given, but BOTH exist for multiple years:
  - Total Current Assets
  - Total Current Liabilities
- Then:
  - For each year: NWC = Current Assets − Current Liabilities
  - For each year N (except the first available year):
    - Change in WC (Year N) = NWC (Year N) − NWC (Year N-1)
  - STRICT:
    - Do NOT compute if any required value is missing.
    - Do NOT use partial components (e.g., inventory only).
    - Do NOT estimate missing liabilities.
    - If incomplete -> return "-" and source="not_found".
    - source="calculated"

Output Format (Strict)
- Populate `tale_of_the_tape.change_in_working_capital.year_wise`.
- For each year key: {{ "value": "<exact>", "source": "<source>" }}.
- Allowed sources: direct | calculated | not_found
- Do NOT include keys like "change", "total", "average" inside `year_wise`. Only specific years.
"""


def _extract_free_cash_flow_separately(
    client: OpenAI,
    ocr_text: str,
    deal_id: Optional[str] = None
) -> Dict[str, Any]:
    if len(ocr_text) > MAX_OCR_CHARS:
        ocr_text = ocr_text[:MAX_OCR_CHARS]

    try:
        response = client.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {"role": "system", "content": _build_free_cash_flow_prompt()},
                {"role": "user", "content": f"Extract and forecast Free Cash Flow from this OCR text:\n\n{ocr_text}"},
            ],
            response_format={"type": "json_object"},
            temperature=TEMPERATURE,
            max_tokens=MAX_TOKENS
        )
    except Exception as e:
        error_msg = f"FCF-only LLM API call failed: {str(e)}"
        print(f"❌ {error_msg}")
        if deal_id:
            _save_error_log(deal_id, error_msg, "FCF_API_FAILURE")
        raise

    raw_content = response.choices[0].message.content
    if not raw_content:
        raise ValueError("FCF-only LLM returned empty response")

    fcf_only = _parse_json_safely(raw_content)
    if not isinstance(fcf_only, dict):
        raise ValueError("FCF-only LLM returned non-object JSON")
    return fcf_only


def _build_free_cash_flow_prompt() -> str:
    fcf_schema = json.dumps(get_free_cash_flow_schema(), indent=2)
    return f"""
You are a financial data extraction and forecasting assistant.

Your task is to determine Free Cash Flow (FCF) for all available historical, current, and forecast years from the provided OCR financial text.

You MUST follow the hierarchy strictly.
DO NOT hallucinate.
DO NOT assume missing values.
DO NOT fabricate inputs.
If insufficient data exists for a step, move to the next allowed step.

Return ONLY valid JSON matching this schema exactly:
{fcf_schema}

General Rules:
- Extract values exactly as written.
- Preserve units and signs.
- Preserve year labels exactly (FY24, 2025E, 2026F, FY26B, FY27F, etc.).
- Do NOT normalize units unless clearly stated.
- Do NOT invent missing years.
- If a required input is missing → do NOT calculate using that method.

Step 1 — Direct Extraction (Highest Priority)
- Search for explicit mentions of:
  - Free Cash Flow
  - FCF
  - Free Cash Flow to Firm
  - Free Cash Flow to Equity
  - Cash Flow After Capex
- If found:
  - Populate `free_cash_flow.historical` year-wise exactly as written.
  - source="direct"
  - method="direct"
  - After direct extraction, still attempt Step 2 to fill any missing years (if inputs exist).

Step 2 — Calculate (Fill Missing Years When Possible)
- Preferred calculation:
  - If BOTH exist for the same year:
    - Cash Flow from Operating Activities (Operating Cash Flow)
    - Capital Expenditures (CAPEX)
  - Then:
    - FCF = Operating Cash Flow − CAPEX
    - method="OCF_minus_CAPEX"
    - source="calculated"
- Alternative calculation (only if above not available):
  - If ALL exist for the same year:
    - EBITDA
    - Change in Working Capital
    - CAPEX
    - Cash Taxes (only if explicitly provided)
  - Then:
    - FCF = EBITDA − Change in Working Capital − CAPEX − Cash Taxes (if clearly disclosed)
    - method="EBITDA_based"
    - source="calculated"
- STRICT:
  - Do NOT assume tax rate.
  - Do NOT estimate depreciation.
  - Do NOT infer working capital.
  - If any required component missing → do NOT calculate.

Step 3 — Forecast Next 5 Years (Mandatory)
- Forecast MUST be produced in ALL cases (whether direct or calculated FCF exists or not).
- Inside forecast_next_5_years, include exactly five forecast year keys (in addition to base_year/growth_rate_used/methodology).
- If Revenue exists and any deterministic forecasting method applies, populate the 5 forecast year values (do NOT output "-" for forecast values just because historical FCF is missing).
- Forecasting must follow deterministic rules:
  - A) If historical FCF exists for ≥ 3 years:
    - Compute CAGR of last 3 available FCF years.
    - Forecast next 5 years using that CAGR.
    - methodology="FCF_CAGR"
  - B) If only 1–2 years of FCF exist:
    - Use Revenue CAGR (last 3 years if available).
    - Apply historical average FCF Margin: FCF Margin = FCF / Revenue
    - Projected FCF = Projected Revenue × Avg FCF Margin
    - methodology="Revenue_margin_based"
  - C) If NO FCF available but EBITDA & CAPEX exist:
    - Estimate FCF Margin using:
      - If WC available: FCF ≈ EBITDA − CAPEX − Change in WC
      - If WC missing: FCF ≈ EBITDA − CAPEX
    - Forecast using Revenue CAGR.
    - methodology="EBITDA_proxy"
  - D) If only Revenue exists:
    - Base FCF Margin = 5% of revenue ONLY IF explicitly no financial components exist.
    - If revenue missing → forecast="-"
    - methodology="industry_proxy"
- Forecast rules:
  - Use most recent actual year as base (if available).
  - Clearly state growth rate used.
  - Do NOT invent macro assumptions.
  - Do NOT exceed historical growth volatility.
  - If insufficient data → forecast="-" and methodology="-".

Sign Convention
- Return mathematical values only.
- Positive = cash generated.

Output Format (Strict)
- `free_cash_flow.historical` must include any year where FCF is found or calculable:
  - `free_cash_flow.historical[<YEAR_LABEL>] = {"value":"<number or exact text>", "source":"direct|calculated|not_found", "method":"direct|OCF_minus_CAPEX|EBITDA_based|-"}`
- Always return `free_cash_flow.forecast_next_5_years` with base_year/growth_rate_used/methodology and exactly 5 forecast years.

Example Output Shape (Illustrative)
{{
  "free_cash_flow": {{
    "historical": {{
      "FY2023": {{"value": "12.3", "source": "direct", "method": "direct"}},
      "FY2024": {{"value": "10.1", "source": "calculated", "method": "OCF_minus_CAPEX"}}
    }},
    "forecast_next_5_years": {{
      "base_year": "2024",
      "growth_rate_used": "8%",
      "methodology": "FCF_CAGR",
      "2025E": "10.9",
      "2026E": "11.8",
      "2027E": "12.7",
      "2028E": "13.7",
      "2029E": "14.8"
    }}
  }}
}}
"""


def _extract_balance_sheet_separately(
    client: OpenAI,
    ocr_text: str,
    deal_id: Optional[str] = None
) -> Dict[str, Any]:
    if len(ocr_text) > MAX_OCR_CHARS:
        ocr_text = ocr_text[:MAX_OCR_CHARS]

    try:
        response = client.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {"role": "system", "content": _build_balance_sheet_prompt()},
                {"role": "user", "content": f"Extract Balance Sheet data from this OCR text:\n\n{ocr_text}"},
            ],
            response_format={"type": "json_object"},
            temperature=TEMPERATURE,
            max_tokens=MAX_TOKENS
        )
    except Exception as e:
        error_msg = f"Balance Sheet LLM API call failed: {str(e)}"
        print(f"❌ {error_msg}")
        if deal_id:
            _save_error_log(deal_id, error_msg, "BS_API_FAILURE")
        raise

    raw_content = response.choices[0].message.content
    bs_only = _parse_json_safely(raw_content)
    return bs_only


def _build_balance_sheet_prompt() -> str:
    schema = json.dumps(get_balance_sheet_schema(), indent=2)
    return f"""
You are a financial data extraction assistant.
Extract Balance Sheet items for all available historical years.

Return ONLY valid JSON matching this schema exactly:
{schema}

Instructions:
1. Identify all balance sheet assets, liabilities, and equity sections.
2. For "assets", extract items like "Cash and cash equivalents", "Accounts receivable", "Inventories", "Property, plant, and equipment", "Intangible assets".
3. For "liabilities", extract items like "Accounts payable", "Current portion of long-term debt", "Long term debt", "Revolver", "Term Loan".
4. For "equity", extract equity/net assets.
5. Create an object for each item, listing its values by period (e.g. "FY21", "FY22").
6. Extract values strictly as written (do not flip signs unexpectedly).
7. If the balance sheet is completely missing, return empty arrays.
"""


def _extract_debt_profile_separately(
    client: OpenAI,
    ocr_text: str,
    deal_id: Optional[str] = None
) -> Dict[str, Any]:
    if len(ocr_text) > MAX_OCR_CHARS:
        ocr_text = ocr_text[:MAX_OCR_CHARS]

    try:
        response = client.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {"role": "system", "content": _build_debt_profile_prompt()},
                {"role": "user", "content": f"Extract Debt Profile / Facilities data from this OCR text:\n\n{ocr_text}"},
            ],
            response_format={"type": "json_object"},
            temperature=TEMPERATURE,
            max_tokens=MAX_TOKENS
        )
    except Exception as e:
        error_msg = f"Debt Profile LLM API call failed: {str(e)}"
        print(f"❌ {error_msg}")
        if deal_id:
            _save_error_log(deal_id, error_msg, "DEBT_API_FAILURE")
        raise

    raw_content = response.choices[0].message.content
    dp_only = _parse_json_safely(raw_content)
    return dp_only


def _build_debt_profile_prompt() -> str:
    schema = json.dumps(get_debt_profile_schema(), indent=2)
    return f"""
You are a financial data extraction assistant.
Extract information about the company's Debt Profile, Credit Facilities, Term Loans, and Revolvers.

Return ONLY valid JSON matching this schema exactly:
{schema}

Instructions:
1. Search the document for sections labeled "Capital Structure", "Debt", "Financing", "Credit Agreement", "Facilities".
2. Identify each specific debt facility (e.g. "Revolving Credit Facility", "Term Loan A", "Subordinated Debt", "Seller Note").
3. For each facility, extract the current balance/outstanding amount.
4. Extract the interest rate (often a percentage or spread, e.g. "SOFR + 4.5%". For the percentage, provide the total approximate % if possible, or just the main number). Use null if missing.
5. Extract the mandatory annual amortization amount (often expressed in $ millions). Use null if missing.
6. If no debt profile is found, return an empty array for facilities.
"""


# ============================================================================
# FILE OPERATIONS
# ============================================================================

def save_extracted_data(deal_id: str, data: Dict[str, Any], source_path: str = None) -> Optional[str]:
    """
    Save extracted data to JSON file with verification.
    Also saves a copy to the source directory if source_path is provided.
    
    Args:
        deal_id: Deal identifier
        data: Extracted financial data
        source_path: Path to source OCR text file (optional)
        
    Returns:
        str: Path to saved file (in extracted_data dir), or None if failed
    """
    try:
        # Generate filename with timestamp
        timestamp = int(time.time())
        filename = f"{deal_id}_{timestamp}.json"
        filepath = os.path.join(EXTRACTED_DATA_DIR, filename)
        
        # Ensure directory exists
        os.makedirs(EXTRACTED_DATA_DIR, exist_ok=True)
        
        # Write file
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            f.flush()
            os.fsync(f.fileno())  # Force disk write
            
        # ---------------------------------------------------------------------
        # SECONDARY SAVE: parsed_text/[basename]_extracted.json
        # ---------------------------------------------------------------------
        if source_path:
            try:
                # E.g. /path/to/Project NetworkCIP... .txt -> /path/to/Project NetworkCIP..._extracted.json
                src_dir = os.path.dirname(source_path)
                src_basename = os.path.basename(source_path)
                src_name = os.path.splitext(src_basename)[0]
                
                secondary_filename = f"{src_name}_extracted.json"
                secondary_path = os.path.join(src_dir, secondary_filename)
                
                with open(secondary_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                    f.flush()
                    os.fsync(f.fileno())
                
                print(f"✓ Also saved schema to: {secondary_filename}")
                
            except Exception as e:
                print(f"⚠️ Failed to save secondary copy to parsed_text: {e}")
        
        # Verify file was written (primary)
        if not os.path.exists(filepath):
            raise IOError("File not found after write")
        
        file_size = os.path.getsize(filepath)
        if file_size == 0:
            raise IOError("File is empty after write")
        
        # Verify JSON integrity
        with open(filepath, 'r', encoding='utf-8') as f:
            verification = json.load(f)
            if not verification:
                raise ValueError("Saved file contains empty JSON")
        
        return filepath
        
    except Exception as e:
        print(f"❌ Save failed: {e}")
        traceback.print_exc()
        return None


def load_extracted_data(deal_id: str) -> Optional[Dict[str, Any]]:
    """
    Load the most recent extracted data for a deal.
    
    Args:
        deal_id: Deal identifier
        
    Returns:
        dict: Extracted data, or None if not found
    """
    try:
        if not os.path.exists(EXTRACTED_DATA_DIR):
            return None
        
        # Find all files for this deal
        files = [
            f for f in os.listdir(EXTRACTED_DATA_DIR)
            if (f.startswith(f"{deal_id}_") or f == f"{deal_id}.json") and f.endswith('.json') and 'ERROR' not in f
        ]
        
        if not files:
            return None
        
        # Sort by timestamp (newest first)
        files.sort(reverse=True)
        latest_file = os.path.join(EXTRACTED_DATA_DIR, files[0])
        
        # Load and return
        with open(latest_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        data = _normalize_extracted_data(data)
        
        print(f"📂 Loaded: {os.path.basename(latest_file)}")
        return data
        
    except Exception as e:
        print(f"❌ Load failed for {deal_id}: {e}")
        return None


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def _build_extraction_prompt() -> str:
    """
    Build the system prompt for financial extraction.
    This tells the LLM exactly what to extract and in what format.
    """
    schema = get_extraction_schema()
    
    return f"""You are an expert financial analyst AI specialized in extracting structured data from investment documents.

Your task is to analyze OCR-extracted text from financial documents and extract key financial metrics into a structured JSON format.

**OUTPUT SCHEMA:**
You must return data matching this exact structure:

{json.dumps(schema, indent=2)}

**EXTRACTION GUIDELINES:**

1. **Company Information:**
   - Extract company name
   - Extract currency code (e.g., "USD", "EUR", "GBP"). If not explicitly stated, infer from symbols ($ -> USD, € -> EUR, £ -> GBP).
   - Write a concise company summary (2-3 sentences)
   - Note where you found this information (source_context)

2. **Revenue:**
   - Extract historical revenue (past years)
   - Current/present revenue (most recent period)
   - Projected/future revenue (forecasts)
   - Include period (e.g., "FY2023", "Q1 2024"), value, and unit (millions/thousands)

3. **Profit Metrics (COMPREHENSIVE):**
   - **MUST extract EXACTLY from the "Income Statement" table.**
   - **Do NOT calculate. Do NOT infer. Do NOT interpolate.** if it is missing, return empty.
   - **Gross Profit:** Extract exact values.
   - **Operating Expenses:** Extract exact value from the row labeled "Operating Expenses" or similar total operating cost rows.
   - **Operating Income:** Extract operating profit/loss.
   - **EBITDA:** Extract exactly as written. Do NOT compute EBITDA from revenue.
   - **Adjusted EBITDA:** Extract exactly as written if available.
   - **Net Income:** Extract Net Income / Net Profit after tax.
   - **Margins:** Do NOT re-calculate margins. Extract ONLY if explicitly written.
   - Store as arrays with `period`, `value` (number), `unit`, `source_context`.
   - **CRITICAL YEAR SUFFIX RULE FOR PERIODS**:
     - Extract the suffix EXACTLY from the column header.
     - If it ends in "A" -> Actual.
     - If it ends in "B", "E", "F", "R", "M" -> Forecast/Not Actual.
     - If NO suffix is present: if the table title contains 'Forecast', append 'E'. If the table title contains 'Income Statement' and contains FYXX only, append 'A'.

4. **Market Intelligence (HIGH PRIORITY):**
   - **Industry Position:** Explicitly state the company's rank (e.g., "#1 in US", "Market Leader"). If not stated, infer from context (e.g., "leading provider" -> "Top Tier").
   - **Market Size (TAM/SAM/SOM):** Extract the Total Addressable Market (TAM) or general market size if available. 
     - **Strategy:** Look for "Global Market Size", "Industry Value", "CAGR", "TAM".
     - **Inference:** If company specific TAM is missing, use the general industry size mentioned in the market overview section.
     - **Format:** Return as a string value (e.g., "$50B Global Market", "Growing to $12B by 2025").
   - **Market Share:** Extract percentage (e.g., "15% share"). If exact number is missing but descriptive text exists (e.g., "dominant share", "majority of market"), use that phrase.
   - **Competitors:** Extract ALL named competitors. If none are named, look for "competition" sections and summarize descriptions.
   - **Market Trends:** Extract key growth drivers and headwinds.
   - **Customer Base:** Summarize target audience (e.g., "Fortune 500", "SMEs").
   - **Geographic Presence:** List regions/countries of operation.
   - **Context:** Always provide the source text context for these findings to verify accuracy.

5. **Risk Analysis (CRITICAL SECTION):**
   - You MUST identify and categorize risks. If a section titled "Risks" is missing, **INFER** risks from the context (e.g., "highly competitive market" -> Market Risk, "dependent on key suppliers" -> Operational Risk).
   - **Operational Risks:** Supply chain issues, key person dependency, technology failure, integration risks.
   - **Financial Risks:** Currency fluctuation, high leverage, liquidity constraints, customer concentration.
   - **Market Risks:** Competition, pricing pressure, demand changes, economic downturns.
   - **Regulatory Risks:** Legal changes, compliance costs, environmental regulations, pending litigation.
   - Populate the lists `operational_risks`, `financial_risks`, `market_risks`, `regulatory_risks` with specific bullet points.
   - Do NOT leave these empty if any risks can be reasonably inferred.

6. **AI Recommendation:**
   - Based on the data, provide Buy/Hold/Sell recommendation
   - Give confidence percentage (0-100)
   - Explain rationale briefly

7. **Section 7: Tale of the Tape (Three Core Metrics)**
      - **Task:** Extract and/or calculate for all available years:
        1) CAPEX
        2) Change in Working Capital
        3) 1x Cost (Non-Recurring / EBITDA Normalizations)

      - **General Rules (Strict):**
        - Never hallucinate. Never assume. Never estimate.
        - Extract values exactly as written.
        - Preserve units and signs.
        - Preserve year labels exactly (FY24, FY25, FY26B, etc.). Do NOT create artificial years.
        - If inputs are insufficient, return "-" for that year.
        - If only one year exists for a change calculation, return "-".
        - If only two years exist, calculate change for the later year only.

      - **Part A: CAPEX**
        - Do NOT extract or calculate CAPEX in this call.
        - Leave `tale_of_the_tape.capex` as an empty object or placeholders.
        - CAPEX is extracted in a separate dedicated extraction step.

      - **Part B: Change in Working Capital**
        - Do NOT extract or calculate Change in Working Capital in this call.
        - Leave `tale_of_the_tape.change_in_working_capital` as an empty object or placeholders.
        - Change in Working Capital is extracted in a separate dedicated extraction step.

      - **Part C: 1x Cost (Non-Recurring / EBITDA Normalizations)**
        - **Step 3A — Direct Extraction (Priority):**
          - Search for: "Total normalizations", "EBITDA normalizations", "Non-recurring", "Add-backs", "EBITDA reconciliation".
          - If total normalizations table exists: extract value exactly. source="direct".
        - **Step 3B — Calculate from EBITDA Bridge:**
          - If BOTH exist for same year:
            - Reported EBITDA
            - Normalized / Adjusted EBITDA
          - Then:
            - 1x = Adjusted EBITDA - Reported EBITDA
            - source="calculated_from_bridge"
        - Otherwise: return "-" and source="not_found".

      - **Strict Output Format (within schema):**
        - Populate `tale_of_the_tape.one_time_cost.year_wise`.
        - For each year key: `{{ "value": "<exact>", "source": "<source>" }}`.
        - Allowed sources:
          - 1x: direct | calculated_from_bridge | not_found
        - Do NOT include keys like "change", "total", "average" inside `year_wise`. Only specific years.

      - **Section 8: Free Cash Flow (FCF)**
        - Do NOT extract or forecast Free Cash Flow in this call.
        - Leave `free_cash_flow` as an empty object or placeholders.
        - Free Cash Flow is extracted in a separate dedicated extraction step.

**IMPORTANT RULES:**
- Output **ONLY** valid JSON (no markdown, no code blocks)
- If data is not found:
  - For `tale_of_the_tape.*.year_wise[year].value`, use "-" and source "not_found"
  - For missing lists, use `[]`
  - For missing scalar fields, use `null`
- Do NOT fabricate numbers - only extract what's in the document
- Include source_context to show where data was found
- Use confidence levels: "high", "medium", "low"
- For Revenue / Profit Metrics arrays, `value` should be a number where possible.

Extract the data now."""


def _normalize_extracted_data(extracted_data: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(extracted_data, dict):
        return get_extraction_schema()

    extracted_data = dict(extracted_data)
    extracted_data["tale_of_the_tape"] = _normalize_tale_of_the_tape(
        extracted_data.get("tale_of_the_tape"),
        extracted_data
    )
    extracted_data["free_cash_flow"] = _normalize_free_cash_flow(
        extracted_data.get("free_cash_flow"),
        extracted_data
    )

    return extracted_data


def normalize_extracted_data(extracted_data: Dict[str, Any]) -> Dict[str, Any]:
    return _normalize_extracted_data(extracted_data)


def _normalize_free_cash_flow(free_cash_flow: Any, extracted_data_root: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(free_cash_flow, dict):
        free_cash_flow = {}

    normalized = dict(free_cash_flow)
    historical = normalized.get("historical")

    if not isinstance(historical, dict):
        year_wise = normalized.get("year_wise")
        if isinstance(year_wise, dict):
            historical = year_wise
        else:
            historical = {}

    normalized_historical: Dict[str, Dict[str, Any]] = {}
    for year, val in historical.items():
        if isinstance(val, dict):
            value = val.get("value")
            source = val.get("source")
            method = val.get("method")
        else:
            value = val
            source = None
            method = None

        normalized_historical[str(year)] = {
            "value": "-" if value is None or value == "" else str(value),
            "source": str(source) if source else "not_found",
            "method": str(method) if method else "-"
        }

    forecast = normalized.get("forecast_next_5_years")
    if not isinstance(forecast, dict):
        forecast = {}

    normalized_forecast = dict(forecast)
    normalized_forecast.setdefault("base_year", "")
    normalized_forecast.setdefault("growth_rate_used", "")
    normalized_forecast.setdefault("methodology", "-")

    normalized_fcf = {
        "historical": normalized_historical,
        "forecast_next_5_years": normalized_forecast
    }

    normalized_fcf = _ensure_fcf_historical(normalized_fcf, extracted_data_root)
    return _ensure_fcf_forecast(normalized_fcf, extracted_data_root)


def _ensure_fcf_historical(
    normalized_fcf: Dict[str, Any],
    extracted_data_root: Dict[str, Any]
) -> Dict[str, Any]:
    if not isinstance(normalized_fcf, dict):
        normalized_fcf = {}

    historical = normalized_fcf.get("historical")
    if not isinstance(historical, dict):
        historical = {}
    historical = dict(historical)

    def has_numeric_value(item: Any) -> bool:
        if not isinstance(item, dict):
            return False
        return _parse_number(item.get("value")) is not None

    has_any_historical = any(has_numeric_value(v) for v in historical.values())

    profit = extracted_data_root.get("profit_metrics")
    profit = profit if isinstance(profit, dict) else {}

    def collect_period_label_map(items: Any) -> Dict[int, str]:
        out: Dict[int, str] = {}
        if not isinstance(items, list):
            return out
        for item in items:
            if not isinstance(item, dict):
                continue
            period = item.get("period")
            y = _parse_year_int(str(period))
            if y is None:
                continue
            out.setdefault(y, str(period))
        return out

    def collect_tale_year_label_map(metric_key: str) -> Dict[int, str]:
        tale = extracted_data_root.get("tale_of_the_tape")
        if not isinstance(tale, dict):
            return {}
        metric = tale.get(metric_key)
        if not isinstance(metric, dict):
            return {}
        year_wise = metric.get("year_wise")
        if not isinstance(year_wise, dict):
            return {}
        out: Dict[int, str] = {}
        for label in year_wise.keys():
            y = _parse_year_int(str(label))
            if y is None:
                continue
            out.setdefault(y, str(label))
        return out

    fcf_items = profit.get("free_cash_flow")
    fcf_label_map = collect_period_label_map(fcf_items)
    for item in fcf_items if isinstance(fcf_items, list) else []:
        if not isinstance(item, dict):
            continue
        period = item.get("period")
        y = _parse_year_int(str(period))
        if y is None:
            continue
        v = item.get("value")
        if v is None:
            continue
        label = str(period)
        existing = historical.get(label)
        if isinstance(existing, dict) and _parse_number(existing.get("value")) is not None:
            continue
        historical[label] = {
            "value": str(v),
            "source": "direct",
            "method": "direct"
        }

    ocf_points = _collect_profit_metric_points(extracted_data_root, "operating_cash_flow")
    capex_points = _collect_tale_metric_points(extracted_data_root, "capex")
    if ocf_points and capex_points:
        ocf_by_year = {y: v for y, v in ocf_points}
        capex_by_year = {y: v for y, v in capex_points}
        ocf_label_map = collect_period_label_map(profit.get("operating_cash_flow"))
        capex_label_map = collect_tale_year_label_map("capex")

        years = sorted(set(ocf_by_year.keys()) & set(capex_by_year.keys()))
        for y in years:
            ocf_val = ocf_by_year.get(y)
            capex_val = capex_by_year.get(y)
            if ocf_val is None or capex_val is None:
                continue
            fcf_calc = ocf_val - abs(capex_val)
            label = capex_label_map.get(y) or ocf_label_map.get(y) or fcf_label_map.get(y) or str(y)
            existing = historical.get(label)
            if isinstance(existing, dict) and _parse_number(existing.get("value")) is not None:
                continue
            historical[label] = {
                "value": _format_number(fcf_calc),
                "source": "calculated",
                "method": "OCF_minus_CAPEX"
            }

    if not has_any_historical and historical:
        normalized_fcf["historical"] = historical
    else:
        normalized_fcf["historical"] = historical

    return normalized_fcf


def _ensure_fcf_forecast(
    normalized_fcf: Dict[str, Any],
    extracted_data_root: Dict[str, Any]
) -> Dict[str, Any]:
    if not isinstance(normalized_fcf, dict):
        normalized_fcf = {}

    historical = normalized_fcf.get("historical")
    if not isinstance(historical, dict):
        historical = {}

    forecast = normalized_fcf.get("forecast_next_5_years")
    if not isinstance(forecast, dict):
        forecast = {}

    forecast = dict(forecast)
    forecast.setdefault("base_year", "")
    forecast.setdefault("growth_rate_used", "")
    forecast.setdefault("methodology", "-")

    revenue_points = _collect_revenue_points(extracted_data_root)
    if not revenue_points:
        normalized_fcf["historical"] = historical
        normalized_fcf["forecast_next_5_years"] = forecast
        return normalized_fcf

    base_year_int = _pick_base_year_int_from_revenue(extracted_data_root, revenue_points)
    if base_year_int is None:
        normalized_fcf["historical"] = historical
        normalized_fcf["forecast_next_5_years"] = forecast
        return normalized_fcf

    existing_forecast_values = {
        k: v for k, v in forecast.items()
        if k not in {"base_year", "growth_rate_used", "methodology"}
    }
    existing_forecast_year_keys = list(existing_forecast_values.keys())
    parsed_existing_forecast_years = [
        (k, _parse_year_int(str(k))) for k in existing_forecast_year_keys
    ]
    parsed_existing_forecast_years = [
        (k, y) for (k, y) in parsed_existing_forecast_years if y is not None
    ]
    parsed_existing_forecast_years.sort(key=lambda x: x[1])

    if parsed_existing_forecast_years:
        forecast_year_labels = [k for k, _ in parsed_existing_forecast_years][:5]
        forecast_year_ints = [y for _, y in parsed_existing_forecast_years][:5]
    else:
        forecast_year_ints = [base_year_int + i for i in range(1, 6)]
        forecast_year_labels = [f"{y}E" for y in forecast_year_ints]

    has_any_numeric_forecast = any(_parse_number(v) is not None for v in existing_forecast_values.values())

    if has_any_numeric_forecast:
        forecast.setdefault("base_year", forecast.get("base_year") or str(base_year_int))
        for label in forecast_year_labels:
            forecast.setdefault(label, existing_forecast_values.get(label, "-"))
        normalized_fcf["historical"] = historical
        normalized_fcf["forecast_next_5_years"] = forecast
        return normalized_fcf

    projected_revenue, revenue_growth_rate_used = _project_revenue_next_5_years(
        revenue_points,
        base_year_int,
        forecast_year_ints
    )

    if not projected_revenue:
        forecast["base_year"] = str(base_year_int)
        forecast["growth_rate_used"] = revenue_growth_rate_used or forecast.get("growth_rate_used", "")
        forecast["methodology"] = "-"
        for label in forecast_year_labels:
            forecast[label] = "-"
        normalized_fcf["historical"] = historical
        normalized_fcf["forecast_next_5_years"] = forecast
        return normalized_fcf

    historical_fcf_points = _collect_historical_fcf_points(historical)
    if len(historical_fcf_points) >= 3:
        fcf_cagr = _compute_cagr_from_last_n_points(historical_fcf_points, 3)
        if fcf_cagr is None:
            fcf_cagr = 0.0
        base_fcf_year, base_fcf_value = historical_fcf_points[-1]
        forecast["base_year"] = str(base_fcf_year)
        forecast["growth_rate_used"] = _format_percent(fcf_cagr)
        forecast["methodology"] = "FCF_CAGR"
        for y_int, label in zip(forecast_year_ints, forecast_year_labels):
            years_forward = y_int - base_fcf_year
            if years_forward <= 0:
                forecast[label] = "-"
                continue
            forecast[label] = _format_number(base_fcf_value * ((1.0 + fcf_cagr) ** years_forward))
        normalized_fcf["historical"] = historical
        normalized_fcf["forecast_next_5_years"] = forecast
        return normalized_fcf

    revenue_by_year = {y: v for y, v in revenue_points}
    if len(historical_fcf_points) in (1, 2):
        margins: List[float] = []
        for y, f in historical_fcf_points:
            rev = revenue_by_year.get(y)
            if rev is None or rev == 0:
                continue
            margins.append(f / rev)
        if margins:
            avg_margin = sum(margins) / len(margins)
            forecast["base_year"] = str(base_year_int)
            forecast["growth_rate_used"] = revenue_growth_rate_used or ""
            forecast["methodology"] = "Revenue_margin_based"
            for y_int, label in zip(forecast_year_ints, forecast_year_labels):
                rev = projected_revenue.get(y_int)
                forecast[label] = _format_number(rev * avg_margin) if rev is not None else "-"
            normalized_fcf["historical"] = historical
            normalized_fcf["forecast_next_5_years"] = forecast
            return normalized_fcf

    ebitda_points = _collect_profit_metric_points(extracted_data_root, "ebitda")
    capex_points = _collect_tale_metric_points(extracted_data_root, "capex")
    wc_points = _collect_tale_metric_points(extracted_data_root, "change_in_working_capital")

    if ebitda_points and capex_points:
        ebitda_by_year = {y: v for y, v in ebitda_points}
        capex_by_year = {y: v for y, v in capex_points}
        wc_by_year = {y: v for y, v in wc_points} if wc_points else {}

        candidate_years = sorted(set(ebitda_by_year.keys()) & set(capex_by_year.keys()))
        proxy_year = candidate_years[-1] if candidate_years else None

        if proxy_year is not None:
            ebitda_val = ebitda_by_year.get(proxy_year)
            capex_val = capex_by_year.get(proxy_year)
            wc_val = wc_by_year.get(proxy_year, 0.0)
            if ebitda_val is not None and capex_val is not None:
                proxy_fcf = ebitda_val - abs(capex_val) - (wc_val if wc_val is not None else 0.0)
                base_rev = revenue_by_year.get(proxy_year)
                proxy_margin = (proxy_fcf / base_rev) if base_rev not in (None, 0) else None

                forecast["base_year"] = str(base_year_int)
                forecast["growth_rate_used"] = revenue_growth_rate_used or ""
                forecast["methodology"] = "EBITDA_proxy"
                for y_int, label in zip(forecast_year_ints, forecast_year_labels):
                    rev = projected_revenue.get(y_int)
                    if rev is None:
                        forecast[label] = "-"
                        continue
                    if proxy_margin is not None:
                        forecast[label] = _format_number(rev * proxy_margin)
                    else:
                        base_rev_for_scaling = projected_revenue.get(base_year_int)
                        if base_rev_for_scaling not in (None, 0):
                            forecast[label] = _format_number(proxy_fcf * (rev / base_rev_for_scaling))
                        else:
                            forecast[label] = "-"
                normalized_fcf["historical"] = historical
                normalized_fcf["forecast_next_5_years"] = forecast
                return normalized_fcf

    forecast["base_year"] = str(base_year_int)
    forecast["growth_rate_used"] = revenue_growth_rate_used or ""
    forecast["methodology"] = "industry_proxy"
    for y_int, label in zip(forecast_year_ints, forecast_year_labels):
        rev = projected_revenue.get(y_int)
        forecast[label] = _format_number(rev * 0.05) if rev is not None else "-"

    normalized_fcf["historical"] = historical
    normalized_fcf["forecast_next_5_years"] = forecast
    return normalized_fcf


def _collect_historical_fcf_points(historical: Dict[str, Any]) -> List[tuple]:
    points: List[tuple] = []
    if not isinstance(historical, dict):
        return points
    for year_label, obj in historical.items():
        year_int = _parse_year_int(str(year_label))
        if year_int is None:
            continue
        if isinstance(obj, dict):
            v = _parse_number(obj.get("value"))
        else:
            v = _parse_number(obj)
        if v is None:
            continue
        points.append((year_int, v))
    points.sort(key=lambda x: x[0])
    return points


def _collect_revenue_points(extracted_data_root: Dict[str, Any]) -> List[tuple]:
    revenue = extracted_data_root.get("revenue")
    if not isinstance(revenue, dict):
        return []

    points: Dict[int, float] = {}

    def add_point(period: Any, value: Any):
        year_int = _parse_year_int(str(period)) if period is not None else None
        v = _parse_number(value)
        if year_int is None or v is None:
            return
        points.setdefault(year_int, float(v))

    for item in revenue.get("history") or []:
        if isinstance(item, dict):
            add_point(item.get("period"), item.get("value"))

    present = revenue.get("present")
    if isinstance(present, dict):
        add_point(present.get("period"), present.get("value"))

    for item in revenue.get("future") or []:
        if isinstance(item, dict):
            add_point(item.get("period"), item.get("value"))

    return sorted(points.items(), key=lambda x: x[0])


def _collect_profit_metric_points(extracted_data_root: Dict[str, Any], metric_key: str) -> List[tuple]:
    profit = extracted_data_root.get("profit_metrics")
    if not isinstance(profit, dict):
        return []
    items = profit.get(metric_key)
    if not isinstance(items, list):
        return []

    points: Dict[int, float] = {}
    for item in items:
        if not isinstance(item, dict):
            continue
        y = _parse_year_int(str(item.get("period")))
        v = _parse_number(item.get("value"))
        if y is None or v is None:
            continue
        points.setdefault(y, float(v))
    return sorted(points.items(), key=lambda x: x[0])


def _collect_tale_metric_points(extracted_data_root: Dict[str, Any], metric_key: str) -> List[tuple]:
    tale = extracted_data_root.get("tale_of_the_tape")
    if not isinstance(tale, dict):
        return []
    metric = tale.get(metric_key)
    if not isinstance(metric, dict):
        return []
    year_wise = metric.get("year_wise")
    if not isinstance(year_wise, dict):
        return []

    points: Dict[int, float] = {}
    for year_label, obj in year_wise.items():
        y = _parse_year_int(str(year_label))
        if y is None:
            continue
        if isinstance(obj, dict):
            v = _parse_number(obj.get("value"))
        else:
            v = _parse_number(obj)
        if v is None:
            continue
        points.setdefault(y, float(v))
    return sorted(points.items(), key=lambda x: x[0])


def _pick_base_year_int_from_revenue(
    extracted_data_root: Dict[str, Any],
    revenue_points: List[tuple]
) -> Optional[int]:
    revenue = extracted_data_root.get("revenue")
    if isinstance(revenue, dict):
        years: List[int] = []
        for item in revenue.get("history") or []:
            if not isinstance(item, dict):
                continue
            y = _parse_year_int(str(item.get("period")))
            if y is not None:
                years.append(y)
        if years:
            return max(years)

        present = revenue.get("present")
        if isinstance(present, dict):
            y = _parse_year_int(str(present.get("period")))
            if y is not None:
                return y

    if not revenue_points:
        return None
    return max(y for y, _ in revenue_points)


def _project_revenue_next_5_years(
    revenue_points: List[tuple],
    base_year_int: int,
    forecast_year_ints: List[int]
) -> tuple:
    revenue_by_year = {y: v for y, v in revenue_points}

    projected: Dict[int, float] = {}
    for y in forecast_year_ints:
        if y in revenue_by_year:
            projected[y] = revenue_by_year[y]

    if len(projected) == len(forecast_year_ints):
        return projected, ""

    last_points = [(y, v) for y, v in revenue_points if v is not None]
    last_points.sort(key=lambda x: x[0])
    last_points = last_points[-5:]

    growth_rate_used = ""
    cagr = _compute_cagr_from_last_n_points(last_points, 3) if len(last_points) >= 3 else None
    if cagr is None and len(last_points) >= 2:
        first_y, first_v = last_points[-2]
        last_y, last_v = last_points[-1]
        if first_v not in (None, 0) and last_v is not None and last_y > first_y:
            cagr = (last_v / first_v) ** (1.0 / (last_y - first_y)) - 1.0

    if cagr is not None:
        max_vol = _max_abs_yoy(last_points)
        if max_vol is not None and abs(cagr) > max_vol:
            cagr = max_vol if cagr > 0 else -max_vol
        growth_rate_used = _format_percent(cagr)

    last_known_year = max(y for y, _ in revenue_points)
    last_known_value = revenue_by_year.get(last_known_year)

    if last_known_value is None or cagr is None:
        return projected, growth_rate_used

    for y in forecast_year_ints:
        if y in projected:
            continue
        years_forward = y - last_known_year
        if years_forward <= 0:
            continue
        projected[y] = float(last_known_value) * ((1.0 + cagr) ** years_forward)

    return projected, growth_rate_used


def _compute_cagr_from_last_n_points(points: List[tuple], n: int) -> Optional[float]:
    if len(points) < n:
        return None
    pts = sorted(points, key=lambda x: x[0])[-n:]
    start_y, start_v = pts[0]
    end_y, end_v = pts[-1]
    if start_v in (None, 0) or end_v is None:
        return None
    years = end_y - start_y
    if years <= 0:
        return None
    if start_v <= 0 or end_v <= 0:
        return None
    return (end_v / start_v) ** (1.0 / years) - 1.0


def _max_abs_yoy(points: List[tuple]) -> Optional[float]:
    pts = sorted(points, key=lambda x: x[0])
    yoys: List[float] = []
    for (y1, v1), (y2, v2) in zip(pts, pts[1:]):
        if v1 in (None, 0) or v2 is None:
            continue
        if y2 <= y1:
            continue
        yoys.append((v2 / v1) - 1.0)
    if not yoys:
        return None
    return max(abs(x) for x in yoys)


def _parse_year_int(label: str) -> Optional[int]:
    if not label:
        return None
    m = re.search(r"(19\d{2}|20\d{2})", label)
    if m:
        return int(m.group(1))
    m2 = re.search(r"-(\d{2})\b", label)
    if m2:
        yy = int(m2.group(1))
        return 2000 + yy if yy <= 50 else 1900 + yy
    m3 = re.search(r"\bFY\s?(\d{2})(?!\d)", label, re.IGNORECASE)
    if m3:
        yy = int(m3.group(1))
        return 2000 + yy if yy <= 50 else 1900 + yy
    return None


def _parse_number(value: Any) -> Optional[float]:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    s = str(value).strip()
    if s == "" or s == "-":
        return None
    neg = False
    if s.startswith("(") and s.endswith(")"):
        neg = True
        s = s[1:-1]
    s = s.replace(",", "")
    s = re.sub(r"[^0-9.\-]", "", s)
    if s in ("", "-", "."):
        return None
    try:
        num = float(s)
    except Exception:
        return None
    return -num if neg else num


def _format_number(value: float) -> str:
    if value is None:
        return "-"
    if abs(value) >= 1000:
        return str(round(value, 2))
    return str(round(value, 2))


def _format_percent(value: float) -> str:
    if value is None:
        return ""
    return f"{round(value * 100.0, 2)}%"


def _normalize_tale_of_the_tape(
    tale_of_the_tape: Any,
    extracted_data_root: Dict[str, Any]
) -> Dict[str, Any]:
    if not isinstance(tale_of_the_tape, dict):
        tale_of_the_tape = {}

    normalized = dict(tale_of_the_tape)
    alt_root_metrics = {}
    for metric_key in ("capex", "change_in_working_capital", "one_time_cost"):
        if isinstance(extracted_data_root.get(metric_key), dict):
            alt_root_metrics[metric_key] = extracted_data_root.get(metric_key)

    reserved_metric_keys = {"year_wise", "unit", "source", "formula_used", "method"}

    for metric_key in ("capex", "change_in_working_capital", "one_time_cost"):
        metric_obj = normalized.get(metric_key)
        if not isinstance(metric_obj, dict):
            metric_obj = {}

        year_wise = metric_obj.get("year_wise")
        if not isinstance(year_wise, dict):
            year_wise = {}

        for maybe_year, maybe_val in list(metric_obj.items()):
            if maybe_year in reserved_metric_keys:
                continue
            if isinstance(maybe_val, (dict, str, int, float)) or maybe_val is None:
                year_wise.setdefault(maybe_year, maybe_val)

        if metric_key in alt_root_metrics:
            for year, val in alt_root_metrics[metric_key].items():
                year_wise.setdefault(year, val)

        normalized_year_wise: Dict[str, Dict[str, Any]] = {}
        fallback_source = metric_obj.get("source") or "not_found"
        for year, val in year_wise.items():
            if isinstance(val, dict):
                value = val.get("value")
                source = val.get("source") or fallback_source
            else:
                value = val
                source = fallback_source

            normalized_year_wise[str(year)] = {
                "value": "-" if value is None or value == "" else str(value),
                "source": str(source) if source else "not_found"
            }

        metric_obj["year_wise"] = normalized_year_wise
        metric_obj.setdefault("unit", "$M")
        normalized[metric_key] = metric_obj

    for metric_key in alt_root_metrics.keys():
        extracted_data_root.pop(metric_key, None)

    return normalized


def _parse_json_safely(content: str) -> Dict[str, Any]:
    """
    Parse JSON from LLM response, handling potential markdown wrapping.
    """
    # Remove markdown code blocks if present
    cleaned = re.sub(r'^```json\s*', '', content.strip(), flags=re.MULTILINE)
    cleaned = re.sub(r'\s*```$', '', cleaned, flags=re.MULTILINE)
    cleaned = re.sub(r'^```\s*', '', cleaned, flags=re.MULTILINE)
    
    # Remove <think> tags if present (common in reasoning models)
    cleaned = re.sub(r'<think>.*?</think>', '', cleaned, flags=re.DOTALL)
    
    return json.loads(cleaned)


def _log_extraction_summary(data: Dict[str, Any]):
    """
    Print a summary of what was extracted.
    """
    print(f"\n📊 Extraction Summary:")
    print(f"   Company: {data.get('company_name', 'N/A')}")
    print(f"   Currency: {data.get('currency', 'N/A')}")
    
    revenue = data.get('revenue', {})
    if revenue.get('present'):
        print(f"   Current Revenue: {revenue['present'].get('value')} ({revenue['present'].get('period')})")
    
    profit = data.get('profit_metrics', {})
    ebitda = profit.get('ebitda', []) or profit.get('adjusted_ebitda', [])
    if ebitda:
        print(f"   EBITDA entries: {len(ebitda)}")
    
    market = data.get('market_intelligence', {})
    if market.get('industry_position'):
        print(f"   Industry Position: {market['industry_position']}")
    
    risks = data.get('risk_analysis', {})
    total_risks = sum([
        len(risks.get('operational_risks', [])),
        len(risks.get('financial_risks', [])),
        len(risks.get('market_risks', [])),
        len(risks.get('regulatory_risks', []))
    ])
    print(f"   Total Risks: {total_risks}")
    
    ai = data.get('ai_suggestion', {})
    if ai.get('recommendation'):
        print(f"   AI Recommendation: {ai['recommendation']} ({ai.get('confidence_percent', 0)}% confidence)")


def _save_error_log(deal_id: str, error_message: str, error_type: str):
    """
    Save error details to file for debugging.
    """
    try:
        timestamp = int(time.time())
        filename = f"{deal_id}_ERROR_{timestamp}.json"
        filepath = os.path.join(EXTRACTED_DATA_DIR, filename)
        
        error_data = {
            "error": True,
            "error_type": error_type,
            "message": error_message,
            "timestamp": timestamp,
            "deal_id": deal_id
        }
        
        os.makedirs(EXTRACTED_DATA_DIR, exist_ok=True)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(error_data, f, indent=2)
        
        print(f"🚨 Error log saved: {filename}")
        
    except Exception as e:
        print(f"❌ Could not save error log: {e}")


# ============================================================================
# UTILITY FUNCTIONS (for backward compatibility)
# ============================================================================

def get_extraction_status(deal_id: str) -> Dict[str, Any]:
    """
    Get extraction status for a deal.
    
    Returns:
        dict: Status information
    """
    extracted = load_extracted_data(deal_id)
    
    return {
        "deal_id": deal_id,
        "has_extraction": extracted is not None,
        "extracted_at": None,  # Could parse from filename
        "company_name": extracted.get('company_name') if extracted else None,
        "data_quality": "complete" if extracted and validate_schema(extracted)[0] else "partial"
    }


def _extract_transaction_assumptions_separately(
    client: OpenAI,
    ocr_text: str,
    deal_id: Optional[str] = None
) -> Dict[str, Any]:
    if len(ocr_text) > MAX_OCR_CHARS:
        ocr_text = ocr_text[:MAX_OCR_CHARS]

    try:
        response = client.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {"role": "system", "content": _build_transaction_assumptions_prompt()},
                {"role": "user", "content": f"Extract transaction assumptions from this OCR text:\n\n{ocr_text}"},
            ],
            response_format={"type": "json_object"},
            temperature=TEMPERATURE,
            max_tokens=MAX_TOKENS
        )
    except Exception as e:
        error_msg = f"Transaction Assumptions API call failed: {str(e)}"
        print(f"❌ {error_msg}")
        if deal_id:
            _save_error_log(deal_id, error_msg, "TA_API_FAILURE")
        raise

    raw_content = response.choices[0].message.content
    if not raw_content:
        raise ValueError("TA-only LLM returned empty response")

    ta_only = _parse_json_safely(raw_content)
    if not isinstance(ta_only, dict):
        raise ValueError("TA-only LLM returned non-object JSON")
    return ta_only


def _build_transaction_assumptions_prompt() -> str:
    ta_schema = json.dumps(get_transaction_assumptions_schema(), indent=2)
    return f"""
You are an expert investment banking operations assistant.

Your task is to extract sources & uses data, transaction assumptions, and EBITDA adjustments (Quality of Earnings add-backs) from the OCR text. 

You MUST follow the schema exactly.
DO NOT hallucinate.

Schema:
{ta_schema}

Extraction Rules:
1. 'purchase_price': Search for Enterprise Value, Purchase Price. If not found, return null. 
2. 'seller_rollover': Look for rollover equity, management rollover.
3. 'transaction_fees': Look for total diligence or transaction fees. Provide as a number (in the document's scale, typically millions or thousands).
4. 'entry_multiple': Extract Entry Multiple explicitly stated (e.g., 5.0). 
5. 'exit_multiple': Extract Exit Multiple explicitly stated (e.g., 5.0).
6. 'ebitda_adjustments': Extract an array of objects for specific adjustments to EBITDA (e.g. 'Severance', 'Rent adjustment', 'COVID disruption'). Include the item name and an array of periodic values found.

If a specific metric is completely missing, return null for its field. Do not make up a value.
Return ONLY valid JSON.
"""

def _extract_interest_schedule_separately(
    client: OpenAI,
    ocr_text: str,
    deal_id: Optional[str] = None
) -> Dict[str, Any]:
    if len(ocr_text) > MAX_OCR_CHARS:
        ocr_text = ocr_text[:MAX_OCR_CHARS]

    try:
        from .schema import get_interest_schedule_schema
        is_schema = json.dumps(get_interest_schedule_schema(), indent=2)
        system_prompt = f"""You are an expert financial extraction assistant.
Task: Extract the precise Interest Schedule (Revolver Interest, Term Loan Interest, Seller Note Interest, Interest Subtotal) from the OCR text.
Do not hallucinate. Do not recalculate if not present. Just extract values for historical/current years.

Schema:
{is_schema}

Rules:
1. 'revolver': Extract interest paid specifically labelled for Revolvers.
2. 'term_loan': Extract interest paid specifically labelled for Term Loans.
3. 'seller_note': Extract interest paid specifically labelled for Seller Notes.
4. 'interest_subtotal': Total interest or interest expense.
Map these to the exact years found (e.g. {{"2022": 5.0, "2023": 6.5}}). If any specific breakdown is missing, return empty object {{}}.
Return ONLY valid JSON.
"""
        response = client.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Extract the interest schedule from this OCR text:\n\n{ocr_text}"},
            ],
            response_format={"type": "json_object"},
            temperature=0.0,
            max_tokens=MAX_TOKENS
        )
    except Exception as e:
        error_msg = f"Interest Schedule API call failed: {str(e)}"
        print(f"❌ {error_msg}")
        if deal_id:
            _save_error_log(deal_id, error_msg, "IS_API_FAILURE")
        raise

    raw_content = response.choices[0].message.content
    if not raw_content:
        raise ValueError("IS-only LLM returned empty response")

    is_only = _parse_json_safely(raw_content)
    if not isinstance(is_only, dict):
        raise ValueError("IS-only LLM returned non-object JSON")
    return is_only
