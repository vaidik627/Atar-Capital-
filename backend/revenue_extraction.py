"""
Financial Matrix Extraction Module
Extracts comprehensive financial metrics (Revenue, Gross Profit, OpEx, EBITDA) 
for Actuals, Atar Projections, and Management Projections.
"""
import json
import os
from typing import Dict, Any, Optional
from openai import OpenAI
from .config import (
    LLM_API_KEY, 
    LLM_MODEL, 
    LLM_BASE_URL,
    REVENUE_DATA_DIR,
    MAX_TOKENS,
    TEMPERATURE,
    MAX_OCR_CHARS
)

def extract_financial_matrix(ocr_text: str, deal_id: str) -> Dict[str, Any]:
    """
    Extracts detailed financial matrix data from OCR text.
    
    Args:
        ocr_text (str): The OCR text to analyze.
        deal_id (str): The deal identifier.
        
    Returns:
        Dict[str, Any]: The extracted JSON data.
    """
    print(f"💰 Extracting Detailed Financial Matrix for deal {deal_id}...")
    
    if not ocr_text or len(ocr_text.strip()) < 50:
        print("⚠️ OCR text empty or too short. Returning null structure.")
        return _get_empty_matrix_structure()

    try:
        client = OpenAI(
            api_key=LLM_API_KEY,
            base_url=LLM_BASE_URL
        )
        
        # Use configurable max chars
        prompt = _build_matrix_prompt(ocr_text[:MAX_OCR_CHARS])
        
        response = client.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {"role": "system", "content": "You are a senior financial analyst AI expert in reading financial statements and making reasonable projections."},
                {"role": "user", "content": prompt}
            ],
            temperature=TEMPERATURE,
            max_tokens=MAX_TOKENS,
            response_format={"type": "json_object"}
        )
        
        content = response.choices[0].message.content
        data = json.loads(content)
        
        # Save to disk
        _save_matrix_data(deal_id, data)
        
        return data
        
    except Exception as e:
        print(f"❌ Financial matrix extraction failed: {e}")
        return _get_empty_matrix_structure()

def load_financial_matrix(deal_id: str) -> Dict[str, Any]:
    """Loads extracted matrix data from disk."""
    filepath = os.path.join(REVENUE_DATA_DIR, f"deal_{deal_id}_matrix.json")
    if os.path.exists(filepath):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading matrix data: {e}")
    return _get_empty_matrix_structure()

def _save_matrix_data(deal_id: str, data: Dict[str, Any]):
    """Saves extracted data to disk."""
    if not os.path.exists(REVENUE_DATA_DIR):
        os.makedirs(REVENUE_DATA_DIR, exist_ok=True)
        
    filepath = os.path.join(REVENUE_DATA_DIR, f"deal_{deal_id}_matrix.json")
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        print(f"✓ Financial matrix data saved to: {filepath}")
    except Exception as e:
        print(f"Error saving matrix data: {e}")

