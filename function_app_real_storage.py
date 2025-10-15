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
        
        # Convert relative URLs to absolute and categorize
        documents = []
        for link in parser.document_links:
            if link.startswith(('http://', 'https://')):
                absolute_url = link
            else:
                absolute_url = urllib.parse.urljoin(base_url, link)
            
            # Determine file type
            lower_link = link.lower()
            if any(lower_link.endswith(ext) for ext in {'.pdf', '.doc', '.docx', '.txt', '.xls', '.xlsx', '.xml', '.csv', '.rtf'}):
                file_ext = lower_link.split('.')[-1]
            else:
                file_ext = 'unknown'
            
            documents.append({
                "url": absolute_url,
                "filename": link.split('/')[-1] if '/' in link else link,
                "extension": file_ext,
                "original_link": link
            })
        
        # Return documents plus debugging info
        return {
            "documents": documents,
            "total_links_found": len(parser.all_links),
            "sample_links": parser.all_links[:10]  # First 10 links for debugging
        }
    except Exception as e:
        logging.error(f'HTML parsing error: {str(e)}')
        return {"documents": [], "total_links_found": 0, "sample_links": []}

def get_managed_identity_token():
    """Get access token using managed identity"""
    try:
        # Azure Functions managed identity endpoint
        identity_endpoint = "http://169.254.169.254/metadata/identity/oauth2/token"
        identity_header = "true"
        
        # Request token for Azure Storage
        params = {
            "api-version": "2018-02-01",
            "resource": "https://storage.azure.com/"
        }
        
        url = f"{identity_endpoint}?{urllib.parse.urlencode(params)}"
        
        req = urllib.request.Request(url)
        req.add_header("Metadata", identity_header)
        
        with urllib.request.urlopen(req, timeout=10) as response:
            token_data = json.loads(response.read().decode())
            return token_data.get("access_token")
            
    except Exception as e:
        logging.error(f'Failed to get managed identity token: {str(e)}')
        return None

def upload_to_blob_storage_real(content, filename, storage_account="stbtpuksprodcrawler01", container="documents"):
    """Upload content to Azure Blob Storage using REST API and managed identity"""
    try:
        # Get access token
        access_token = get_managed_identity_token()
        if not access_token:
            return {
                "success": False,
                "error": "Failed to get access token",
                "message": "Falling back to simulation"
            }
        
        # Construct blob URL
        blob_url = f"https://{storage_account}.blob.core.windows.net/{container}/{filename}"
        
        # Create request
        req = urllib.request.Request(blob_url, data=content, method='PUT')
        req.add_header("Authorization", f"Bearer {access_token}")
        req.add_header("x-ms-blob-type", "BlockBlob")
        req.add_header("x-ms-version", "2021-06-08")
        req.add_header("Content-Length", str(len(content)))
        
        # Determine content type based on file extension
        if filename.lower().endswith('.pdf'):
            req.add_header("Content-Type", "application/pdf")
        elif filename.lower().endswith('.xml'):
            req.add_header("Content-Type", "application/xml")
        elif filename.lower().endswith('.csv'):
            req.add_header("Content-Type", "text/csv")
        else:
            req.add_header("Content-Type", "application/octet-stream")
        
        # Upload to blob storage
        with urllib.request.urlopen(req, timeout=60) as response:
            status_code = response.status
            
        if status_code in [200, 201]:
            logging.info(f'Successfully uploaded {filename} to {blob_url}')
            return {
                "success": True,
                "blob_url": blob_url,
                "size": len(content),
                "message": "Real Azure Storage upload successful",
                "status_code": status_code
            }
        else:
            return {
                "success": False,
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
            content_type = response.headers.get('Content-Type', 'application/octet-stream')
            
        return {
            "success": True,
            "content": content,
            "content_type": content_type,
            "size": len(content)
        }
    except Exception as e:
        logging.error(f'Document download failed: {str(e)}')
        return {"success": False, "error": str(e)}

def calculate_content_hash(content):
    """Calculate MD5 hash of content for change detection"""
    return hashlib.md5(content).hexdigest()

# Function App with function level authentication for security
app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)

# Timer trigger function that runs every 4 hours
@app.timer_trigger(schedule="0 0 */4 * * *", arg_name="mytimer", run_on_startup=False,
              use_monitor=False) 
