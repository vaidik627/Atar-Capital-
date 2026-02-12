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
from .schema import get_extraction_schema, validate_schema


# ============================================================================
# MAIN EXTRACTION FUNCTION
# ============================================================================

def extract_financial_data(ocr_text: str, api_key: str = None, deal_id: str = None, source_path: str = None) -> Dict[str, Any]:
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
    
    if not ocr_text or len(ocr_text.strip()) < 100:
        raise ValueError(f"❌ OCR text too short: {len(ocr_text) if ocr_text else 0} chars (min 100)")
    
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
        
        response = client.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {
                    "role": "system", 
                    "content": _build_extraction_prompt()
                },
                {
                    "role": "user", 
                    "content": f"Extract all financial metrics from this document:\n\n{ocr_text}"
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
            if f.startswith(f"{deal_id}_") and f.endswith('.json') and 'ERROR' not in f
        ]
        
        if not files:
            return None
        
        # Sort by timestamp (newest first)
        files.sort(reverse=True)
        latest_file = os.path.join(EXTRACTED_DATA_DIR, files[0])
        
        # Load and return
        with open(latest_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
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
   - Extract company name, currency (USD/EUR/GBP etc.)
   - Write a concise company summary (2-3 sentences)
   - Note where you found this information (source_context)

2. **Revenue:**
   - Extract historical revenue (past years)
   - Current/present revenue (most recent period)
   - Projected/future revenue (forecasts)
   - Include period (e.g., "FY2023", "Q1 2024"), value, and unit (millions/thousands)

3. **Profit Metrics (COMPREHENSIVE):**
   - **Gross Profit:** Extract values, margins, and trends.
   - **Operating Income:** Extract operating profit/loss.
   - **EBITDA:** Extract EBITDA and Adjusted EBITDA. **CRITICAL:** Look for "Adjusted EBITDA" reconciliations or footnotes.
   - **Net Income:** Extract Net Income / Net Profit after tax.
   - **Margins:** Calculate or extract Gross Margin %, Operating Margin %, EBITDA Margin %, Net Margin %.
   - **EPS:** Earnings Per Share (Basic and Diluted).
   - **Cash Flow:** Operating Cash Flow, Free Cash Flow (if available).
   - Store as arrays with `period`, `value` (number), `unit`, `source_context`.
   - Ensure you capture the *exact* fiscal period (e.g., "FY23", "Q1 24", "LTM Sep 23").

4. **Market Intelligence:**
   - Market size and growth rate
   - Company's market share and industry position
   - List key competitors
   - Market trends, customer base, geographic presence

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

**IMPORTANT RULES:**
- Output **ONLY** valid JSON (no markdown, no code blocks)
- If data is not found, use `null` or empty arrays `[]`
- Do NOT fabricate numbers - only extract what's in the document
- Include source_context to show where data was found
- Use confidence levels: "high", "medium", "low"
- All monetary values should be numbers (not strings with $ signs)

Extract the data now."""


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
