from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import time
import traceback
from .ocr_service import extract_text_from_file
from .extraction import extract_financial_data, load_extracted_data

app = Flask(__name__, static_folder='../')
CORS(app)

# Mock Database
DEALS = {}
DOCUMENTS = {}

# Ensure directories exist
EXTRACTED_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'extracted_data')
os.makedirs(EXTRACTED_DATA_DIR, exist_ok=True)

# Serve Static Files
@app.route('/')
def index():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory(app.static_folder, path)

# --- API Endpoints ---

@app.route('/api/deals', methods=['GET', 'POST'])
def handle_deals():
    if request.method == 'POST':
        data = request.json
        deal_id = str(len(DEALS) + 1)
        DEALS[deal_id] = {
            "id": deal_id,
            "name": data.get('name', 'New Deal'),
            "status": "Active",
            "date": "2024-10-25"
        }
        return jsonify({"success": True, "deal": DEALS[deal_id]})
    return jsonify({"success": True, "deals": list(DEALS.values())})

@app.route('/api/documents', methods=['GET'])
def list_documents():
    deal_id = request.args.get('dealId')
    docs = [doc for doc in DOCUMENTS.values() if doc['deal_id'] == deal_id] if deal_id else list(DOCUMENTS.values())
    return jsonify({
        "success": True,
        "data": docs
    })

@app.route('/api/analysis/<deal_id>', methods=['GET'])
def get_analysis(deal_id):
    extracted_data = None
    
    # 1. Try to find in memory first
    deal_docs = [doc for doc in DOCUMENTS.values() if doc['deal_id'] == deal_id]
    if deal_docs:
        extracted_data = deal_docs[-1]['extracted_data']
    
    # 2. If not in memory, try to load from disk
    if not extracted_data:
        extracted_data = load_extracted_data(deal_id)
        
    if not extracted_data:
        return jsonify({
            "success": False,
            "message": "Analysis not found",
            "data": {}
        })
    
    # Format for frontend
    # Map the backend schema to the frontend expected structure
    # Frontend expects: header, revenue, profitMetrics, marketIntelligence, riskAnalysis, aiSuggestion
    
    analysis_data = {
        "header": {
            "companyName": extracted_data.get('company_name'),
            "currency": extracted_data.get('currency', 'USD'),
            "dealValue": {
                "description": "Deal Value",
                "display": extracted_data.get('market_intelligence', {}).get('market_size') or "N/A",
                "visible": True
            }
        },
        "summary": {
            "text": extracted_data.get('company_summary', {}).get('text', ''),
            "visible": True
        },
        "revenue": {
            "present": {
                "value": extracted_data.get('revenue', {}).get('present', {}).get('value', 'N/A'),
                "period": extracted_data.get('revenue', {}).get('present', {}).get('period', 'N/A')
            },
            "history": extracted_data.get('revenue', {}).get('history', []),
            "future": extracted_data.get('revenue', {}).get('future', []),
            "visible": True
        },
        "profitMetrics": {
            "grossProfit": extracted_data.get('profit_metrics', {}).get('gross_profit', []),
            "ebitda": extracted_data.get('profit_metrics', {}).get('ebitda', []),
            "netIncome": extracted_data.get('profit_metrics', {}).get('net_income', []),
            "visible": True
        },
        "marketIntelligence": {
            "industryPosition": extracted_data.get('market_intelligence', {}).get('industry_position'),
            "marketSharePercent": extracted_data.get('market_intelligence', {}).get('market_share_percent'),
            "competitors": extracted_data.get('market_intelligence', {}).get('key_competitors', []),
            "visible": True
        },
        "riskAnalysis": {
            "operational": extracted_data.get('risk_analysis', {}).get('operational_risks', []),
            "financial": extracted_data.get('risk_analysis', {}).get('financial_risks', []),
            "market": extracted_data.get('risk_analysis', {}).get('market_risks', []),
            "regulatory": extracted_data.get('risk_analysis', {}).get('regulatory_risks', []),
            "visible": True
        },
        "aiSuggestion": {
            "recommendation": extracted_data.get('ai_suggestion', {}).get('recommendation'),
            "confidence": extracted_data.get('ai_suggestion', {}).get('confidence_percent'),
            "rationale": extracted_data.get('ai_suggestion', {}).get('rationale'),
            "visible": True
        }
    }

    return jsonify({
        "success": True,
        "data": analysis_data
    })

@app.route('/api/extract', methods=['POST'])
@app.route('/api/documents/upload', methods=['POST'])
def process_document():
    deal_id = request.form.get('dealId') # Frontend sends dealId in FormData
    
    if 'file' not in request.files:
        # Check for 'document' or 'documents' field as well for compatibility
        if 'document' in request.files:
            file = request.files['document']
        elif 'documents' in request.files:
            file = request.files['documents']
        else:
            return jsonify({"success": False, "message": "No file part"}), 400
    else:
        file = request.files['file']
    
    if file.filename == '':
        return jsonify({"success": False, "message": "No selected file"}), 400
    
    try:
        # 1. OCR Extraction
        file_content = file.read()
        mime_type = file.mimetype or 'application/pdf'
        print(f"Processing file: {file.filename} ({mime_type}) for Deal: {deal_id}")
        
        ocr_text = extract_text_from_file(file_content, mime_type)
        print("OCR complete. Text length:", len(ocr_text))

        # Save OCR text to backend/parsed_text
        parsed_text_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'parsed_text')
        os.makedirs(parsed_text_dir, exist_ok=True)
        
        ocr_filename = f"{int(time.time())}_{file.filename}.txt"
        ocr_filepath = os.path.join(parsed_text_dir, ocr_filename)
        
        with open(ocr_filepath, 'w', encoding='utf-8') as f:
            f.write(ocr_text)
        print(f"OCR text saved to: {ocr_filepath}")
        
        # 2. Financial Data Extraction
        # Use deal_id from request if available, otherwise construct one
        extraction_deal_id = deal_id if deal_id else f"upload_{file.filename}"
        extracted_data = extract_financial_data(ocr_text, deal_id=extraction_deal_id)
        
        # Store result (Mock)
        doc_id = f"doc_{int(time.time())}_{file.filename}"
        DOCUMENTS[doc_id] = {
            "id": doc_id,
            "deal_id": extraction_deal_id,
            "name": file.filename,
            "extracted_data": extracted_data,
            "ocr_text_preview": ocr_text[:500]
        }
        
        return jsonify({
            "success": True,
            "dealId": extraction_deal_id,
            "data": extracted_data,
            "ocr_text_preview": ocr_text[:500]
        })
        
    except Exception as e:
        print(f"Error processing document: {e}")
        traceback.print_exc()
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy", "service": "Financial Extraction Engine"})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    app.run(host='0.0.0.0', port=port, debug=True)