def scheduled_crawler(mytimer: func.TimerRequest) -> None:
    """Timer trigger function that crawls websites every 4 hours"""
    logging.info('Scheduled crawler function started - with REAL Azure Storage!')
    
    # Test crawling recent legislation
    try:
        test_url = "https://www.legislation.gov.uk/ukpga/2025/22"
        with urllib.request.urlopen(test_url, timeout=15) as response:
            content = response.read().decode('utf-8')
            result = find_documents_in_html(content, test_url)
            
        logging.info(f'Found {len(result["documents"])} documents on {test_url}')
        
        # Process first document if found
        if result["documents"]:
            doc = result["documents"][0]
            logging.info(f'Processing document: {doc["filename"]}')
            
            # Download document
            download_result = download_document(doc["url"])
            if download_result["success"]:
                # Calculate hash for change detection
                content_hash = calculate_content_hash(download_result["content"])
                
                # Upload to blob storage (REAL)
                upload_result = upload_to_blob_storage_real(
                    download_result["content"], 
                    doc["filename"]
                )
                
                logging.info(f'Document processing complete: {upload_result["message"]}')
                logging.info(f'Content hash: {content_hash}')
            
    except Exception as e:
        logging.error(f'Scheduled crawl failed: {str(e)}')

@app.route(route="manual_crawl", methods=["POST"])
def manual_crawl(req: func.HttpRequest) -> func.HttpResponse:
    """Manual trigger for crawling and downloading documents"""
    logging.info('Manual crawl function triggered - with REAL Azure Storage!')
    
    try:
        req_body = req.get_json()
        url = req_body.get('url') if req_body else None
        download_docs = req_body.get('download', False) if req_body else False
        use_real_storage = req_body.get('real_storage', True) if req_body else True
        
        if not url:
            url = "https://www.legislation.gov.uk/ukpga/2025/22"  # Default test URL
        
        # Basic URL validation
        if not url.startswith(('http://', 'https://')):
            return func.HttpResponse(
                json.dumps({"error": "Invalid URL - must start with http:// or https://"}),
                status_code=400,
                mimetype="application/json"
            )
        
        with urllib.request.urlopen(url, timeout=15) as response:
            content = response.read().decode('utf-8')
            result = find_documents_in_html(content, url)
        
        response_data = {
            "message": "Web crawler with REAL Azure Storage integration is working!",
            "url": url,
            "status_code": response.status,
            "documents_found": len(result["documents"]),
            "documents": result["documents"][:10],  # Limit to first 10
            "debug_info": {
                "total_links_found": result["total_links_found"],
                "sample_links": result["sample_links"]
            },
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        # Download and store documents if requested
        if download_docs and result["documents"]:
            downloads = []
            for doc in result["documents"][:2]:  # Limit to first 2 for testing real storage
                logging.info(f'Downloading {doc["filename"]}...')
                
                download_result = download_document(doc["url"])
                if download_result["success"]:
                    content_hash = calculate_content_hash(download_result["content"])
                    
                    if use_real_storage:
                        upload_result = upload_to_blob_storage_real(
                            download_result["content"], 
                            doc["filename"]
                        )
                    else:
                        # Fallback simulation
                        upload_result = {
                            "success": True,
                            "blob_url": f"https://stbtpuksprodcrawler01.blob.core.windows.net/documents/{doc['filename']}",
                            "size": len(download_result["content"]),
                            "message": "Simulated upload (real_storage=false)"
                        }
                    
                    downloads.append({
                        "filename": doc["filename"],
                        "size": download_result["size"],
                        "hash": content_hash,
                        "upload_success": upload_result["success"],
                        "blob_url": upload_result.get("blob_url", ""),
                        "message": upload_result.get("message", ""),
                        "real_storage": use_real_storage,
                        "status_code": upload_result.get("status_code"),
                        "error": upload_result.get("error")
                    })
                else:
                    downloads.append({
                        "filename": doc["filename"],
                        "error": download_result["error"]
                    })
            
            response_data["downloads"] = downloads
            
        return func.HttpResponse(
            json.dumps(response_data),
            status_code=200,
            mimetype="application/json"
        )
    except Exception as e:
        logging.error(f'Manual crawl error: {str(e)}')
        return func.HttpResponse(
            json.dumps({"error": str(e)}),
            status_code=500,
            mimetype="application/json"
        )

@app.route(route="search_site", methods=["GET"])
def search_site(req: func.HttpRequest) -> func.HttpResponse:
    """Search a specific site for documents with enhanced detection"""
    logging.info('Search site function triggered - with REAL Azure Storage!')
    
    url = req.params.get('url', 'https://www.legislation.gov.uk/')
    
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
            
        return func.HttpResponse(
            json.dumps({
                "url": url,
                "status_code": response.status,
                "content_length": len(content),
                "documents_found": len(result["documents"]),
                "documents": result["documents"],
                "debug_info": {
                    "total_links_found": result["total_links_found"],
                    "sample_links": result["sample_links"]
                },
                "message": "Enhanced document search with REAL Azure Storage integration successful"
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