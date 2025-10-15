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
import os
import gzip
import io

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
            r'/ukpga/\d{4}-\d{4}', # UK legislation decade-based links (e.g., /ukpga/1990-1999)
            r'/ukpga/\d{4}',       # UK legislation year-based links (e.g., /ukpga/2025)
            r'/uksi/\d{4}',        # UK statutory instruments by year
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

def crawl_document_page_for_sub_documents(doc_url, base_url, max_depth=1, current_depth=1):
    """Step 5a: Crawl a document page to find additional sub-documents (Level 2+ crawling)"""
    if current_depth >= max_depth:
        return []
    
    try:
        logging.info(f'Step 5a: Deep crawling level {current_depth + 1} - {doc_url}')
        
        # Use same advanced headers as main crawler
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'en-GB,en;q=0.9',
            'Sec-Ch-Ua': '"Google Chrome";v="119", "Chromium";v="119", "Not?A_Brand";v="24"',
            'Sec-Ch-Ua-Mobile': '?0',
            'Sec-Ch-Ua-Platform': '"Windows"',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Upgrade-Insecure-Requests': '1',
            'Connection': 'keep-alive',
            'Cache-Control': 'max-age=0'
        }
        
        req = urllib.request.Request(doc_url, headers=headers)
        with urllib.request.urlopen(req, timeout=15) as response:
            # Handle gzipped responses properly
            raw_content = response.read()
            if response.info().get('Content-Encoding') == 'gzip':
                content = gzip.decompress(raw_content).decode('utf-8')
            else:
                content = raw_content.decode('utf-8')
            
            # Find documents on this sub-page
            result = find_documents_in_html(content, doc_url)
            sub_documents = result["documents"]
            
            # Filter out documents that don't belong to same domain (avoid external links)
            domain_base = urllib.parse.urlparse(base_url).netloc
            filtered_docs = []
            
            for doc in sub_documents:
                doc_domain = urllib.parse.urlparse(doc["url"]).netloc
                if doc_domain == domain_base:
                    # Mark as sub-document for tracking
                    doc["crawl_level"] = current_depth + 1
                    doc["parent_url"] = doc_url
                    filtered_docs.append(doc)
            
            logging.info(f'Step 5a: Found {len(filtered_docs)} sub-documents on level {current_depth + 1}')
            return filtered_docs
            
    except Exception as e:
        logging.warning(f'Step 5a: Failed to crawl sub-page {doc_url}: {str(e)}')
        return []

def get_managed_identity_token():
    """Get access token using managed identity - FIXED for Azure Functions"""
    try:
        # Check for Azure Functions environment variables first (FIXED AUTH)
        identity_endpoint = os.environ.get('IDENTITY_ENDPOINT')
        identity_header = os.environ.get('IDENTITY_HEADER')
        
        if identity_endpoint and identity_header:
            # Azure Functions managed identity method
            logging.info('Using Azure Functions managed identity endpoint')
            token_url = f"{identity_endpoint}?resource=https://storage.azure.com/&api-version=2019-08-01"
            req = urllib.request.Request(token_url)
            req.add_header('X-IDENTITY-HEADER', identity_header)
        else:
            # Fallback to standard VM metadata endpoint
            logging.info('Using standard VM metadata endpoint')
            token_url = "http://169.254.169.254/metadata/identity/oauth2/token?api-version=2018-02-01&resource=https://storage.azure.com/"
            req = urllib.request.Request(token_url)
            req.add_header('Metadata', 'true')
        
        with urllib.request.urlopen(req, timeout=10) as response:
            token_data = json.loads(response.read().decode())
            logging.info('Successfully obtained access token')
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

