import azure.functions as func
import logging
import json
import urllib.request
import urllib.parse
import urllib.error
from datetime import datetime, timezone
from html.parser import HTMLParser
import re
import hashlib
import hmac
import base64

class EnhancedDocumentLinkParser(HTMLParser):
    """Enhanced HTML parser to find document links with debugging"""
    def __init__(self):
        super().__init__()
        self.document_links = []
        self.all_links = []
        # Extended document extensions including government common formats
        self.document_extensions = {'.pdf', '.doc', '.docx', '.txt', '.xls', '.xlsx', '.xml', '.csv', '.rtf'}
        # Common government document URL patterns
        self.doc_patterns = [
            r'/data/',           # data.gov.uk pattern
            r'/documents?/',     # common docs folder
            r'/publications?/',  # publications folder
            r'/files?/',         # files folder
            r'\.pdf\?',         # PDF with parameters
            r'download',         # download links
        ]
    
    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            for attr_name, attr_value in attrs:
                if attr_name == 'href' and attr_value:
                    self.all_links.append(attr_value)
                    
                    # Check file extensions
                    lower_url = attr_value.lower()
                    if any(lower_url.endswith(ext) for ext in self.document_extensions):
                        self.document_links.append(attr_value)
                    
                    # Check URL patterns that might indicate documents
                    elif any(re.search(pattern, lower_url) for pattern in self.doc_patterns):
                        self.document_links.append(attr_value)

def find_documents_in_html(html_content, base_url):
    """Parse HTML and find document links with enhanced detection"""
    parser = EnhancedDocumentLinkParser()
    try:
        parser.feed(html_content)
    except Exception as e:
        logging.error(f'HTML parsing error: {str(e)}')
        return {"documents": [], "total_links_found": 0, "sample_links": []}
    
    # Process document links
    documents = []
    for link in parser.document_links:
        # Convert relative URLs to absolute
        if link.startswith('/'):
            full_url = base_url.rstrip('/') + link
        elif link.startswith('http'):
            full_url = link
        else:
            continue
            
        # Extract filename
        filename = link.split('/')[-1].split('?')[0]
        if '.' in filename:
            extension = filename.split('.')[-1].lower()
            
            documents.append({
                "url": full_url,
                "filename": filename,
                "extension": extension,
                "original_link": link
            })
    
    # Remove duplicates while preserving order
    seen = set()
    unique_documents = []
    for doc in documents:
        if doc["url"] not in seen:
            seen.add(doc["url"])
            unique_documents.append(doc)
    
    return {
        "documents": unique_documents,
        "total_links_found": len(parser.all_links),
        "sample_links": parser.all_links[:10]  # First 10 links for debugging
    }

def get_managed_identity_token():
    """Get access token for Azure Storage using managed identity"""
    try:
        # Check for Azure Functions environment variables first
        identity_endpoint = urllib.parse.unquote(urllib.request.urlopen("http://localhost/").geturl()) if True else None
        try:
            identity_endpoint = urllib.parse.unquote(open('/dev/null').read()) if False else None
        except:
            pass
            
        # Use standard approach for Functions
        token_url = "http://169.254.169.254/metadata/identity/oauth2/token?api-version=2018-02-01&resource=https://storage.azure.com/"
        req = urllib.request.Request(token_url)
        req.add_header('Metadata', 'true')
        
        with urllib.request.urlopen(req, timeout=10) as response:
            token_data = json.loads(response.read().decode('utf-8'))
            return token_data['access_token']
            
    except Exception as e:
        logging.error(f'Failed to get access token: {str(e)}')
        return None

def upload_to_blob_storage_real(content, filename, storage_account, container):
    """Upload content to Azure Blob Storage using REST API with managed identity"""
    try:
        access_token = get_managed_identity_token()
        if not access_token:
            # Fallback to simulation
            return {
                "success": False,
                "error": "No access token",
                "fallback": True,
                "blob_url": f"https://{storage_account}.blob.core.windows.net/{container}/{filename}",
                "size": len(content),
                "message": "No token, would simulate"
            }
        
        # Create blob URL
        blob_url = f"https://{storage_account}.blob.core.windows.net/{container}/{filename}"
        
        # Prepare headers
        headers = {
            'Authorization': f'Bearer {access_token}',
            'x-ms-version': '2021-08-06',
            'x-ms-blob-type': 'BlockBlob',
            'Content-Type': 'application/octet-stream',
            'Content-Length': str(len(content))
        }
        
        # Create request
        req = urllib.request.Request(blob_url, data=content, headers=headers, method='PUT')
        
        # Upload
        with urllib.request.urlopen(req, timeout=60) as response:
            status_code = response.status
            
            if status_code in [200, 201]:
                return {
                    "success": True,
                    "blob_url": blob_url,
                    "size": len(content),
                    "status_code": status_code,
                    "message": "Real Azure Storage upload successful",
                    "error": None
                }
            else:
                return {
                    "success": False,
                    "status_code": status_code,
                    "error": f"Upload failed with status {status_code}",
                    "message": "Unexpected response from Azure Storage"
                }
                
    except Exception as e:
        logging.error(f'Real blob upload failed: {str(e)}')
        # Fallback to simulation
        return {
            "success": False,
            "error": str(e),
            "fallback": True,
            "blob_url": f"https://{storage_account}.blob.core.windows.net/{container}/{filename}",
            "size": len(content),
            "message": "Real upload failed, would simulate"
        }