def _build_matrix_prompt(ocr_text: str) -> str:
    """Builds the extraction prompt for the financial matrix."""
    return f"""
 INPUT: 
 OCR-extracted text from a company financial document.
 
 OBJECTIVE: 
 Extract and POPULATE a comprehensive Financial Matrix with HIGH PRECISION. 
 You are a forensic financial analyst. Your goal is to find the "Consolidated Statement of Operations", "Income Statement", or "P&L" and extract the exact values.
 
 CRITICAL INSTRUCTION - DATA NORMALIZATION & HISTORICAL SEARCH:
 1. **Scale Detection & Normalization**:
    - **CRITICAL**: The user wants values in **THOUSANDS** or **FULL NUMBERS** (e.g., "$30,000" not "30.0").
    - **Conversion Rule**:
      - If the document says "($ in millions)" and the value is "12.5", you MUST output "12,500,000".
      - If the document says "($ in thousands)" and the value is "23,000", you MUST output "23,000,000".
      - **NEVER OUTPUT SMALL INTEGERS** like "10" or "9" for Revenue/EBITDA. These are typically in Millions or Thousands.
      - **Sanity Check**: If a Revenue value is < 1,000, it is likely in Millions. MULTIPLY BY 1,000,000.
 2. **Fiscal Year Alignment**: Map "FY19", "Fiscal 2019", "Year Ended 2019" directly to "2019A".
 3. **Relative Year Inference**: If columns are unlabeled but adjacent to "2023 Forecast", assume the left columns are "2022A", "2021A", etc.
 4. **Aggressive Historical Search**: If the main table starts at 2023, SCAN THE TEXT for "Historical Financials", "TTM", "LTM", or narrative descriptions of 2019-2022 performance. 
    - **YOU MUST FIND ACTUALS**. Do not return "-" for 2019-2022 unless the document is purely a forward-looking pitch deck with zero history.
 
 METRIC DEFINITIONS & SYNONYMS (Search broadly):
 1. **Net Revenue**: 
    - Search for: "Net Sales", "Total Revenue", "Gross Revenue", "Service Revenue", "Sales".
    - Action: Extract the top-line number.
 2. **Gross Profit**: 
    - Search for: "Gross Margin", "Gross Income".
    - **Formula Priority**: If explicit "Gross Profit" is missing, CALCULATE IT: `Net Revenue - Cost of Goods Sold (COGS/Cost of Sales)`.
 3. **Operating Expenses**: 
    - Search for: "Total Operating Expenses", "Total OpEx".
    - **Summation Priority**: If "Total OpEx" is missing, SUM the components: `SG&A + R&D + Sales & Marketing + General & Admin + Depreciation (if part of opex)`.
 4. **Reported EBITDA**: 
    - Search for: "EBITDA", "Earnings Before Interest Taxes Depreciation and Amortization".
    - **Calculation**: If missing, calculate as `Operating Income + Depreciation + Amortization`.
 5. **Adjusted EBITDA**: 
    - Search for: "Adj. EBITDA", "Adjusted EBITDA", "Pro Forma EBITDA".
    - If strictly not found, assume it equals Reported EBITDA (or apply standard add-backs if listed).
 
 MANDATORY PROJECTION LOGIC (AI INTELLIGENCE):
         - **Scenario A (Projections Exist)**: If the doc contains "Forecast", "Budget", "Management Case", or "Projection" columns for 2023+, USE THEM for both Atar (R) and Management (M) columns unless distinct sets are found.
         - **Scenario B (Actuals Only)**: If the doc only has history (e.g., up to 2022), **YOU MUST PREDICT 2023-2027**.
            - **Growth Rule**: Apply a conservative **5-8% YoY growth** to Revenue.
            - **Margin Rule**: Maintain the **2022A Gross Margin %** and **EBITDA Margin %** for all future years.
            - **Do NOT return "-" for projections if you have Actuals.** Build the forecast for BOTH R (Atar) and M (Management) columns.
         - **Scenario C (Sparse Actuals)**: If some historical years are missing (e.g., 2019 missing but 2021 exists), **FILL GAPS and PROJECT**.
            - If at least ONE actual data point exists, use it as a baseline to backfill history and forecast future years.
            - NEVER return empty projections if ANY actual data is found.
         - **Scenario D (Management vs Atar Differentiation)**:
            - **Differentiation Rule**: "Management Projections" (M) are typically the company's optimistic view. "Atar Projections" (R) are the Sponsor's conservative view.
            - **If ONLY ONE set of projections is found**:
              1. Assign the found values to **Management Projections (M)**.
              2. **MANDATORY HAIRCUT**: You MUST create **Atar Projections (R)** by applying a **5-10% Reduction** to the Management Revenue and EBITDA values.
              3. **Example**: If Management Revenue is 100.0, Atar Revenue MUST be between 90.0 and 95.0.
              4. **CRITICAL ERROR CHECK**: If your output shows identical values for 2024R and 2024M, YOU HAVE FAILED. They MUST BE DIFFERENT.
            - **If TWO sets are found**: Assign the higher/optimistic case to Management (M) and the lower/base case to Atar (R).
            - **NEVER return identical columns for R and M**. DIFFERENTIATE THEM.

 STRICT OUTPUT FORMAT (JSON ONLY):
 {{
   "financials": [
     {{
       "metric": "Net Revenue",
       "sub_metric": "% Growth",
       "values": {{
         "2019A": "val", "2020A": "val", "2021A": "val", "2022A": "val",
         "2023R": "val", "2024R": "val", "2025R": "val", "2026R": "val", "2027R": "val",
         "2023M": "val", "2024M": "val", "2025M": "val", "2026M": "val", "2027M": "val"
       }},
       "sub_values": {{
         "2019A": "pct", "2020A": "pct", "2021A": "pct", "2022A": "pct",
         "2023R": "pct", "2024R": "pct", "2025R": "pct", "2026R": "pct", "2027R": "pct",
         "2023M": "pct", "2024M": "pct", "2025M": "pct", "2026M": "pct", "2027M": "pct"
       }}
     }},
     {{
       "metric": "Gross Profit",
       "sub_metric": "% Margin",
       "values": {{ ... same keys ... }},
       "sub_values": {{ ... same keys ... }}
     }},
     {{
       "metric": "Operating Expenses",
       "sub_metric": "% Growth",
       "values": {{ ... same keys ... }},
       "sub_values": {{ ... same keys ... }}
     }},
     {{
       "metric": "Reported EBITDA",
       "sub_metric": null,
       "values": {{ ... same keys ... }},
       "sub_values": null
     }},
     {{
       "metric": "Adj. EBITDA",
       "sub_metric": "% Margin",
       "values": {{ ... same keys ... }},
       "sub_values": {{ ... same keys ... }}
     }}
   ],
   "cash_flow": [
     {{
       "metric": "Adj. EBITDA",
       "values": {{ ... same keys ... }}
     }},
     {{
       "metric": "Capex",
       "values": {{ ... same keys ... }}
     }},
     {{
       "metric": "Change in WC",
       "values": {{ ... same keys ... }}
     }},
     {{
       "metric": "Free Cash Flow",
       "values": {{ ... same keys ... }}
     }},
     {{
       "metric": "Interest: Revolver",
       "values": {{ ... same keys ... }}
     }},
     {{
       "metric": "Interest: Term Loan",
       "values": {{ ... same keys ... }}
     }},
     {{
       "metric": "Interest: Seller Note",
       "values": {{ ... same keys ... }}
     }},
     {{
       "metric": "Interest Subtotal",
       "values": {{ ... same keys ... }}
     }},
     {{
       "metric": "Amortization: Term Loan",
       "values": {{ ... same keys ... }}
     }},
     {{
       "metric": "Amortization: Seller Note",
       "values": {{ ... same keys ... }}
     }},
     {{
       "metric": "Amortization Subtotal",
       "values": {{ ... same keys ... }}
     }},
     {{
       "metric": "Total Debt Service",
       "values": {{ ... same keys ... }}
     }},
     {{
       "metric": "FCF After Debt Service",
       "values": {{ ... same keys ... }}
     }},
     {{
       "metric": "Management Fees",
       "values": {{ ... same keys ... }}
     }},
     {{
       "metric": "Earnout",
       "values": {{ ... same keys ... }}
     }},
     {{
       "metric": "Cash Available for Revolver",
       "values": {{ ... same keys ... }}
     }},
     {{
       "metric": "Revolver Drawdown (Repayment)",
       "values": {{ ... same keys ... }}
     }},
     {{
       "metric": "Revolver Balance",
       "values": {{ ... same keys ... }}
     }},
     {{
       "metric": "Remaining Cash",
       "values": {{ ... same keys ... }}
     }},
     {{
       "metric": "FCCR",
       "values": {{ ... same keys ... }}
     }}
   ]
 }}

 TALE OF THE TAPE (CASH FLOW ANALYSIS) INSTRUCTIONS:
  You must populate the "cash_flow" array with a High-Precision "Tale of The Tape" analysis.
  
  CRITICAL: DO NOT LAZILY COPY VALUES. CALCULATE THEM.
  
  1. ANTI-DUPLICATION & ACTUALS RECOVERY:
     - **Actuals (2019-2022)**: Look for columns LEFT of the 2023 Projection.
       - If you see unlabeled columns, assume: [2019, 2020, 2021, 2022] -> [2023 Proj].
       - Extract explicit historical data for EBITDA, Capex, etc.
     - **No Lazy Repetition**: Do NOT repeat the same value for 2023, 2024, 2025 unless the document explicitly shows flat performance.
  
  2. MANAGEMENT VS ATAR (SCENARIO LOGIC):
     - **Atar (R)**: The "Conservative" or "Base" case.
     - **Management (M)**: The "Upside" or "Sellers" case.
     - **Differentiation Rule**: If the document only shows one set of projections, assign it to Management (M). Then, for Atar (R), apply a **5-10% Haircut** (reduction) to Revenue/EBITDA/FCF to create a conservative scenario.
     - **Verification**: Atar values MUST generally be LOWER than Management values. If they are identical, you failed.
  
  3. CALCULATION ENGINE (MANDATORY MATH):
     - You MUST perform row-by-row math. Do not just extract "Free Cash Flow" if it conflicts with components.
     - **Missing Inputs**: If "Change in WC", "Interest", or "Amortization" are missing, **USE 0** (Zero) for calculations. Do NOT return "-" if it breaks the math.
     
     **Formulas (Enforce These):**
     *   `Free Cash Flow` = `Adj. EBITDA` - `Capex` - `Change in WC`
         (Example: 1400 - 100 - 0 = 1300. NOT 1400.)
     *   `Total Debt Service` = `Interest Subtotal` + `Amortization Subtotal`
     *   `FCF After Debt Service` = `Free Cash Flow` - `Total Debt Service`
     *   `Cash Avail for Revolver` = `FCF After Debt Service` - `Mgmt Fees` - `Earnout`
     *   `Revolver Balance`:
         - If `Cash Avail` is NEGATIVE -> `Revolver Drawdown` increases (add absolute value).
         - If `Cash Avail` is POSITIVE -> `Revolver Drawdown` decreases (repay debt).
     
  4. FORMATTING & SCALE:
     - **Full Numbers**: Convert "1.4" (millions) to "1,400,000". Convert "1400" (thousands) to "1,400,000".
     - **Consistency**: All values must be in the SAME SCALE (e.g., all raw units or all thousands). Prefer **Raw Units** (e.g. 30,000,000) so the frontend can divide by 1,000 easily.
     - **Negatives**: Return as string with parentheses, e.g. "(500,000)".
  
  5. SELF-CORRECTION CHECKLIST:
     - Did I calculate FCF correctly? (EBITDA - Capex).
     - Did I differentiate Atar vs Management? (Are they identical? If yes, apply haircut).
     - Did I populate Actuals? (Look left of 2023).
     - Are my zeros real zeros or missing data? (Use 0 for missing expenses to allow FCF calc).
  
  DOCUMENT TEXT:
  {ocr_text} 
"""

def _get_empty_matrix_structure() -> Dict[str, Any]:
    """Returns the empty JSON structure."""
    return {
        "financials": [],
        "cash_flow": []
    }