def get_document_hashes_from_storage(storage_account="stbtpuksprodcrawler01", container="documents"):
    """Retrieve stored document hashes from Azure Storage for change detection - using existing documents container"""
    try:
        access_token = get_managed_identity_token()
        if not access_token:
            logging.error('Failed to get access token for hash retrieval')
            return {}
            
        filename = "document_hashes.json"
        url = f"https://{storage_account}.blob.core.windows.net/{container}/{filename}"
        
        req = urllib.request.Request(url, method='GET')
        req.add_header('Authorization', f'Bearer {access_token}')
        req.add_header('x-ms-version', '2020-04-08')
        
        with urllib.request.urlopen(req, timeout=30) as response:
            hash_data = json.loads(response.read().decode())
            logging.info(f'Retrieved {len(hash_data)} stored document hashes from {container}/{filename}')
            return hash_data
            
    except urllib.error.HTTPError as e:
        if e.code == 404:
            logging.info('No previous hash file found - this appears to be the first run')
            return {}
        else:
            logging.error(f'HTTP error retrieving hashes: {e.code} {e.reason}')
            return {}
    except Exception as e:
        logging.error(f'Error retrieving document hashes: {str(e)}')
        return {}

def get_enabled_websites():
    """Step 5a: Multi-Level Deep Crawling - CPS + Baseline with sub-document discovery"""
    website_configs = {
        "college_of_policing": {
            "name": "College of Policing",
            "url": "https://www.college.police.uk/",
            "enabled": False,
            "description": "BLOCKED: Advanced anti-bot protection - requires specialized bypass",
            "document_types": ["pdf", "doc", "docx", "xml"],
            "crawl_depth": "deep",
            "priority": "blocked"
        },
        "cps_working": {
            "name": "Crown Prosecution Service",
            "url": "https://www.cps.gov.uk/prosecution-guidance",
            "enabled": True,
            "description": "CPS prosecution guidance and legal policies (2-level crawl enabled)",
            "document_types": ["pdf", "doc", "docx", "xml", "html"],
            "crawl_depth": "deep",
            "priority": "high",
            "multi_level": True,
            "max_depth": 2
        },
        "legislation_test_working": {
            "name": "UK Legislation (Test - Working)",
            "url": "https://www.legislation.gov.uk/uksi/2024/1052/contents",
            "enabled": True,
            "description": "Keep one working legislation site for comparison",
            "document_types": ["pdf", "xml"],
            "crawl_depth": "single",
            "priority": "baseline"
        },
        "npcc_future": {
            "name": "National Police Chiefs' Council",
            "url": "https://www.npcc.police.uk/",
            "enabled": False,
            "description": "NPCC guidance - Step 4b",
            "document_types": ["pdf", "doc", "docx", "xml"],
            "crawl_depth": "deep",
            "priority": "high" 
        },
        "cps_future": {
            "name": "Crown Prosecution Service",
            "url": "https://www.cps.gov.uk/",
            "enabled": False,
            "description": "CPS legal guidance - Step 4c",
            "document_types": ["pdf", "doc", "docx", "xml"],
            "crawl_depth": "deep",
            "priority": "high"
        },
        "uk_legislation_future": {
            "name": "UK Public General Acts",
            "url": "https://www.legislation.gov.uk/ukpga",
            "enabled": True,
            "description": "UK Public General Acts from all years - comprehensive legal database (ENABLED)",
            "document_types": ["pdf", "xml", "html"],
            "crawl_depth": "deep",
            "priority": "high",
            "multi_level": True,
            "max_depth": 2
        },
        "gov_uk_future": {
            "name": "GOV.UK",
            "url": "https://www.gov.uk/",
            "enabled": False,
            "description": "UK government guidance and publications - Step 4e",
            "document_types": ["pdf", "doc", "docx", "csv", "xml"],
            "crawl_depth": "deep",
            "priority": "high"
        }
    }
    
    enabled_sites = []
    for site_id, config in website_configs.items():
        if config.get("enabled", False):
            enabled_sites.append({
                "id": site_id,
                "name": config["name"],
                "url": config["url"],
                "description": config["description"]
            })
    
    return enabled_sites

