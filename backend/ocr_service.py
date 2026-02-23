import os
import io
import time
from dotenv import load_dotenv
from google.cloud import documentai
from google.api_core.client_options import ClientOptions
import pypdf

# Load environment variables
load_dotenv()

from openai import OpenAI
from backend.config import LLM_API_KEY, LLM_MODEL, LLM_BASE_URL, MAX_OCR_CHARS, MAX_TOKENS, TEMPERATURE

# Configuration
PROJECT_ID = os.environ.get('GOOGLE_PROJECT_ID')
LOCATION = os.environ.get('GOOGLE_LOCATION', 'us')
PROCESSOR_ID = os.environ.get('GOOGLE_PROCESSOR_ID')
CREDENTIALS_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'credentials.json')

# Set credentials explicitly
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = CREDENTIALS_PATH

def process_document_chunk(client, processor_name, file_content, mime_type):
    """Process a single chunk of document with Document AI"""
    # Load Binary Data into Document AI RawDocument Object
    raw_document = documentai.RawDocument(content=file_content, mime_type=mime_type)

    # Configure the process request
    request = documentai.ProcessRequest(name=processor_name, raw_document=raw_document)

    # Use the Document AI client to process the sample form
    result = client.process_document(request=request)

    return result.document.text

def extract_text_from_file(file_content, mime_type='application/pdf'):
    """
    Extract text from a file (PDF or Image).
    Tries Google Document AI first, falls back to PyPDF if credentials missing.
    Then applies the Deterministic Financial parsing logic.
    """
    # Check for credentials
    if not os.path.exists(CREDENTIALS_PATH):
        print("⚠️ Google Cloud Credentials not found. Falling back to simple PDF extraction.")
        return extract_text_fallback(file_content, mime_type)

    try:
        # Initialize Document AI client
        client_options = ClientOptions(api_endpoint=f"{LOCATION}-documentai.googleapis.com")
        client = documentai.DocumentProcessorServiceClient(client_options=client_options)
        processor_name = client.processor_path(PROJECT_ID, LOCATION, PROCESSOR_ID)
        
        full_text = ""
        
        # Check if PDF and split if necessary
        if mime_type == 'application/pdf':
            pdf_reader = pypdf.PdfReader(io.BytesIO(file_content))
            total_pages = len(pdf_reader.pages)
            chunk_size = 15
            
            for i in range(0, total_pages, chunk_size):
                chunk_writer = pypdf.PdfWriter()
                end_page = min(i + chunk_size, total_pages)
                
                for page_num in range(i, end_page):
                    chunk_writer.add_page(pdf_reader.pages[page_num])
                
                chunk_stream = io.BytesIO()
                chunk_writer.write(chunk_stream)
                chunk_content = chunk_stream.getvalue()
                
                # Process chunk
                chunk_text = process_document_chunk(client, processor_name, chunk_content, mime_type)
                full_text += chunk_text + "\n"
        else:
            # Process non-PDF or single chunk if not PDF
            full_text = process_document_chunk(client, processor_name, file_content, mime_type)
            
        raw_text = full_text

    except Exception as e:
        print(f"Error in OCR processing: {e}")
        print("Attempting fallback extraction...")
        raw_text = extract_text_fallback(file_content, mime_type)

    # -------------------------------------------------------------
    # Apply Deterministic parsing and append to text
    # -------------------------------------------------------------
    structured_data = run_deterministic_parser(raw_text)
    if structured_data:
        return raw_text + "\n\n--- DETERMINISTIC FINANCIAL EXTRACTION ---\n\n" + structured_data
    return raw_text

def extract_text_fallback(file_content, mime_type):
    """Fallback text extraction using pypdf"""
    try:
        if mime_type == 'application/pdf':
            pdf_reader = pypdf.PdfReader(io.BytesIO(file_content))
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
            
            if not text.strip():
                return "Error: Could not extract text from PDF. It might be a scanned image without OCR."
            return text
        else:
            return "Error: Unsupported file type for fallback extraction."
    except Exception as e:
        return f"Error in fallback extraction: {str(e)}"