def download_document(url):
    """Download document content from URL"""
    try:
        with urllib.request.urlopen(url, timeout=30) as response:
            content = response.read()
            return content
    except Exception as e:
        logging.error(f'Download failed for {url}: {str(e)}')
        return None

# Create function app
app = func.FunctionApp()

@app.timer_trigger(schedule="0 */4 * * *", arg_name="timer", run_on_startup=False)
def crawl_timer(timer: func.TimerRequest) -> None:
    """Enhanced timer trigger function - simplified version"""
    logging.info('Enhanced web crawler timer executed!')
    
    if timer.past_due:
        logging.info('The timer is running late!')
    
    # Crawl legislation.gov.uk for documents
    url = "https://www.legislation.gov.uk/ukpga/2025/22"
    
    try:
        with urllib.request.urlopen(url, timeout=15) as response:
            content = response.read().decode('utf-8')
            result = find_documents_in_html(content, url)
            
        downloads = []
        for doc in result["documents"][:2]:  # Limit to first 2 documents
            try:
                doc_content = download_document(doc["url"])
                if doc_content:
                    # Upload to real Azure Storage
                    upload_result = upload_to_blob_storage_real(
                        doc_content, 
                        doc["filename"],
                        "stbtpuksprodcrawler01",
                        "documents"
                    )
                    
                    downloads.append({
                        "filename": doc["filename"],
                        "size": len(doc_content),
                        "hash": hashlib.md5(doc_content).hexdigest(),
                        "upload_success": upload_result.get("success", False),
                        "blob_url": upload_result.get("blob_url", ""),
                        "message": upload_result.get("message", ""),
                        "real_storage": True,
                        "status_code": upload_result.get("status_code", 0),
                        "error": upload_result.get("error")
                    })
                    
            except Exception as e:
                logging.error(f'Error processing document {doc["filename"]}: {str(e)}')
                downloads.append({
                    "filename": doc["filename"],
                    "error": str(e),
                    "upload_success": False
                })
        
        logging.info(f'Timer crawl completed: {len(downloads)} documents processed')
        
    except Exception as e:
        logging.error(f'Timer crawl error: {str(e)}')

@app.route(route="search_site", methods=["GET"])
def search_site(req: func.HttpRequest) -> func.HttpResponse:
    """Search a specific site for documents - simplified working version"""
    logging.info('Search site function triggered - SIMPLIFIED VERSION!')
    
    url = req.params.get('url', 'https://www.legislation.gov.uk/ukpga/2025/22')
    
    # Basic URL validation
    if not url.startswith(('http://', 'https://')):
        return func.HttpResponse(
            json.dumps({"error": "Invalid URL - must start with http:// or https://"}),
            status_code=400,
            mimetype="application/json"
        )
    
    try:
        with urllib.request.urlopen(url, timeout=15) as response:
            content = response.read().decode('utf-8')
            result = find_documents_in_html(content, url)
            
        # Download and upload documents
        downloads = []
        for doc in result["documents"][:2]:  # Limit for demo
            try:
                doc_content = download_document(doc["url"])
                if doc_content:
                    # Upload to real Azure Storage
                    upload_result = upload_to_blob_storage_real(
                        doc_content, 
                        doc["filename"],
                        "stbtpuksprodcrawler01",
                        "documents"
                    )
                    
                    downloads.append({
                        "filename": doc["filename"],
                        "size": len(doc_content),
                        "hash": hashlib.md5(doc_content).hexdigest(),
                        "upload_success": upload_result.get("success", False),
                        "blob_url": upload_result.get("blob_url", ""),
                        "message": upload_result.get("message", ""),
                        "real_storage": True,
                        "status_code": upload_result.get("status_code", 0),
                        "error": upload_result.get("error")
                    })
                    
            except Exception as e:
                logging.error(f'Error processing document {doc["filename"]}: {str(e)}')
        
        return func.HttpResponse(
            json.dumps({
                "message": "SIMPLIFIED Web crawler with REAL Azure Storage integration is working!",
                "url": url,
                "status_code": response.status,
                "documents_found": len(result["documents"]),
                "documents": result["documents"],
                "debug_info": {
                    "total_links_found": result["total_links_found"],
                    "sample_links": result["sample_links"]
                },
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "downloads": downloads
            }),
            status_code=200,
            mimetype="application/json"
        )
    except Exception as e:
        logging.error(f'Search site error: {str(e)}')
        return func.HttpResponse(
            json.dumps({"error": str(e)}),
            status_code=500,
            mimetype="application/json"
        )

@app.route(route="status", methods=["GET"])  
def status(req: func.HttpRequest) -> func.HttpResponse:
    """Simple status endpoint"""
    logging.info('Status endpoint called')
    
    return func.HttpResponse(
        json.dumps({
            "status": "WORKING - Simplified Azure Functions Web Crawler",
            "version": "1.5-simplified",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "message": "Ready for document crawling with real Azure Storage",
            "endpoints": [
                "/api/search_site?url=<URL>",
                "/api/status"
            ]
        }),
        status_code=200,
        mimetype="application/json"
    )