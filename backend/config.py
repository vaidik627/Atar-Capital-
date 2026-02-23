"""
Configuration for LLM API
Change only the API key and model to switch between different LLM providers
"""
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# ============================================================================
# LLM CONFIGURATION - CHANGE ONLY THESE VALUES
# ============================================================================

# OpenAI API Configuration
LLM_API_KEY = os.environ.get('LLM_API_KEY', os.environ.get('OPENAI_API_KEY'))
LLM_MODEL = os.environ.get('LLM_MODEL', 'openai/gpt-oss-120b')
LLM_BASE_URL = os.environ.get('LLM_BASE_URL')

# For NVIDIA API:
# LLM_API_KEY = 'nvapi-...'
# LLM_MODEL = 'openai/gpt-oss-120b'
# LLM_BASE_URL = "https://integrate.api.nvidia.com/v1"

# For other providers:
# Anthropic Claude:
# LLM_API_KEY = os.environ.get('ANTHROPIC_API_KEY')
# LLM_MODEL = 'claude-3-opus-20240229'
# LLM_BASE_URL = None

# ============================================================================
# EXTRACTION SETTINGS
# ============================================================================

MAX_OCR_CHARS = 100000  # Maximum characters to send to LLM
MAX_TOKENS = 16000      # Maximum tokens for response
TEMPERATURE = 0         # 0 = deterministic, 1 = creative

# ============================================================================
# FILE PATHS
# ============================================================================

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PARSED_TEXT_DIR = os.path.join(BASE_DIR, 'backend', 'parsed_text')
EXTRACTED_DATA_DIR = os.path.join(BASE_DIR, 'backend', 'extracted_data')
REVENUE_DATA_DIR = os.path.join(BASE_DIR, 'backend', 'revenue_data_json')
REPORTS_DIR = os.path.join(BASE_DIR, 'backend', 'reports')

# ============================================================================
# EXCEL TEMPLATE
# ============================================================================

EXCEL_TEMPLATE_PATH = os.environ.get('EXCEL_TEMPLATE_PATH')


def get_excel_template_path() -> str:
    if EXCEL_TEMPLATE_PATH and os.path.exists(EXCEL_TEMPLATE_PATH):
        return EXCEL_TEMPLATE_PATH

    base_parent = os.path.dirname(BASE_DIR)
    candidates = []
    try:
        for name in os.listdir(base_parent):
            if name.lower().endswith(('.xlsm', '.xlsx')):
                candidates.append(os.path.join(base_parent, name))
    except Exception:
        candidates = []

    if candidates:
        candidates.sort(key=lambda p: os.path.getmtime(p), reverse=True)
        return candidates[0]

    raise FileNotFoundError(
        "Excel template not found. Set EXCEL_TEMPLATE_PATH env var or place a .xlsm/.xlsx next to the project root."
    )

# Create directories immediately on import
os.makedirs(PARSED_TEXT_DIR, exist_ok=True)
os.makedirs(EXTRACTED_DATA_DIR, exist_ok=True)
os.makedirs(REVENUE_DATA_DIR, exist_ok=True)
os.makedirs(REPORTS_DIR, exist_ok=True)

print(f"📁 Config loaded:")
print(f"   Parsed text dir: {PARSED_TEXT_DIR}")
print(f"   Extracted data dir: {EXTRACTED_DATA_DIR}")
print(f"   Revenue Data dir: {REVENUE_DATA_DIR}")
print(f"   Reports dir: {REPORTS_DIR}")
print(f"   LLM Model: {LLM_MODEL}")
print(f"   API Key: {'✓ SET' if LLM_API_KEY else '✗ NOT SET'}")
if LLM_API_KEY:
    print(f"   API Key (masked): {LLM_API_KEY[:5]}...{LLM_API_KEY[-4:]}")
print(f"   Base URL: {LLM_BASE_URL}")

# ============================================================================
# VALIDATION HELPERS
# ============================================================================

def is_configured():
    """Check if system is properly configured"""
    return LLM_API_KEY is not None and len(LLM_API_KEY) > 0

def get_config_status():
    """Get detailed configuration status"""
    return {
        "api_key_set": LLM_API_KEY is not None,
        "model": LLM_MODEL,
        "parsed_text_dir_exists": os.path.exists(PARSED_TEXT_DIR),
        "extracted_data_dir_exists": os.path.exists(EXTRACTED_DATA_DIR),
        "is_ready": is_configured()
    }

