import os
import io
import time
from dotenv import load_dotenv
from google.cloud import documentai
from google.api_core.client_options import ClientOptions
import pypdf

# Load environment variables
load_dotenv()

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
            
        return full_text

    except Exception as e:
        print(f"Error in OCR processing: {e}")
        print("Attempting fallback extraction...")
        return extract_text_fallback(file_content, mime_type)

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