def store_document_hashes_to_storage(hash_data, storage_account="stbtpuksprodcrawler01", container="documents"):
    """Store document hashes to Azure Storage for change detection - using existing documents container"""
    try:
        access_token = get_managed_identity_token()
        if not access_token:
            logging.error('Failed to get access token for hash storage')
            return False
            
        filename = "document_hashes.json"
        content = json.dumps(hash_data, indent=2).encode('utf-8')
        
        url = f"https://{storage_account}.blob.core.windows.net/{container}/{filename}"
        
        req = urllib.request.Request(url, data=content, method='PUT')
        req.add_header('Authorization', f'Bearer {access_token}')
        req.add_header('x-ms-version', '2020-04-08')
        req.add_header('x-ms-blob-type', 'BlockBlob')
        req.add_header('Content-Type', 'application/json')
        req.add_header('Content-Length', str(len(content)))
        
        with urllib.request.urlopen(req, timeout=30) as response:
            if response.status == 201:
                logging.info(f'Successfully stored {len(hash_data)} document hashes to {container}/{filename}')
                return True
            else:
                logging.error(f'Failed to store hashes: HTTP {response.status}')
                return False
                
    except urllib.error.HTTPError as e:
        logging.error(f'HTTP error storing document hashes: {e.code} {e.reason}')
        return False
    except Exception as e:
        logging.error(f'Error storing document hashes: {str(e)}')
        return False

# Function App with anonymous authentication
app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

# Timer trigger function that runs every 4 hours
@app.timer_trigger(schedule="0 0 */4 * * *", arg_name="mytimer", run_on_startup=False,
              use_monitor=False) 
