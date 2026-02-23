import requests
import io

def test_upload():
    url = "http://localhost:8000/api/documents/upload"
    
    # Create a dummy PDF content
    pdf_content = (
        b"%PDF-1.4\n"
        b"1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n"
        b"2 0 obj\n<<\n/Type /Pages\n/Kids [3 0 R]\n/Count 1\n>>\nendobj\n"
        b"3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/MediaBox [0 0 612 792]\n/Resources << >>\n/Contents 4 0 R\n>>\nendobj\n"
        b"4 0 obj\n<<\n/Length 44\n>>\nstream\nBT\n/F1 24 Tf\n100 700 Td\n(Hello World) Tj\nET\nendstream\nendobj\n"
        b"xref\n0 5\n0000000000 65535 f\n0000000010 00000 n\n0000000060 00000 n\n0000000157 00000 n\n0000000282 00000 n\n"
        b"trailer\n<<\n/Size 5\n/Root 1 0 R\n>>\nstartxref\n376\n%%EOF"
    )
    
    files = {
        'file': ('test.pdf', pdf_content, 'application/pdf')
    }
    
    data = {
        'dealName': 'Test Deal',
        'dealValue': '$10M'
    }

    try:
        response = requests.post(url, files=files, data=data)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"Request failed: {e}")

if __name__ == "__main__":
    test_upload()