def run_deterministic_parser(ocr_text: str) -> str:
    """Passes OCR text through a strict deterministic LLM prompt."""
    if not LLM_API_KEY:
        print("⚠️ No LLM API key for deterministic parser.")
        return ""
        
    print("🤖 Running Deterministic Financial Parser...")
    
    try:
        client_config = {"api_key": LLM_API_KEY}
        if LLM_BASE_URL:
            client_config["base_url"] = LLM_BASE_URL
        client = OpenAI(**client_config)

        # truncate softly to avoid overflow on big docs if needed
        clean_text = ocr_text[:MAX_OCR_CHARS] if len(ocr_text) > MAX_OCR_CHARS else ocr_text

        system_prompt = """You are a STRICT financial data extraction engine and document section classifier.

You are NOT allowed to:
- calculate
- estimate
- infer
- scale
- convert units
- derive values
- reinterpret numbers
- combine values from different sections
- summarize text
- modify text

------------------------------------------
TASK 1 — SECTION CLASSIFICATION & RAW EXTRACTION

From the OCR text, detect and isolate the following sections if present:
1) Income Statement / Profit and Loss / Statement of Operations
2) Balance Sheet / Statement of Financial Position
3) Cash Flow Statement

For each detected section:
- Return the exact raw text block belonging to that section.
- Preserve formatting as-is.
- Do not clean or alter numbers.
- Do not shorten content.

If a section is not present, return null for that section.

------------------------------------------
TASK 2 — FINANCIAL DATA EXTRACTION

You are ONLY allowed to extract numbers that are:
1) Explicitly written in the OCR text
2) Clearly associated with the requested financial label
3) Located inside a financial statement table

STEP 1 — SECTION FILTERING (MANDATORY)
Only extract data if it appears inside sections clearly labeled as one of:
- Consolidated Income Statement
- Statement of Operations
- Profit and Loss Statement
- Balance Sheet
- Statement of Financial Position
- Cash Flow Statement

Ignore: Management commentary, Highlights sections, Bullet summaries, Ratios, KPI summaries, Narrative explanations, Graph descriptions.

STEP 2 — UNIT DETECTION (DO NOT CONVERT)
Detect if the statement contains a unit declaration such as:
- "in millions"
- "in thousands"
- "in billions"
- "$m"
- "$bn"
- "₹ crore"

Return it as: "unit_detected": "millions" | "thousands" | "billions" | "crore" | null
DO NOT modify, scale, or convert numbers.

STEP 3 — STRICT LABEL MATCHING
Only extract values if the exact or near-exact label appears in the table row.
Allowed label mappings:
Revenue: revenue, total revenue, net sales
EBITDA: ebitda
Adjusted EBITDA: adjusted ebitda, adj ebitda
Capital Expenditure: capital expenditure, capex, purchase of ppe
Depreciation: depreciation
Amortization: amortization
Inventory: inventory
Trade Receivables: trade receivables, accounts receivable
Trade Payables: trade payables, accounts payable
Current Assets: total current assets
Current Liabilities: total current liabilities
One Time Cost: exceptional items, restructuring cost, one-time items, non-recurring items

If label is not explicitly present in table row → return null.

STEP 4 — NUMBER EXTRACTION RULES
- Extract numbers exactly as written.
- Remove commas.
- Convert "(1,234)" to -1234.
- Ignore percentages, calculated margins, ratios, per-share values, subtotal rows unless explicitly labeled.
If a value looks scaled version of another value in same table → DO NOT extract unless explicitly labeled.

STEP 5 — MULTI-YEAR HANDLING
If multiple year columns exist: Detect year labels, Map values under correct year.
If year labels not visible: Use "year_1", "year_2", etc from left to right.

------------------------------------------
OUTPUT FORMAT (STRICT JSON ONLY)

{
  "income_statement_section": "exact raw text or null",
  "balance_sheet_section": "exact raw text or null",
  "cash_flow_section": "exact raw text or null",
  "unit_detected": "...",
  "source_section": "...",
  "revenue": { "2022": value_or_null, "2023": value_or_null },
  "ebitda": { "2022": value_or_null, "2023": value_or_null },
  "adjusted_ebitda": { "2022": value_or_null, "2023": value_or_null },
  "depreciation": { "2022": value_or_null, "2023": value_or_null },
  "amortization": { "2022": value_or_null, "2023": value_or_null },
  "capital_expenditure": { "2022": value_or_null, "2023": value_or_null },
  "inventory": { "2022": value_or_null, "2023": value_or_null },
  "trade_receivables": { "2022": value_or_null, "2023": value_or_null },
  "trade_payables": { "2022": value_or_null, "2023": value_or_null },
  "current_assets": { "2022": value_or_null, "2023": value_or_null },
  "current_liabilities": { "2022": value_or_null, "2023": value_or_null },
  "one_time_cost": { "2022": value_or_null, "2023": value_or_null }
}

If absolutely no financial data and no sections are found:
{
  "error": "no_financial_data_found"
}"""
        
        response = client.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"OCR TEXT STARTS BELOW:\n{clean_text}"}
            ],
            response_format={"type": "json_object"},
            temperature=0,  # Ensure strict adherence
            max_tokens=MAX_TOKENS
        )
        
        raw_content = response.choices[0].message.content
        print("✓ Deterministic parse complete.")
        return raw_content
        
    except Exception as e:
        print(f"❌ Deterministic parser failed: {e}")
        return ""