def scheduled_crawler(mytimer: func.TimerRequest) -> None:
    """Step 5a: Timer trigger function with multi-level crawling every 4 hours"""
    logging.info('Step 3b: Scheduled multi-website crawler started - 4-hour automated crawling with change detection!')
    
    # Step 3b: Get enabled websites from configuration
    enabled_sites = get_enabled_websites()
    logging.info(f'Step 3b: Found {len(enabled_sites)} enabled websites to process')
    
    total_processed = 0
    total_new = 0
    total_changed = 0
    total_unchanged = 0
    total_uploaded = 0
    total_sites_processed = 0
    site_results = []
    
    for site_config in enabled_sites:
        site_url = site_config["url"]
        site_name = site_config["name"]
        total_sites_processed += 1
        try:
            logging.info(f'Step 4a: Processing site {total_sites_processed}/{len(enabled_sites)} - {site_name} ({site_url})')
            
            # Advanced headers with Chrome security context for government/police sites
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                'Accept-Language': 'en-GB,en;q=0.9',
                'Sec-Ch-Ua': '"Google Chrome";v="119", "Chromium";v="119", "Not?A_Brand";v="24"',
                'Sec-Ch-Ua-Mobile': '?0',
                'Sec-Ch-Ua-Platform': '"Windows"',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1',
                'Upgrade-Insecure-Requests': '1',
                'Connection': 'keep-alive',
                'Cache-Control': 'max-age=0'
            }
            
            req = urllib.request.Request(site_url, headers=headers)
            try:
                with urllib.request.urlopen(req, timeout=15) as response:
                    # Handle gzipped responses properly
                    raw_content = response.read()
                    if response.info().get('Content-Encoding') == 'gzip':
                        content = gzip.decompress(raw_content).decode('utf-8')
                    else:
                        content = raw_content.decode('utf-8')
                    result = find_documents_in_html(content, site_url)
            except urllib.error.HTTPError as e:
                if e.code == 403:
                    logging.warning(f'Step 4a: Site {site_name} blocked (403) - government anti-bot protection')
                    site_results.append({
                        "site_name": site_name,
                        "site_url": site_url,
                        "status": "blocked",
                        "error": "HTTP 403 - Anti-bot protection",
                        "documents_found": 0,
                        "suggestion": "Site requires advanced bypass techniques"
                    })
                    continue
                else:
                    raise
            
            all_documents = result["documents"]
            logging.info(f'Step 5a: Found {len(all_documents)} Level 1 documents on {site_name}')
            
            # Step 5a: Multi-level crawling if enabled
            if site_config.get("multi_level", False) and site_config.get("max_depth", 1) > 1:
                max_depth = site_config.get("max_depth", 2)  
                logging.info(f'Step 5a: Starting multi-level crawl for {site_name} (max depth: {max_depth})')
                
                # Crawl each Level 1 document for sub-documents  
                level1_count = len(all_documents)
                sub_documents_found = 0
                
                for level1_doc in all_documents[:3]:  # Limit to first 3 for safety and testing
                    try:
                        sub_docs = crawl_document_page_for_sub_documents(
                            level1_doc["url"], 
                            site_url, 
                            max_depth=max_depth, 
                            current_depth=1
                        )
                        all_documents.extend(sub_docs)
                        sub_documents_found += len(sub_docs)
                        
                        # Add small delay to be respectful
                        import time
                        time.sleep(1)
                        
                    except Exception as e:
                        logging.warning(f'Step 5a: Failed to crawl sub-docs for {level1_doc["url"]}: {str(e)}')
                        continue
                
                logging.info(f'Step 5a: Multi-level crawl complete - {level1_count} Level 1 + {sub_documents_found} Level 2+ = {len(all_documents)} total documents')
            
            if not all_documents:
                continue
                
            # Step 5a: Get previous document hashes for change detection
            previous_hashes = get_document_hashes_from_storage()
            current_hashes = {}
            
            # Process all documents (Level 1 + Level 2+) with change detection
            for i, doc in enumerate(all_documents):
                try:
                    logging.info(f'Step 5a: Processing document {i+1}/{len(all_documents)} from {site_name} - {doc["filename"]}')
                    
                    # Download to get current hash
                    download_result = download_document(doc["url"])
                    
                    if download_result["success"]:
                        current_hash = calculate_content_hash(download_result["content"])
                        current_hashes[doc["url"]] = {
                            "filename": doc["filename"],
                            "hash": current_hash,
                            "last_seen": datetime.now(timezone.utc).isoformat()
                        }
                        
                        # Check if document has changed
                        previous_hash = previous_hashes.get(doc["url"], {}).get("hash")
                        
                        if previous_hash is None:
                            # New document
                            status = "new"
                            total_new += 1
                            should_upload = True
                        elif previous_hash != current_hash:
                            # Changed document  
                            status = "changed"
                            total_changed += 1
                            should_upload = True
                        else:
                            # Unchanged document
                            status = "unchanged"
                            total_unchanged += 1
                            should_upload = False
                        
                        total_processed += 1
                        
                        # Only upload if document is new or changed
                        if should_upload:
                            storage_result = upload_to_blob_storage_real(download_result["content"], doc["filename"])
                            if storage_result["success"]:
                                total_uploaded += 1
                                logging.info(f'Step 3b: Uploaded {doc["filename"]} from {site_name} - Status: {status}')
                            else:
                                logging.error(f'Step 3b: Upload failed for {doc["filename"]} from {site_name} - {storage_result.get("error", "Unknown error")}')
                        else:
                            logging.info(f'Step 3b: Skipped upload for {doc["filename"]} from {site_name} - Status: {status}')
                            
                    else:
                        logging.error(f'Step 3b: Download failed for {doc["filename"]} from {site_name} - {download_result["error"]}')
                        
                except Exception as doc_error:
                    logging.error(f'Step 3b: Error processing document {doc["filename"]} from {site_name}: {str(doc_error)}')
            
            # Store updated hashes for next run
            if current_hashes:
                store_success = store_document_hashes_to_storage(current_hashes)
                if store_success:
                    logging.info(f'Step 3b: Successfully stored {len(current_hashes)} document hashes for {site_name}')
                else:
                    logging.error(f'Step 3b: Failed to store document hashes for {site_name}')
                    
        except Exception as site_error:
            logging.error(f'Step 3b: Error processing site {site_name} ({site_url}): {str(site_error)}')
    
    # Log comprehensive summary
    logging.info(f'Step 3b: Multi-website scheduled crawl complete - Sites: {total_sites_processed}/{len(enabled_sites)}, Documents: {total_processed}, New: {total_new}, Changed: {total_changed}, Unchanged: {total_unchanged}, Uploaded: {total_uploaded}')

