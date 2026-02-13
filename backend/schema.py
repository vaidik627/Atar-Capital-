"""
Financial Data Extraction Schema
Defines the structure for extracted financial data - NO DEMO DATA
"""

def get_extraction_schema():
    """
    Returns the expected schema structure for financial data extraction.
    This is used for validation and documentation purposes only.
    NO sample data - all values are None or empty.
    """
    return {
        "company_name": None,
        "currency": None,
        "company_summary": {
            "text": None,
            "source_context": None,
            "confidence": None
        },
        "revenue": {
            "history": [],
            "present": {},
            "future": []
        },
        "profit_metrics": {
            "gross_profit": [],
            "operating_income": [],
            "ebitda": [],
            "adjusted_ebitda": [],
            "net_income": [],
            "earnings_per_share": [],
            "operating_cash_flow": [],
            "free_cash_flow": [],
            "gross_margin_percent": [],
            "operating_margin_percent": [],
            "ebitda_margin_percent": [],
            "net_margin_percent": []
        },
        "financial_matrix": [],
        "market_intelligence": {
            "market_size": None,
            "market_growth_percent": None,
            "market_share_percent": None,
            "industry_position": None,
            "key_competitors": [],
            "market_trends": None,
            "customer_base": None,
            "geographic_presence": None,
            "source_context": None,
            "confidence": None
        },
        "risk_analysis": {
            "operational_risks": [],
            "financial_risks": [],
            "market_risks": [],
            "regulatory_risks": [],
            "source_context": None,
            "confidence": None
        },
        "ai_suggestion": {
            "recommendation": None,
            "confidence_percent": None,
            "rationale": None
        }
    }


def validate_schema(data):
    """
    Validates that extracted data matches the expected schema structure.
    
    Args:
        data (dict): Extracted financial data to validate
        
    Returns:
        tuple: (is_valid, errors)
    """
    errors = []
    schema = get_extraction_schema()
    
    # Check top-level required fields
    required_fields = ['company_name', 'currency', 'company_summary', 'revenue', 
                      'profit_metrics', 'market_intelligence', 'risk_analysis', 'ai_suggestion', 'financial_matrix']
    
    for field in required_fields:
        if field not in data:
            errors.append(f"Missing required field: {field}")
    
    # Validate nested structures
    if 'revenue' in data:
        if not isinstance(data['revenue'], dict):
            errors.append("Revenue must be a dictionary")
        else:
            for key in ['history', 'present', 'future']:
                if key not in data['revenue']:
                    errors.append(f"Revenue missing '{key}' field")
    
    if 'profit_metrics' in data:
        if not isinstance(data['profit_metrics'], dict):
            errors.append("Profit metrics must be a dictionary")

    if 'financial_matrix' in data:
        if not isinstance(data['financial_matrix'], list):
            errors.append("Financial matrix must be a list")
    
    if 'market_intelligence' in data:
        if not isinstance(data['market_intelligence'], dict):
            errors.append("Market intelligence must be a dictionary")
    
    if 'risk_analysis' in data:
        if not isinstance(data['risk_analysis'], dict):
            errors.append("Risk analysis must be a dictionary")
        else:
            for key in ['operational_risks', 'financial_risks', 'market_risks', 'regulatory_risks']:
                if key not in data['risk_analysis']:
                    errors.append(f"Risk analysis missing '{key}' field")
    
    is_valid = len(errors) == 0
    return is_valid, errors


def get_schema_documentation():
    """
    Returns human-readable documentation of the schema structure.
    """
    return """
    Financial Data Extraction Schema
    =================================
    
    company_name: string
        The name of the company being analyzed
        
    currency: string
        Currency code (e.g., USD, EUR, GBP)
        
    company_summary: object
        text: string - Company description
        source_context: string - Where this info was found
        confidence: string - high/medium/low
        
    revenue: object
        history: array - Past revenue data points
        present: object - Current revenue
        future: array - Projected revenue
        
    profit_metrics: object
        gross_profit: array
        operating_income: array
        ebit: array
        ebitda: array
        adjusted_ebitda: array
        net_income: array
        net_profit: array
        profit_after_tax: array
        ebitda_margin_percent: array
        
    market_intelligence: object
        market_size: object
        market_growth_percent: number
        market_share_percent: number
        industry_position: string
        key_competitors: array
        market_trends: string
        customer_base: string
        geographic_presence: string
        source_context: string
        confidence: string
        
    risk_analysis: object
        operational_risks: array
        financial_risks: array
        market_risks: array
        regulatory_risks: array
        source_context: string
        confidence: string
        
    ai_suggestion: object
        recommendation: string (Buy/Sell/Hold)
        confidence_percent: number (0-100)
        rationale: string
    """


# Backward compatibility - but returns empty schema
def get_empty_schema():
    """
    DEPRECATED: Use get_extraction_schema() instead.
    Returns empty schema structure.
    """
    return get_extraction_schema()


# Remove sample data function completely - no demo data allowed
# If you need sample data for testing, use actual extracted data from files