@app.route(route="manual_crawl", methods=["POST"], auth_level=func.AuthLevel.ANONYMOUS)
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
        
        # Advanced headers for government/police sites with strong anti-bot protection
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'en-GB,en;q=0.9',
            'Sec-Ch-Ua': '"Google Chrome";v="119", "Chromium";v="119", "Not?A_Brand";v="24"',
            'Sec-Ch-Ua-Mobile': '?0',
            'Sec-Ch-Ua-Platform': '"Windows"',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Upgrade-Insecure-Requests': '1',
            'Connection': 'keep-alive',
            'Cache-Control': 'max-age=0'
        }
        
        req = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=15) as response:
                # Handle gzipped responses properly
                raw_content = response.read()
                if response.info().get('Content-Encoding') == 'gzip':
                    content = gzip.decompress(raw_content).decode('utf-8')
                else:
                    content = raw_content.decode('utf-8')
                result = find_documents_in_html(content, url)
        except urllib.error.HTTPError as e:
            if e.code == 403:
                # Government site blocking - try alternative approach
                return func.HttpResponse(
                    json.dumps({
                        "error": f"HTTP Error 403: Site blocking detected",
                        "url": url,
                        "message": "Government/police site has anti-bot protection",
                        "suggestion": "Site may require session cookies or JS execution",
                        "step": "4a",
                        "status": "blocked"
                    }),
                    status_code=403,
                    mimetype="application/json"
                )
            else:
                raise
        
        all_documents = result["documents"]
        logging.info(f'Step 5a Manual: Found {len(all_documents)} Level 1 documents')
        
        # Step 5a: Multi-level crawling for CPS and UK Legislation
        site_domain = urllib.parse.urlparse(url).netloc
        sub_documents_found = 0
        
        if "cps.gov.uk" in site_domain:
            logging.info(f'Step 5a Manual: Starting multi-level crawl for CPS (max depth: 2)')
            
            # Crawl each Level 1 document for sub-documents
            for level1_doc in all_documents[:5]:  # Process first 5 categories for manual testing
                try:
                    sub_docs = crawl_document_page_for_sub_documents(
                        level1_doc["url"], 
                        url, 
                        max_depth=2, 
                        current_depth=1
                    )
                    
                    if sub_docs:
                        all_documents.extend(sub_docs[:10])  # Add up to 10 sub-docs per category
                        sub_documents_found += len(sub_docs)
                        logging.info(f'Step 5a Manual: Found {len(sub_docs)} sub-documents in {level1_doc["url"]}')
                    
                except Exception as sub_error:
                    logging.warning(f'Step 5a Manual: Error crawling sub-page {level1_doc["url"]}: {str(sub_error)}')
        
        elif "legislation.gov.uk" in site_domain:
            logging.info(f'Step 5a Manual: Starting multi-level crawl for UK Legislation (max depth: 2)')
            
            # Crawl each Level 1 document (likely year-based listings) for Acts
            for level1_doc in all_documents[:5]:  # Process first 5 year categories for manual testing
                try:
                    sub_docs = crawl_document_page_for_sub_documents(
                        level1_doc["url"], 
                        url, 
                        max_depth=2, 
                        current_depth=1
                    )
                    
                    if sub_docs:
                        all_documents.extend(sub_docs[:15])  # Add up to 15 Acts per year for comprehensive coverage
                        sub_documents_found += len(sub_docs)
                        logging.info(f'Step 5a Manual: Found {len(sub_docs)} Acts in {level1_doc["url"]}')
                    
                except Exception as sub_error:
                    logging.warning(f'Step 5a Manual: Error crawling legislation sub-page {level1_doc["url"]}: {str(sub_error)}')
        
        if sub_documents_found > 0:
            logging.info(f'Step 5a Manual: Multi-level crawl complete - Total documents: {len(all_documents)}, Sub-documents: {sub_documents_found}')
        
        response_data = {
            "message": "Web crawler with REAL Azure Storage integration is working!",
            "url": url,
            "status_code": response.status,
            "documents_found": len(all_documents),
            "documents": all_documents[:15],  # Show more documents now that we have multi-level
            "debug_info": {
                "total_links_found": result["total_links_found"],
                "sample_links": result["sample_links"]
            },
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        # Download and store documents if requested
        if download_docs and all_documents:
            downloads = []
            for doc in all_documents[:5]:  # Download first 5 documents (may include sub-documents)
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

@app.route(route="search_site", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
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
            # Handle gzipped responses properly
            raw_content = response.read()
            if response.info().get('Content-Encoding') == 'gzip':
                content = gzip.decompress(raw_content).decode('utf-8')
            else:
                content = raw_content.decode('utf-8')
            result = find_documents_in_html(content, url)
            
        # Step 2a: Get previous document hashes for change detection
        previous_hashes = get_document_hashes_from_storage()
        current_hashes = {}
        
        # Step 2a+2b: Process ALL documents with change detection
        download_results = []
        successful_downloads = 0
        successful_uploads = 0
        unchanged_count = 0
        changed_count = 0
        new_count = 0
        
        if result["documents"]:
            logging.info(f'Step 2a: Processing {len(result["documents"])} documents with change detection')
            
            for i, doc in enumerate(result["documents"]):
                try:
                    logging.info(f'Step 2a: Processing document {i+1}/{len(result["documents"])} - {doc["filename"]}')
                    
                    # First, download to get current hash
                    download_result = download_document(doc["url"])
                    
                    if download_result["success"]:
                        current_hash = calculate_content_hash(download_result["content"])
                        current_hashes[doc["url"]] = {
                            "filename": doc["filename"],
                            "hash": current_hash,
                            "last_seen": datetime.now(timezone.utc).isoformat()
                        }
                        
                        # Check if document has changed
                        previous_hash = previous_hashes.get(doc["url"], {}).get("hash")
                        
                        if previous_hash is None:
                            # New document
                            status = "new"
                            new_count += 1
                            should_upload = True
                        elif previous_hash != current_hash:
                            # Changed document  
                            status = "changed"
                            changed_count += 1
                            should_upload = True
                        else:
                            # Unchanged document
                            status = "unchanged"
                            unchanged_count += 1
                            should_upload = False
                        
                        successful_downloads += 1
                        
                        # Only upload if document is new or changed
                        if should_upload:
                            storage_result = upload_to_blob_storage_real(download_result["content"], doc["filename"])
                            if storage_result["success"]:
                                successful_uploads += 1
                        else:
                            storage_result = {"success": True, "skipped": True}
                        
                        download_results.append({
                            "filename": doc["filename"],
                            "size": download_result["size"],
                            "hash": current_hash,
                            "content_type": download_result["content_type"],
                            "downloaded": True,
                            "uploaded_to_storage": storage_result["success"],
                            "storage_url": storage_result.get("url", None),
                            "storage_error": storage_result.get("error", None),
                            "document_index": i + 1,
                            "change_status": status,
                            "previous_hash": previous_hash,
                            "upload_skipped": storage_result.get("skipped", False)
                        })
                    else:
                        download_results.append({
                            "filename": doc["filename"],
                            "error": download_result["error"],
                            "downloaded": False,
                            "uploaded_to_storage": False,
                            "document_index": i + 1,
                            "change_status": "download_failed"
                        })
                except Exception as e:
                    download_results.append({
                        "filename": doc["filename"],
                        "error": str(e),
                        "downloaded": False,
                        "uploaded_to_storage": False,
                        "document_index": i + 1,
                        "change_status": "error"
                    })
            
            # Store updated hashes for next run
            if current_hashes:
                store_document_hashes_to_storage(current_hashes)
            
        return func.HttpResponse(
            json.dumps({
                "url": url,
                "status_code": response.status,
                "content_length": len(content),
                "documents_found": len(result["documents"]),
                "documents": result["documents"],
                "download_ready": len(result["documents"]) > 0,
                "downloadable_count": len([d for d in result["documents"] if d["extension"] in ["pdf", "xml", "doc", "docx"]]),
                "download_results": download_results,
                "processing_summary": {
                    "total_documents": len(result["documents"]),
                    "successful_downloads": successful_downloads,
                    "successful_uploads": successful_uploads,
                    "new_documents": new_count,
                    "changed_documents": changed_count,
                    "unchanged_documents": unchanged_count,
                    "step": "4a"
                },
                "debug_info": {
                    "total_links_found": result["total_links_found"],
                    "sample_links": result["sample_links"]
                },
                "message": "Step 2a: Multi-document processing with change detection and smart Azure Storage upload"
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

@app.route(route="status", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
def status(req: func.HttpRequest) -> func.HttpResponse:
    """Simple system status endpoint - NEW ADDITION"""
    logging.info('Status endpoint called')
    
    return func.HttpResponse(
        json.dumps({
            "status": "WORKING",
            "message": "Web crawler with REAL Azure Storage integration is operational",
            "version": "1.1-status-endpoint",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "storage_account": "stbtpuksprodcrawler01",
            "container": "documents",
            "features": [
                "Document discovery",
                "Real Azure Storage uploads", 
                "PDF and XML support",
                "4-hour timer scheduling",
                "Fixed managed identity auth"
            ]
        }),
        status_code=200,
        mimetype="application/json"
    )

@app.route(route="websites", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
def websites(req: func.HttpRequest) -> func.HttpResponse:
    """Simple website configuration endpoint - shows available crawl targets"""
    logging.info('Website configuration endpoint called')
    
    # Step 3b: Enhanced website configuration with specific URLs
    website_configs = {
        "legislation_si_2024_1052": {
            "name": "UK Legislation - SI 2024/1052",
            "url": "https://www.legislation.gov.uk/uksi/2024/1052/contents",
            "enabled": True,
            "description": "Specific legislation document (proven working)",
            "document_types": ["pdf", "xml"]
        },
        "legislation_si_recent": {
            "name": "UK Legislation - Recent SI",
            "url": "https://www.legislation.gov.uk/uksi/2024/1051/contents",
            "enabled": True,
            "description": "Another recent legislation document",
            "document_types": ["pdf", "xml"]
        },
        "legislation_ukpga_sample": {
            "name": "UK Legislation - UKPGA Sample",
            "url": "https://www.legislation.gov.uk/ukpga/2024/22/contents",
            "enabled": False,
            "description": "UK Public General Acts sample",
            "document_types": ["pdf", "xml"]
        },
        "test_site": {
            "name": "Test Site",
            "url": "https://www.legislation.gov.uk/uksi/2024/1050/contents",
            "enabled": False,
            "description": "Additional test site for expansion",
            "document_types": ["pdf", "xml"]
        }
    }
    
    return func.HttpResponse(
        json.dumps({
            "message": "Available website configurations",
            "total_websites": len(website_configs),
            "enabled_count": sum(1 for w in website_configs.values() if w["enabled"]),
            "websites": website_configs,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }),
        status_code=200,
        mimetype="application/json"
    )

@app.route(route="crawl", methods=["POST"], auth_level=func.AuthLevel.ANONYMOUS)
def crawl(req: func.HttpRequest) -> func.HttpResponse:
    """Simple crawl endpoint - alias for manual_crawl for easier access"""
    return manual_crawl(req)

@app.route(route="manage_websites", methods=["GET", "POST"], auth_level=func.AuthLevel.ANONYMOUS)
def manage_websites(req: func.HttpRequest) -> func.HttpResponse:
    """Step 3b: Management endpoint to view and manage websites for crawling"""
    logging.info('Step 3b: Website management endpoint called')
    
    if req.method == "GET":
        # Get current enabled sites
        enabled_sites = get_enabled_websites()
        
        return func.HttpResponse(
            json.dumps({
                "message": "Step 3b: Multi-website crawler configuration",
                "enabled_sites": enabled_sites,
                "total_enabled": len(enabled_sites),
                "next_scheduled_run": "Every 4 hours at 12:00 AM, 4:00 AM, 8:00 AM, 12:00 PM, 4:00 PM, 8:00 PM",
                "step": "3b"
            }),
            status_code=200,
            mimetype="application/json"
        )
    
    # POST method for future configuration changes
    try:
        req_body = req.get_json()
        action = req_body.get('action') if req_body else None
        
        return func.HttpResponse(
            json.dumps({
                "message": "Website configuration management (read-only in current version)",
                "note": "To modify enabled sites, update the get_enabled_websites() function",
                "current_enabled_count": len(get_enabled_websites()),
                "step": "3b"
            }),
            status_code=200,
            mimetype="application/json"
        )
    
    except Exception as e:
        logging.error(f'Step 3b: Website management error: {str(e)}')
        return func.HttpResponse(
            json.dumps({"error": f"Website management failed: {str(e)}"}),
            status_code=500,
            mimetype="application/json"
        )