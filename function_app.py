import azure.functions as func
import azure.durable_functions as df
import logging
import json
import urllib.request
import urllib.parse
import urllib.error
from datetime import datetime, timezone, timedelta
from html.parser import HTMLParser
import re
import hashlib
import hmac
import base64
import os
import gzip
import io

class HTMLContentExtractor(HTMLParser):
    """Extract main content from HTML guidance pages for College of Policing"""
    def __init__(self):
        super().__init__()
        self.content_text = []
        self.in_main_content = False
        self.in_navigation = False
        self.in_header = False
        self.in_footer = False
        self.current_tag = None
        
    def handle_starttag(self, tag, attrs):
        self.current_tag = tag
        attrs_dict = dict(attrs)
        
        # Detect main content areas - be more permissive for College of Policing
        if tag in ['main', 'article', 'section']:
            self.in_main_content = True
        elif 'class' in attrs_dict:
            classes = attrs_dict['class'].lower()
            # Look for common content indicators
            if any(x in classes for x in ['main-content', 'content', 'guidance', 'article', 'page-content', 'body', 'col8']):
                self.in_main_content = True
            elif any(x in classes for x in ['nav', 'navigation', 'menu', 'sidebar', 'header', 'footer']):
                self.in_navigation = True
        elif 'id' in attrs_dict:
            id_val = attrs_dict['id'].lower()
            if any(x in id_val for x in ['main-content', 'content', 'guidance', 'article']):
                self.in_main_content = True
        
        # Detect navigation/header/footer areas to skip
        if tag in ['nav', 'header', 'footer']:
            if tag == 'nav':
                self.in_navigation = True
            elif tag == 'header':
                self.in_header = True
            elif tag == 'footer':
                self.in_footer = True
    
    def handle_endtag(self, tag):
        if tag in ['main', 'article', 'section']:
            self.in_main_content = False
        elif tag == 'nav':
            self.in_navigation = False
        elif tag == 'header':
            self.in_header = False
        elif tag == 'footer':
            self.in_footer = False
        self.current_tag = None
    
    def handle_data(self, data):
        # Only capture text from main content, skip navigation/header/footer
        if self.in_main_content and not self.in_navigation and not self.in_header and not self.in_footer:
            text = data.strip()
            if text and len(text) > 10:  # Skip very short snippets
                self.content_text.append(text)
    
    def get_content(self):
        """Get extracted content as formatted text"""
        return '\n\n'.join(self.content_text)
    
    def has_substantial_content(self):
        """Check if page has substantial guidance content (not just navigation)"""
        total_chars = sum(len(text) for text in self.content_text)
        return total_chars > 200  # At least 200 chars of content (lowered from 500)

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
            r'/pdfs/',          # legislation.gov.uk PDFs folder
            r'/data\.xml',      # legislation.gov.uk XML data files
            r'/data\.akn',      # legislation.gov.uk AKN format
            r'/data\.htm',      # legislation.gov.uk HTML data format
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

def generate_unique_filename(url, original_filename, site_name="unknown"):
    """Generate unique filename preventing collisions with folder organization
    
    Args:
        url: Full document URL
        original_filename: Original filename from URL
        site_name: Source website name for folder organization
    
    Returns:
        str: Unique filename with folder prefix (e.g., "crown-prosecution-service/abc123_doc.pdf")
    """
    # Generate URL hash for uniqueness (8 chars is sufficient)
    url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
    
    # Sanitize site name for folder structure
    safe_site = re.sub(r'[^a-z0-9-]', '', site_name.lower().replace(' ', '-'))[:30]
    if not safe_site:
        safe_site = "unknown"
    
    # Extract and preserve extension
    if '.' in original_filename:
        ext = '.' + original_filename.split('.')[-1].lower()
        base_name = original_filename.rsplit('.', 1)[0]
    else:
        ext = '.pdf'  # Default extension
        base_name = original_filename
    
    # Sanitize base filename (remove special chars, limit length)
    safe_base = re.sub(r'[^a-zA-Z0-9_-]', '_', base_name)[:50]
    if not safe_base:
        safe_base = "document"
    
    # Format: folder/hash_filename.ext
    # Folder provides organization, hash ensures uniqueness, base provides readability
    return f"{safe_site}/{url_hash}_{safe_base}{ext}"

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
            
            # Original filename from URL (for reference)
            original_filename = link.split('/')[-1] if '/' in link else link
            
            documents.append({
                "url": absolute_url,
                "filename": original_filename,  # Keep original for logging
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

def get_folder_name_for_website(website_name):
    """Convert website name to folder name for blob storage organization
    
    Args:
        website_name: Website display name (e.g., "Crown Prosecution Service")
    
    Returns:
        str: Sanitized folder name (e.g., "crown-prosecution-service")
    """
    # Convert to lowercase and replace spaces with hyphens
    folder_name = website_name.lower().replace(' ', '-')
    # Remove special characters, keep only alphanumeric and hyphens
    folder_name = re.sub(r'[^a-z0-9-]', '', folder_name)
    # Limit length for Azure blob naming
    return folder_name[:63]

def ensure_website_folder_exists(website_name, storage_account="stbtpuksprodcrawler01", container="documents"):
    """Create a placeholder file to establish a website folder in blob storage
    
    Args:
        website_name: Website display name
        storage_account: Azure storage account name
        container: Container name
    
    Returns:
        bool: True if folder exists or was created successfully
    """
    try:
        folder_name = get_folder_name_for_website(website_name)
        
        # Create a .folder placeholder file
        # This ensures the folder appears in Azure Storage Explorer
        placeholder_filename = f"{folder_name}/.folder"
        placeholder_content = json.dumps({
            "website_name": website_name,
            "folder_created": datetime.now(timezone.utc).isoformat(),
            "purpose": "Folder placeholder for document organization"
        }, indent=2).encode('utf-8')
        
        # Upload placeholder
        access_token = get_managed_identity_token()
        if not access_token:
            logging.warning('Failed to get access token for folder creation')
            return False
        
        blob_url = f"https://{storage_account}.blob.core.windows.net/{container}/{placeholder_filename}"
        
        req = urllib.request.Request(blob_url, data=placeholder_content, method='PUT')
        req.add_header('Authorization', f'Bearer {access_token}')
        req.add_header('x-ms-blob-type', 'BlockBlob')
        req.add_header('x-ms-version', '2021-06-08')
        req.add_header('Content-Type', 'application/json')
        req.add_header('Content-Length', str(len(placeholder_content)))
        
        # Add metadata
        req.add_header('x-ms-meta-folderplaceholder', 'true')
        req.add_header('x-ms-meta-websitename', urllib.parse.quote(website_name))
        
        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                if response.status in [200, 201]:
                    logging.info(f'✅ Created folder for website: {folder_name}')
                    return True
        except urllib.error.HTTPError as e:
            if e.code == 409:
                # Already exists - this is fine
                logging.info(f'Folder already exists: {folder_name}')
                return True
            else:
                logging.warning(f'Failed to create folder {folder_name}: HTTP {e.code}')
                return False
                
        return True
        
    except Exception as e:
        logging.error(f'Error creating folder for {website_name}: {str(e)}')
        return False

def ensure_container_exists(container_name, storage_account="stbtpuksprodcrawler01"):
    """Create container if it doesn't exist using REST API
    
    Args:
        container_name: Name of container to create
        storage_account: Azure storage account name
    
    Returns:
        bool: True if container exists or was created successfully
    """
    try:
        access_token = get_managed_identity_token()
        if not access_token:
            logging.error('Failed to get access token for container creation')
            return False
        
        # Create container using REST API
        # PUT /{container}?restype=container
        url = f"https://{storage_account}.blob.core.windows.net/{container_name}?restype=container"
        
        req = urllib.request.Request(url, method='PUT')
        req.add_header('Authorization', f'Bearer {access_token}')
        req.add_header('x-ms-version', '2021-06-08')
        
        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                status_code = response.status
                if status_code == 201:
                    logging.info(f'✅ Created new container: {container_name}')
                    return True
                elif status_code == 200:
                    logging.info(f'Container already exists: {container_name}')
                    return True
        except urllib.error.HTTPError as e:
            if e.code == 409:
                # Container already exists - this is fine
                logging.info(f'Container already exists: {container_name}')
                return True
            else:
                logging.error(f'Failed to create container {container_name}: HTTP {e.code}')
                return False
                
        return True
        
    except Exception as e:
        logging.error(f'Error ensuring container exists ({container_name}): {str(e)}')
        return False

def upload_to_blob_storage_real(content, filename, storage_account="stbtpuksprodcrawler01", container="documents", 
                                website_id=None, website_name=None, metadata=None):
    """Upload content to Azure Blob Storage using REST API and managed identity with rich metadata
    
    Args:
        content: Binary content to upload
        filename: Filename with folder prefix (e.g., "crown-prosecution-service/abc123_doc.pdf")
        storage_account: Azure storage account name
        container: Container name (default: "documents")
        website_id: Website ID for metadata (e.g., "cps_working")
        website_name: Website display name for metadata (e.g., "Crown Prosecution Service")
        metadata: Additional custom metadata dict to attach to blob
    
    Returns:
        dict: Upload result with success status
    """
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
        elif filename.lower().endswith('.html') or filename.lower().endswith('.htm'):
            req.add_header("Content-Type", "text/html; charset=utf-8")
        else:
            req.add_header("Content-Type", "application/octet-stream")
        
        # Add rich blob metadata for AI search and filtering
        # Metadata keys must be lowercase and valid HTTP header names
        if website_id:
            req.add_header("x-ms-meta-websiteid", website_id)
        if website_name:
            # URL-encode website name for header safety
            safe_name = urllib.parse.quote(website_name)
            req.add_header("x-ms-meta-websitename", safe_name)
        
        # Add crawl timestamp
        req.add_header("x-ms-meta-crawldate", datetime.now(timezone.utc).isoformat())
        
        # Add custom metadata if provided
        if metadata:
            for key, value in metadata.items():
                # Sanitize key and value for HTTP headers
                safe_key = re.sub(r'[^a-z0-9]', '', key.lower())
                safe_value = urllib.parse.quote(str(value))
                req.add_header(f"x-ms-meta-{safe_key}", safe_value)
        
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

def is_guidance_page(url, min_depth=2):
    """Determine if URL is likely a guidance content page (not navigation/listing)
    
    Used for College of Policing APP guidance which is web-based, not downloadable files.
    
    Args:
        url: URL to check
        min_depth: Minimum path depth (default 2 = /app/category/topic)
        
    Returns:
        bool: True if likely a guidance page
    """
    # College of Policing APP guidance patterns
    app_guidance_patterns = [
        r'/app/[^/]+/[^/]+',  # /app/category/topic (e.g., /app/armed-policing/legal-framework)
        r'/app/[^/]+/[^/]+/[^/]+',  # /app/category/topic/subtopic
    ]
    
    # Exclude navigation/listing pages
    navigation_indicators = [
        '/app/search',
        '/app/categories',
        '/app/?$',  # Just /app or /app/
        '/app$',
    ]
    
    # Check if it's a navigation page (exclude these)
    for pattern in navigation_indicators:
        if re.search(pattern, url, re.IGNORECASE):
            return False
    
    # Check path depth
    parsed = urllib.parse.urlparse(url)
    path_parts = [p for p in parsed.path.split('/') if p]
    
    # For College of Policing: need at least /app/category/topic (3 parts minimum)
    if min_depth >= 2 and len(path_parts) < 3:
        return False
    
    # Check if it matches guidance patterns
    for pattern in app_guidance_patterns:
        if re.search(pattern, url, re.IGNORECASE):
            return True
    
    return False

def capture_html_guidance(url, site_name="Unknown"):
    """Capture HTML content from guidance pages
    
    Used for sites like College of Policing where guidance is web-based, not downloadable.
    Extracts main content and saves as HTML document.
    
    Args:
        url: URL of guidance page
        site_name: Name of source website
        
    Returns:
        dict: Result with success status, content, metadata
    """
    try:
        # Enhanced headers to avoid bot detection - full browser simulation
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-GB,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Sec-Ch-Ua': '"Google Chrome";v="119", "Chromium";v="119", "Not?A_Brand";v="24"',
            'Sec-Ch-Ua-Mobile': '?0',
            'Sec-Ch-Ua-Platform': '"Windows"',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0',
            'Connection': 'keep-alive'
        }
        
        req = urllib.request.Request(url, headers=headers)
        
        with urllib.request.urlopen(req, timeout=30) as response:
            raw_content = response.read()
            
            # Handle gzip encoding
            if response.info().get('Content-Encoding') == 'gzip':
                html_content = gzip.decompress(raw_content).decode('utf-8')
            else:
                html_content = raw_content.decode('utf-8')
        
        # Extract main content
        extractor = HTMLContentExtractor()
        extractor.feed(html_content)
        
        # Check if page has substantial content
        content_length = sum(len(text) for text in extractor.content_text)
        if not extractor.has_substantial_content():
            logging.warning(f'Skipping {url}: Only {content_length} chars extracted (threshold: 200)')
            return {
                "success": False,
                "error": f"Page does not contain substantial guidance content ({content_length} chars, need 200+)"
            }
        
        # Get extracted text content
        text_content = extractor.get_content()
        logging.info(f'Successfully extracted {len(text_content)} chars from {url}')
        
        # Create HTML document with metadata
        html_document = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="source" content="{site_name}">
    <meta name="source-url" content="{url}">
    <meta name="captured-date" content="{datetime.now(timezone.utc).isoformat()}">
    <title>Guidance from {site_name}</title>
</head>
<body>
    <div class="guidance-content">
        <h1>Source: {site_name}</h1>
        <p><strong>URL:</strong> <a href="{url}">{url}</a></p>
        <p><strong>Captured:</strong> {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
        <hr>
        <div class="content">
            {text_content.replace(chr(10), '<br>' + chr(10))}
        </div>
    </div>
</body>
</html>"""
        
        # Convert to bytes for consistent handling with binary documents
        content_bytes = html_document.encode('utf-8')
        
        # Generate filename from URL
        # Extract meaningful name from URL path
        url_path = urllib.parse.urlparse(url).path
        path_parts = [p for p in url_path.split('/') if p]
        if path_parts:
            filename_base = '-'.join(path_parts[-2:]) if len(path_parts) >= 2 else path_parts[-1]
        else:
            filename_base = 'guidance'
        
        # Sanitize and add extension
        filename_base = re.sub(r'[^a-zA-Z0-9-]', '_', filename_base)[:100]
        filename = f"{filename_base}.html"
        
        return {
            "success": True,
            "content": content_bytes,
            "content_type": "text/html",
            "size": len(content_bytes),
            "filename": filename,
            "text_length": len(text_content)
        }
        
    except Exception as e:
        logging.error(f'HTML guidance capture failed for {url}: {str(e)}')
        return {"success": False, "error": str(e)}

def calculate_content_hash(content):
    """Calculate MD5 hash of content for change detection"""
    return hashlib.md5(content).hexdigest()

def get_document_hashes_from_storage(storage_account="stbtpuksprodcrawler01", container="crawl-metadata"):
    """Retrieve stored document hashes from Azure Storage for change detection - using crawl-metadata container"""
    try:
        access_token = get_managed_identity_token()
        if not access_token:
            logging.error('Failed to get access token for hash retrieval')
            return {}
            
        filename = "document-hashes.json"
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

def load_websites_config():
    """Load website configurations from websites.json file
    
    Returns:
        dict: Configuration data with version, description, and websites list
    """
    try:
        # Determine config location (local or Azure)
        config_location = os.environ.get('WEBSITES_CONFIG_LOCATION', 'local')
        
        if config_location == 'local':
            # Read from local file system
            config_path = os.path.join(os.path.dirname(__file__), 'websites.json')
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            logging.info(f'Loaded website config from local file: {config_path}')
        else:
            # Future: Load from Azure Storage or other sources
            logging.warning('Azure storage config loading not yet implemented, falling back to local')
            config_path = os.path.join(os.path.dirname(__file__), 'websites.json')
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
        
        return config_data
        
    except FileNotFoundError:
        logging.error('websites.json file not found, returning empty configuration')
        return {"version": "0.0.0", "websites": []}
    except json.JSONDecodeError as e:
        logging.error(f'Invalid JSON in websites.json: {str(e)}')
        return {"version": "0.0.0", "websites": []}
    except Exception as e:
        logging.error(f'Error loading website configuration: {str(e)}')
        return {"version": "0.0.0", "websites": []}

def get_enabled_websites():
    """Get list of enabled websites from configuration
    
    Returns:
        list: List of enabled website configurations
    """
    config_data = load_websites_config()
    enabled_sites = [site for site in config_data.get('websites', []) if site.get('enabled', False)]
    logging.info(f'Found {len(enabled_sites)} enabled websites from config version {config_data.get("version", "unknown")}')
    return enabled_sites

def get_enabled_websites_legacy():
    """DEPRECATED - Legacy hardcoded configuration (kept for reference)
    Use load_websites_config() and get_enabled_websites() instead
    """
    website_configs = {
        "college_of_policing": {
            "name": "College of Policing - App Portal",
            "url": "https://www.college.police.uk/app",
            "enabled": True,
            "description": "College of Policing app portal - trying /app path to bypass bot protection",
            "document_types": ["pdf", "doc", "docx", "xml"],
            "crawl_depth": "deep",
            "priority": "high"
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
        "npcc_publications": {
            "name": "NPCC Publications - All Publications",
            "url": "https://www.npcc.police.uk/publications/All-publications/",
            "enabled": True,
            "description": "NPCC All Publications page - comprehensive publication database",
            "document_types": ["pdf", "doc", "docx", "xml"],
            "crawl_depth": "deep",
            "priority": "high",
            "multi_level": True,
            "max_depth": 2
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

def crawl_website_core(site_config, previous_hashes=None):
    """Core website crawling logic extracted for reusability
    
    Args:
        site_config (dict): Website configuration with url, name, multi_level settings
        previous_hashes (dict): Previously stored document hashes for change detection
    
    Returns:
        dict: Crawl results including documents found, processed, new, changed, uploaded
    """
    site_url = site_config["url"]
    site_name = site_config["name"]
    
    result = {
        "site_name": site_name,
        "site_url": site_url,
        "status": "unknown",
        "documents_found": 0,
        "documents_processed": 0,
        "documents_new": 0,
        "documents_changed": 0,
        "documents_unchanged": 0,
        "documents_uploaded": 0,
        "current_hashes": {},
        "error": None
    }
    
    try:
        logging.info(f'Crawling site: {site_name} ({site_url})')
        
        # Ensure website folder exists in storage (automatic folder creation)
        ensure_website_folder_exists(site_name)
        
        # Advanced headers with Chrome security context
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
                # Handle gzipped responses
                raw_content = response.read()
                if response.info().get('Content-Encoding') == 'gzip':
                    content = gzip.decompress(raw_content).decode('utf-8')
                else:
                    content = raw_content.decode('utf-8')
                
                parse_result = find_documents_in_html(content, site_url)
                
        except urllib.error.HTTPError as e:
            if e.code == 403:
                logging.warning(f'Site {site_name} blocked (403) - anti-bot protection')
                result["status"] = "blocked"
                result["error"] = "HTTP 403 - Anti-bot protection"
                return result
            else:
                raise
        
        all_documents = parse_result["documents"]
        logging.info(f'Found {len(all_documents)} Level 1 documents on {site_name}')
        
        # HTML Guidance Capture Mode (for College of Policing APP and similar sites)
        # If enabled, capture web-based guidance pages as HTML documents
        if site_config.get("capture_html_guidance", False):
            logging.info(f'HTML guidance capture enabled for {site_name} - will discover and capture web-based guidance pages')
            
            # Parse the main page to find all relevant links
            parser = EnhancedDocumentLinkParser()
            parser.feed(content)
            
            # Get minimum depth requirement
            min_depth = site_config.get("guidance_min_depth", 2)
            
            # First, discover category pages (Level 1)
            category_pages = []
            for link in parser.all_links:
                # Convert to absolute URL
                if link.startswith(('http://', 'https://')):
                    full_url = link
                elif link.startswith('/'):
                    base = urllib.parse.urlparse(site_url)
                    full_url = f"{base.scheme}://{base.netloc}{link}"
                else:
                    full_url = urllib.parse.urljoin(site_url, link)
                
                # Check if it's a category page (1 level deep: /app/category)
                parsed = urllib.parse.urlparse(full_url)
                path_parts = [p for p in parsed.path.split('/') if p]
                if len(path_parts) == 2 and '/app/' in full_url.lower():
                    category_pages.append(full_url)
            
            logging.info(f'Found {len(category_pages)} category pages on {site_name}')
            
            # Now crawl each category page to find guidance pages (Level 2)
            guidance_pages = []
            max_categories = min(20, len(category_pages))  # Limit categories for safety
            logging.info(f'Will crawl {max_categories} category pages to find guidance')
            
            import time
            for i, category_url in enumerate(category_pages[:max_categories]):
                try:
                    logging.info(f'Crawling category {i+1}/{max_categories}: {category_url}')
                    
                    # Download category page with full browser headers
                    headers = {
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0',
                        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                        'Accept-Language': 'en-GB,en;q=0.9',
                        'Accept-Encoding': 'gzip, deflate, br',
                        'Sec-Ch-Ua': '"Google Chrome";v="119", "Chromium";v="119", "Not?A_Brand";v="24"',
                        'Sec-Ch-Ua-Mobile': '?0',
                        'Sec-Ch-Ua-Platform': '"Windows"',
                        'Sec-Fetch-Dest': 'document',
                        'Sec-Fetch-Mode': 'navigate',
                        'Sec-Fetch-Site': 'none',
                        'Sec-Fetch-User': '?1',
                        'Upgrade-Insecure-Requests': '1',
                        'Cache-Control': 'max-age=0',
                        'Connection': 'keep-alive'
                    }
                    req = urllib.request.Request(category_url, headers=headers)
                    with urllib.request.urlopen(req, timeout=15) as response:
                        raw_cat = response.read()
                        if response.info().get('Content-Encoding') == 'gzip':
                            cat_content = gzip.decompress(raw_cat).decode('utf-8')
                        else:
                            cat_content = raw_cat.decode('utf-8')
                    
                    # Parse category page for guidance links
                    cat_parser = EnhancedDocumentLinkParser()
                    cat_parser.feed(cat_content)
                    
                    for link in cat_parser.all_links:
                        # Convert to absolute URL
                        if link.startswith(('http://', 'https://')):
                            guidance_url = link
                        elif link.startswith('/'):
                            base = urllib.parse.urlparse(site_url)
                            guidance_url = f"{base.scheme}://{base.netloc}{link}"
                        else:
                            guidance_url = urllib.parse.urljoin(category_url, link)
                        
                        # Check if it's a guidance page using updated function
                        if is_guidance_page(guidance_url, min_depth=min_depth):
                            guidance_pages.append({
                                "url": guidance_url,
                                "filename": guidance_url.split('/')[-1] or "guidance",
                                "type": "html_guidance",
                                "extension": "html"
                            })
                    
                    # Be respectful - add delay
                    time.sleep(1)
                    
                except urllib.error.HTTPError as e:
                    if e.code == 403:
                        logging.error(f'❌ Category page BLOCKED (403): {category_url} - bot detection active')
                    else:
                        logging.warning(f'HTTP error {e.code} crawling category page {category_url}: {str(e)}')
                    continue
                except Exception as e:
                    logging.warning(f'Failed to crawl category page {category_url}: {str(e)}')
                    continue
            
            # Remove duplicates
            seen_urls = set()
            unique_guidance = []
            for page in guidance_pages:
                if page["url"] not in seen_urls:
                    seen_urls.add(page["url"])
                    unique_guidance.append(page)
            
            logging.info(f'Found {len(unique_guidance)} unique guidance pages to capture for {site_name}')
            
            # Limit to reasonable number
            max_guidance_pages = site_config.get("max_guidance_pages", 50)
            if len(unique_guidance) > max_guidance_pages:
                logging.info(f'Limiting to first {max_guidance_pages} guidance pages')
                unique_guidance = unique_guidance[:max_guidance_pages]
            
            # Add guidance pages to documents list
            all_documents.extend(unique_guidance)
            logging.info(f'Total items to process: {len(all_documents)} (includes {len(unique_guidance)} HTML guidance pages)')
        
        # Multi-level crawling if enabled (for traditional document discovery)
        elif site_config.get("multi_level", False) and site_config.get("max_depth", 1) > 1:
            max_depth = site_config.get("max_depth", 2)
            logging.info(f'Starting multi-level crawl for {site_name} (max depth: {max_depth})')
            
            level1_count = len(all_documents)
            sub_documents_found = 0
            
            # Crawl Level 1 documents for sub-documents (limit to first 100 for safety)
            max_level1_to_crawl = min(100, len(all_documents))
            logging.info(f'Will crawl {max_level1_to_crawl} Level 1 documents for sub-documents')
            
            for level1_doc in all_documents[:max_level1_to_crawl]:
                try:
                    sub_docs = crawl_document_page_for_sub_documents(
                        level1_doc["url"],
                        site_url,
                        max_depth=max_depth,
                        current_depth=1
                    )
                    all_documents.extend(sub_docs)
                    sub_documents_found += len(sub_docs)
                    
                    # Be respectful - add delay
                    import time
                    time.sleep(1)
                    
                except Exception as e:
                    logging.warning(f'Failed to crawl sub-docs for {level1_doc["url"]}: {str(e)}')
                    continue
            
            logging.info(f'Multi-level crawl complete - {level1_count} Level 1 + {sub_documents_found} Level 2+ = {len(all_documents)} total')
        
        result["documents_found"] = len(all_documents)
        
        if not all_documents:
            result["status"] = "no_documents"
            return result
        
        # Use provided hashes or get from storage
        if previous_hashes is None:
            previous_hashes = get_document_hashes_from_storage()
        
        current_hashes = {}
        
        # Phase 2: Collision detection tracking
        filenames_generated = []
        collision_count = 0
        
        # Filter out non-document files (unknown extensions are likely HTML pages, not documents)
        # BUT: Keep html_guidance type for sites with capture_html_guidance enabled
        if site_config.get("capture_html_guidance", False):
            # Keep all documents including HTML guidance
            actual_documents = [doc for doc in all_documents if doc.get("extension") != "unknown" or doc.get("type") == "html_guidance"]
            skipped_count = len(all_documents) - len(actual_documents)
            html_guidance_count = len([doc for doc in actual_documents if doc.get("type") == "html_guidance"])
            logging.info(f'Processing {len(actual_documents)} items (including {html_guidance_count} HTML guidance pages)')
        else:
            # Standard filtering - exclude unknown extensions
            actual_documents = [doc for doc in all_documents if doc.get("extension") != "unknown"]
            skipped_count = len(all_documents) - len(actual_documents)
            
            if skipped_count > 0:
                logging.info(f'Filtered out {skipped_count} non-document links (unknown extension - likely HTML pages)')
                logging.info(f'Processing {len(actual_documents)} actual document files')
        
        # Process documents with change detection
        for i, doc in enumerate(actual_documents):
            try:
                logging.info(f'Processing document {i+1}/{len(actual_documents)} - {doc["filename"]} ({doc.get("extension")})')
                
                # Check if this is an HTML guidance page that needs special handling
                if doc.get("type") == "html_guidance":
                    logging.info(f'Capturing HTML guidance from: {doc["url"]}')
                    download_result = capture_html_guidance(doc["url"], site_name)
                    
                    # If capture failed, skip this document
                    if not download_result["success"]:
                        logging.warning(f'Skipping {doc["url"]}: {download_result.get("error")}')
                        continue
                    
                    # Use the generated filename from capture_html_guidance
                    doc["filename"] = download_result["filename"]
                    logging.info(f'Captured {download_result["text_length"]} chars of guidance content')
                else:
                    # Standard document download
                    download_result = download_document(doc["url"])
                
                if download_result["success"]:
                    current_hash = calculate_content_hash(download_result["content"])
                    
                    # Generate unique filename to prevent collisions
                    unique_filename = generate_unique_filename(
                        doc["url"],
                        doc["filename"],
                        site_name
                    )
                    
                    # Phase 2: Detect filename collisions
                    if unique_filename in filenames_generated:
                        collision_count += 1
                        logging.error(f'⚠️  COLLISION DETECTED: {unique_filename} generated twice!')
                        logging.error(f'   URL1: {[k for k, v in current_hashes.items() if v.get("unique_filename") == unique_filename]}')
                        logging.error(f'   URL2: {doc["url"]}')
                        # Add collision suffix to prevent overwrite
                        base, ext = unique_filename.rsplit('.', 1) if '.' in unique_filename else (unique_filename, 'pdf')
                        unique_filename = f"{base}_collision_{collision_count}.{ext}"
                        logging.info(f'   → Renamed to: {unique_filename}')
                    
                    filenames_generated.append(unique_filename)
                    
                    current_hashes[doc["url"]] = {
                        "filename": doc["filename"],
                        "unique_filename": unique_filename,
                        "hash": current_hash,
                        "last_seen": datetime.now(timezone.utc).isoformat()
                    }
                    
                    # Determine document status
                    previous_hash = previous_hashes.get(doc["url"], {}).get("hash")
                    
                    if previous_hash is None:
                        status = "new"
                        result["documents_new"] += 1
                        should_upload = True
                    elif previous_hash != current_hash:
                        status = "changed"
                        result["documents_changed"] += 1
                        should_upload = True
                    else:
                        status = "unchanged"
                        result["documents_unchanged"] += 1
                        should_upload = False
                    
                    result["documents_processed"] += 1
                    
                    # Upload if new or changed
                    if should_upload:
                        # Prepare metadata for AI search and filtering
                        blob_metadata = {
                            "documenttype": doc.get("type", "unknown"),
                            "originalfilename": doc["filename"],
                            "status": status,
                            "documenturl": doc["url"]
                        }
                        
                        storage_result = upload_to_blob_storage_real(
                            content=download_result["content"],
                            filename=unique_filename,  # Includes folder prefix
                            website_id=site_config.get("id"),
                            website_name=site_name,
                            metadata=blob_metadata
                        )
                        if storage_result["success"]:
                            result["documents_uploaded"] += 1
                            logging.info(f'✅ Uploaded {unique_filename} (original: {doc["filename"]}) - Status: {status}')
                        else:
                            logging.error(f'❌ Upload failed for {doc["filename"]} - {storage_result.get("error", "Unknown")}')
                    else:
                        logging.info(f'⏭️  Skipped upload for {doc["filename"]} - Status: {status}')
                        
                else:
                    logging.error(f'Download failed for {doc["filename"]} - {download_result["error"]}')
                    
            except Exception as doc_error:
                logging.error(f'Error processing document {doc["filename"]}: {str(doc_error)}')
        
        result["current_hashes"] = current_hashes
        result["collision_count"] = collision_count  # Phase 2: Track collisions
        result["status"] = "success"
        
        # Phase 2: Log collision summary
        if collision_count > 0:
            logging.warning(f'⚠️  {site_name}: {collision_count} filename collision(s) detected and resolved')
        else:
            logging.info(f'✅ {site_name}: Zero collisions - all filenames unique')
        
    except Exception as site_error:
        logging.error(f'Error crawling site {site_name}: {str(site_error)}')
        result["status"] = "error"
        result["error"] = str(site_error)
    
    return result

def validate_storage_consistency(uploaded_count, storage_account="stbtpuksprodcrawler01", container="documents"):
    """Phase 2: Validate that storage count matches uploaded count
    
    Args:
        uploaded_count: Number of documents uploaded in this crawl
        storage_account: Azure storage account name
        container: Container name
    
    Returns:
        dict: Validation results with match status and metrics
    """
    try:
        logging.info(f'📊 Phase 2: Validating storage consistency...')
        
        # Get actual storage count
        storage_stats = get_storage_statistics(storage_account, container)
        actual_count = storage_stats.get("total_documents", 0)
        
        # Calculate validation metrics
        validation_result = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "uploaded_count": uploaded_count,
            "storage_count": actual_count,
            "match": uploaded_count == actual_count,
            "discrepancy": abs(uploaded_count - actual_count),
            "accuracy_percent": round((actual_count / uploaded_count * 100) if uploaded_count > 0 else 100, 2)
        }
        
        # Log results
        if validation_result["match"]:
            logging.info(f'✅ Storage validated: {actual_count} documents match upload count (100%)')
        else:
            logging.warning(f'⚠️  Storage mismatch: {uploaded_count} uploaded but {actual_count} in storage')
            logging.warning(f'   Discrepancy: {validation_result["discrepancy"]} documents')
            logging.warning(f'   Accuracy: {validation_result["accuracy_percent"]}%')
        
        return validation_result
        
    except Exception as e:
        logging.error(f'❌ Storage validation failed: {str(e)}')
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "error": str(e),
            "match": False
        }

def store_document_hashes_to_storage(hash_data, storage_account="stbtpuksprodcrawler01", container="crawl-metadata"):
    """Store document hashes to Azure Storage for change detection - using crawl-metadata container"""
    try:
        access_token = get_managed_identity_token()
        if not access_token:
            logging.error('Failed to get access token for hash storage')
            return False
            
        filename = "document-hashes.json"
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

def delete_uncategorized_documents(storage_account="stbtpuksprodcrawler01", container="documents", dry_run=True):
    """Delete documents that don't have a folder prefix (uncategorized documents)
    
    Args:
        storage_account: Azure storage account name
        container: Container name
        dry_run: If True, only list files to be deleted without actually deleting
    
    Returns:
        dict: Results with list of deleted/would-be-deleted files and counts
    """
    try:
        access_token = get_managed_identity_token()
        if not access_token:
            logging.error('Failed to get access token for cleanup')
            return {"error": "Authentication failed"}
        
        # List all blobs in the container
        list_url = f"https://{storage_account}.blob.core.windows.net/{container}?restype=container&comp=list"
        
        req = urllib.request.Request(list_url, method='GET')
        req.add_header('Authorization', f'Bearer {access_token}')
        req.add_header('x-ms-version', '2021-06-08')
        
        with urllib.request.urlopen(req, timeout=30) as response:
            xml_data = response.read().decode('utf-8')
        
        # Parse XML response
        import xml.etree.ElementTree as ET
        root = ET.fromstring(xml_data)
        
        uncategorized_files = []
        system_files = ['document_hashes.json', 'crawl_history.json']
        
        # Find all blobs without folder prefix
        for blob in root.findall('.//Blob'):
            name_elem = blob.find('Name')
            if name_elem is not None:
                name = name_elem.text or ""
                
                # Skip system files and folder placeholders
                if name in system_files or name.endswith('/.folder'):
                    continue
                
                # Check if document has no folder prefix
                if '/' not in name:
                    size_elem = blob.find('Properties/Content-Length')
                    size = int(size_elem.text) if size_elem is not None and size_elem.text else 0
                    uncategorized_files.append({
                        "name": name,
                        "size": size,
                        "size_mb": round(size / (1024 * 1024), 2)
                    })
        
        if not uncategorized_files:
            return {
                "message": "No uncategorized documents found",
                "count": 0,
                "files": [],
                "dry_run": dry_run
            }
        
        deleted_files = []
        failed_deletions = []
        
        if dry_run:
            # Just return the list of files that would be deleted
            logging.info(f'DRY RUN: Would delete {len(uncategorized_files)} uncategorized documents')
            return {
                "message": f"DRY RUN: Found {len(uncategorized_files)} uncategorized documents",
                "count": len(uncategorized_files),
                "total_size_mb": round(sum(f["size"] for f in uncategorized_files) / (1024 * 1024), 2),
                "files": uncategorized_files,
                "dry_run": True,
                "note": "Set dry_run=false to actually delete these files"
            }
        
        # Actually delete the files
        for file_info in uncategorized_files:
            try:
                blob_url = f"https://{storage_account}.blob.core.windows.net/{container}/{file_info['name']}"
                
                del_req = urllib.request.Request(blob_url, method='DELETE')
                del_req.add_header('Authorization', f'Bearer {access_token}')
                del_req.add_header('x-ms-version', '2021-06-08')
                
                with urllib.request.urlopen(del_req, timeout=30) as response:
                    if response.status == 202:
                        deleted_files.append(file_info)
                        logging.info(f'✅ Deleted uncategorized file: {file_info["name"]}')
                    else:
                        failed_deletions.append({
                            "file": file_info["name"],
                            "reason": f"HTTP {response.status}"
                        })
                        logging.warning(f'⚠️ Failed to delete {file_info["name"]}: HTTP {response.status}')
                        
            except Exception as del_error:
                failed_deletions.append({
                    "file": file_info["name"],
                    "reason": str(del_error)
                })
                logging.error(f'❌ Error deleting {file_info["name"]}: {str(del_error)}')
        
        return {
            "message": f"Deleted {len(deleted_files)} uncategorized documents",
            "deleted_count": len(deleted_files),
            "failed_count": len(failed_deletions),
            "total_size_mb": round(sum(f["size"] for f in deleted_files) / (1024 * 1024), 2),
            "deleted_files": deleted_files,
            "failed_deletions": failed_deletions,
            "dry_run": False,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logging.error(f'Error in cleanup operation: {str(e)}')
        return {"error": str(e)}

def get_storage_statistics(storage_account="stbtpuksprodcrawler01", container="documents"):
    """Analyze Azure Storage to get document statistics per website"""
    try:
        access_token = get_managed_identity_token()
        if not access_token:
            logging.error('Failed to get access token for storage analysis')
            return {"error": "Authentication failed"}
            
        # List all blobs in the container
        url = f"https://{storage_account}.blob.core.windows.net/{container}?restype=container&comp=list&maxresults=1000"
        
        req = urllib.request.Request(url, method='GET')
        req.add_header('Authorization', f'Bearer {access_token}')
        req.add_header('x-ms-version', '2020-04-08')
        
        with urllib.request.urlopen(req, timeout=30) as response:
            xml_content = response.read().decode('utf-8')
            
        # Parse XML to extract blob information
        import xml.etree.ElementTree as ET
        try:
            root = ET.fromstring(xml_content)
        except ET.ParseError as e:
            logging.error(f'XML parsing error: {str(e)}')
            return {"error": f"XML parsing failed: {str(e)}"}
        
        blobs = []
        total_size = 0
        
        for blob in root.findall('.//Blob'):
            try:
                name_elem = blob.find('Name')
                size_elem = blob.find('Properties/Content-Length')
                modified_elem = blob.find('Properties/Last-Modified')
                
                if name_elem is not None and size_elem is not None:
                    name = name_elem.text or ""
                    size = int(size_elem.text) if size_elem.text and size_elem.text.isdigit() else 0
                    modified = modified_elem.text if modified_elem is not None else None
                    
                    # Skip system files and folder placeholders
                    if name and name not in ['document_hashes.json', 'crawl_history.json'] and not name.endswith('/.folder'):
                        blobs.append({
                            "name": name,
                            "size": size,
                            "last_modified": modified
                        })
                        total_size += size
            except Exception as blob_error:
                logging.warning(f'Error processing blob: {str(blob_error)}')
                continue
        
        # Categorize documents by site (based on folder prefix in filename)
        # The generate_unique_filename function creates files like: "site-name/hash_filename.ext"
        site_stats = {}
        
        # Load website configurations to build dynamic mapping
        websites_data = load_websites_config()
        site_display_names = {}
        
        if "error" not in websites_data:
            # websites_data["websites"] is a list, not a dict
            for website_config in websites_data.get("websites", []):
                # Generate folder name same way as generate_unique_filename
                folder_name = get_folder_name_for_website(website_config["name"])
                site_display_names[folder_name] = website_config["name"]
        
        for blob in blobs:
            # Extract the site folder prefix (before the first '/')
            if '/' in blob["name"]:
                site_folder = blob["name"].split('/')[0].lower()
                # Get display name from mapping or use prettified folder name
                display_name = site_display_names.get(site_folder, site_folder.replace('-', ' ').title())
            else:
                # Documents without folder prefix - log for investigation
                logging.warning(f'⚠️  Document without folder prefix found: {blob["name"]}')
                site_folder = "uncategorized"
                display_name = "Uncategorized (Legacy)"
            
            # Initialize site stats if not exists
            if display_name not in site_stats:
                site_stats[display_name] = {"count": 0, "size": 0, "files": [], "folder": site_folder}
            
            # Add blob to site stats
            site_stats[display_name]["count"] += 1
            site_stats[display_name]["size"] += blob["size"]
            site_stats[display_name]["files"].append(blob)
        
        return {
            "total_documents": len(blobs),
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "site_breakdown": site_stats,
            "container": container,
            "storage_account": storage_account
        }
        
    except Exception as e:
        logging.error(f'Storage statistics error: {str(e)}')
        return {"error": str(e)}

def store_crawl_history(crawl_data, storage_account="stbtpuksprodcrawler01", container="documents"):
    """Store crawl history to Azure Storage"""
    try:
        # Get existing history
        history = get_crawl_history(storage_account, container)
        
        # Add new entry
        crawl_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "sites_processed": crawl_data.get("sites_processed", 0),
            "documents_found": crawl_data.get("documents_found", 0),
            "documents_new": crawl_data.get("documents_new", 0),
            "documents_changed": crawl_data.get("documents_changed", 0),
            "documents_unchanged": crawl_data.get("documents_unchanged", 0),
            "documents_uploaded": crawl_data.get("documents_uploaded", 0),
            "trigger_type": crawl_data.get("trigger_type", "manual")
        }
        
        history.append(crawl_entry)
        
        # Keep only last 50 entries
        if len(history) > 50:
            history = history[-50:]
        
        # Store back to Azure
        access_token = get_managed_identity_token()
        if not access_token:
            logging.error('Failed to get access token for crawl history storage')
            return False
            
        filename = "crawl_history.json"
        content = json.dumps(history, indent=2).encode('utf-8')
        
        url = f"https://{storage_account}.blob.core.windows.net/{container}/{filename}"
        
        req = urllib.request.Request(url, data=content, method='PUT')
        req.add_header('Authorization', f'Bearer {access_token}')
        req.add_header('x-ms-version', '2020-04-08')
        req.add_header('x-ms-blob-type', 'BlockBlob')
        req.add_header('Content-Type', 'application/json')
        req.add_header('Content-Length', str(len(content)))
        
        with urllib.request.urlopen(req, timeout=30) as response:
            return response.status == 201
            
    except Exception as e:
        logging.error(f'Error storing crawl history: {str(e)}')
        return False

def get_crawl_history(storage_account="stbtpuksprodcrawler01", container="documents"):
    """Retrieve crawl history from Azure Storage"""
    try:
        access_token = get_managed_identity_token()
        if not access_token:
            logging.error('Failed to get access token for crawl history retrieval')
            return []
            
        filename = "crawl_history.json"
        url = f"https://{storage_account}.blob.core.windows.net/{container}/{filename}"
        
        req = urllib.request.Request(url, method='GET')
        req.add_header('Authorization', f'Bearer {access_token}')
        req.add_header('x-ms-version', '2020-04-08')
        
        with urllib.request.urlopen(req, timeout=30) as response:
            history_data = json.loads(response.read().decode())
            return history_data
            
    except urllib.error.HTTPError as e:
        if e.code == 404:
            logging.info('No crawl history file found - returning empty history')
            return []
        else:
            logging.error(f'HTTP error retrieving crawl history: {e.code} {e.reason}')
            return []
    except Exception as e:
        logging.error(f'Error retrieving crawl history: {str(e)}')
        return []

# ============================================================================
# MAIN FUNCTION APP - Initialize BEFORE function definitions
# ============================================================================

# Use DFApp as the main app - it extends FunctionApp and supports both regular and durable functions
app = df.DFApp(http_auth_level=func.AuthLevel.ANONYMOUS)

# ============================================================================
# DURABLE FUNCTIONS - ORCHESTRATOR AND ACTIVITY FUNCTIONS
# ============================================================================

@app.orchestration_trigger(context_name="context")
def web_crawler_orchestrator(context: df.DurableOrchestrationContext):
    """
    Durable Functions Orchestrator for parallel website crawling
    
    This orchestrator:
    1. Loads website configurations
    2. Fans out to multiple activity functions (one per website)
    3. Runs crawls in parallel for maximum efficiency
    4. Aggregates results from all crawls
    5. Stores combined hashes and crawl history
    
    Returns:
        dict: Aggregated results from all website crawls
    """
    logging.info('🚀 Durable Orchestrator: Starting parallel website crawl orchestration')
    
    # Get start time from orchestration input or use current time
    orchestration_start = context.current_utc_datetime
    
    # Activity 1: Load website configurations
    logging.info('📋 Step 1: Loading website configurations')
    config_data = yield context.call_activity('get_configuration_activity')
    
    enabled_sites = [site for site in config_data.get('websites', []) if site.get('enabled', False)]
    logging.info(f'📊 Found {len(enabled_sites)} enabled websites to crawl')
    
    if not enabled_sites:
        logging.warning('⚠️ No enabled websites found in configuration')
        return {
            "success": False,
            "error": "No enabled websites found",
            "sites_processed": 0,
            "orchestration_id": context.instance_id
        }
    
    # Activity 2: Get previous hashes once (efficiency)
    logging.info('🔍 Step 2: Retrieving previous document hashes for change detection')
    previous_hashes = yield context.call_activity('get_document_hashes_activity')
    
    # Step 3: Fan-out to parallel activity functions (one per website)
    logging.info(f'🌐 Step 3: Fanning out to {len(enabled_sites)} parallel website crawl activities')
    
    crawl_tasks = []
    for site_config in enabled_sites:
        # Prepare input for each activity (includes site config and previous hashes)
        activity_input = {
            "site_config": site_config,
            "previous_hashes": previous_hashes
        }
        task = context.call_activity('crawl_single_website_activity', activity_input)
        crawl_tasks.append(task)
    
    # Wait for all parallel crawls to complete
    crawl_results = yield context.task_all(crawl_tasks)
    
    # Step 4: Aggregate results
    logging.info('📈 Step 4: Aggregating results from all website crawls')
    
    total_documents_found = 0
    total_documents_processed = 0
    total_documents_new = 0
    total_documents_changed = 0
    total_documents_unchanged = 0
    total_documents_uploaded = 0
    total_collisions = 0  # Phase 2: Track total collisions
    successful_sites = 0
    failed_sites = 0
    blocked_sites = 0
    all_current_hashes = {}
    site_summaries = []
    
    for result in crawl_results:
        total_documents_found += result.get("documents_found", 0)
        total_documents_processed += result.get("documents_processed", 0)
        total_documents_new += result.get("documents_new", 0)
        total_documents_changed += result.get("documents_changed", 0)
        total_documents_unchanged += result.get("documents_unchanged", 0)
        total_documents_uploaded += result.get("documents_uploaded", 0)
        total_collisions += result.get("collision_count", 0)  # Phase 2: Aggregate collisions
        
        # Track status
        status = result.get("status", "unknown")
        if status == "success":
            successful_sites += 1
        elif status == "blocked":
            blocked_sites += 1
        elif status == "error":
            failed_sites += 1
        
        # Merge hashes
        all_current_hashes.update(result.get("current_hashes", {}))
        
        # Track site summary
        site_summaries.append({
            "site_name": result.get("site_name"),
            "site_url": result.get("site_url"),
            "status": status,
            "documents_found": result.get("documents_found", 0),
            "documents_uploaded": result.get("documents_uploaded", 0),
            "collision_count": result.get("collision_count", 0),  # Phase 2: Include in summary
            "error": result.get("error")
        })
    
    # Activity 5: Store combined document hashes
    if all_current_hashes:
        logging.info(f'💾 Step 5: Storing {len(all_current_hashes)} combined document hashes')
        yield context.call_activity('store_document_hashes_activity', all_current_hashes)
    
    # Phase 2: Activity 5.5 - Validate storage consistency
    logging.info(f'📊 Step 5.5 (Phase 2): Validating storage consistency')
    validation_result = yield context.call_activity('validate_storage_activity', total_documents_uploaded)
    
    # Activity 6: Store crawl history
    orchestration_end = context.current_utc_datetime
    duration = (orchestration_end - orchestration_start).total_seconds()
    
    crawl_summary = {
        "orchestration_id": context.instance_id,
        "sites_total": len(enabled_sites),
        "sites_successful": successful_sites,
        "sites_failed": failed_sites,
        "sites_blocked": blocked_sites,
        "documents_found": total_documents_found,
        "documents_processed": total_documents_processed,
        "documents_new": total_documents_new,
        "documents_changed": total_documents_changed,
        "documents_unchanged": total_documents_unchanged,
        "documents_uploaded": total_documents_uploaded,
        "collision_count": total_collisions,  # Phase 2: Include collision count
        "validation": validation_result,  # Phase 2: Include validation results
        "trigger_type": "orchestrated",
        "start_time": orchestration_start.isoformat(),
        "end_time": orchestration_end.isoformat(),
        "duration_seconds": duration,
        "site_summaries": site_summaries
    }
    
    logging.info(f'📝 Step 6: Storing crawl history')
    yield context.call_activity('store_crawl_history_activity', crawl_summary)
    
    # Phase 2: Enhanced summary logging
    collision_status = f', {total_collisions} collisions' if total_collisions > 0 else ', zero collisions ✅'
    validation_status = '✅' if validation_result.get('match') else '⚠️'
    
    logging.info(f'✅ Orchestration complete: {successful_sites}/{len(enabled_sites)} sites successful, '
                f'{total_documents_uploaded} documents uploaded{collision_status} in {duration:.1f}s')
    logging.info(f'{validation_status} Storage validation: {validation_result.get("accuracy_percent", 0)}% accuracy')
    
    return crawl_summary

# Activity Functions

@app.activity_trigger(input_name="input")
def get_configuration_activity(input: None) -> dict:
    """
    Activity Function: Load website configuration from websites.json
    
    Returns:
        dict: Configuration data with websites list
    """
    logging.info('Activity: Loading website configuration')
    return load_websites_config()

@app.activity_trigger(input_name="input")
def get_document_hashes_activity(input: None) -> dict:
    """
    Activity Function: Retrieve previous document hashes from Azure Storage
    
    Returns:
        dict: Previous document hashes for change detection
    """
    logging.info('Activity: Retrieving document hashes from storage')
    return get_document_hashes_from_storage()

@app.activity_trigger(input_name="input")
def crawl_single_website_activity(input: dict) -> dict:
    """
    Activity Function: Crawl a single website
    
    Args:
        input: Dict with site_config and previous_hashes
    
    Returns:
        dict: Crawl results for this website
    """
    site_config = input["site_config"]
    previous_hashes = input["previous_hashes"]
    
    logging.info(f'Activity: Crawling website - {site_config["name"]}')
    
    # Use the refactored core crawling function
    result = crawl_website_core(site_config, previous_hashes)
    
    logging.info(f'Activity: Completed crawl for {site_config["name"]} - '
                f'Status: {result["status"]}, Documents: {result["documents_found"]}, '
                f'Uploaded: {result["documents_uploaded"]}')
    
    return result

@app.activity_trigger(input_name="input")
def store_document_hashes_activity(input: dict) -> bool:
    """
    Activity Function: Store combined document hashes to Azure Storage
    
    Args:
        input: Combined document hashes from all websites
    
    Returns:
        bool: Success status
    """
    logging.info(f'Activity: Storing {len(input)} document hashes to Azure Storage')
    return store_document_hashes_to_storage(input)

@app.activity_trigger(input_name="input")
def store_crawl_history_activity(input: dict) -> bool:
    """
    Activity Function: Store crawl history to Azure Storage
    
    Args:
        input: Crawl summary data
    
    Returns:
        bool: Success status
    """
    logging.info('Activity: Storing crawl history to Azure Storage')
    return store_crawl_history(input)

@app.activity_trigger(input_name="uploaded_count")
def validate_storage_activity(uploaded_count: int) -> dict:
    """
    Activity Function: Validate storage consistency (Phase 2 Monitoring)
    
    Compares the number of documents uploaded in this crawl to the actual
    count in blob storage to detect any issues.
    
    Args:
        uploaded_count: Number of documents uploaded during crawl
    
    Returns:
        dict: Validation results with status, counts, and accuracy
    """
    logging.info(f'Activity: Validating storage consistency ({uploaded_count} uploaded)')
    return validate_storage_consistency(uploaded_count)

# ============================================================================
# DURABLE FUNCTIONS TIMER TRIGGER
# ============================================================================

@app.timer_trigger(schedule="0 0 */4 * * *", arg_name="mytimer", run_on_startup=False, use_monitor=False)
@app.durable_client_input(client_name="client")
async def scheduled_crawler_orchestrated(mytimer: func.TimerRequest, client) -> None:
    """
    Timer trigger function that starts orchestrated crawling every 4 hours
    
    This replaces the legacy scheduled_crawler with Durable Functions orchestration
    for parallel website crawling and better resilience.
    """
    logging.info('⏰ Scheduled Timer: Starting orchestrated multi-website crawler (every 4 hours)')
    
    try:
        # Start the orchestration
        instance_id = await client.start_new('web_crawler_orchestrator', None, None)
        
        logging.info(f'✅ Scheduled crawl orchestration started with ID: {instance_id}')
        
        # Log timer info
        if mytimer.past_due:
            logging.warning('⚠️ Timer is running late!')
        
    except Exception as e:
        logging.error(f'❌ Error starting scheduled orchestration: {str(e)}')
        # Don't raise - let the next timer run try again

# ============================================================================
# LEGACY TIMER TRIGGER (Preserved for backwards compatibility)
# Use scheduled_crawler_orchestrated instead for new deployments
# ============================================================================

# Timer trigger function that runs every 4 hours
@app.timer_trigger(schedule="0 0 */4 * * *", arg_name="mytimer", run_on_startup=False,
              use_monitor=False) 
def scheduled_crawler(mytimer: func.TimerRequest) -> None:
    """Step 5a: Timer trigger function with multi-level crawling every 4 hours"""
    logging.info('Step 3b: Scheduled multi-website crawler started - 4-hour automated crawling with change detection!')
    
    # REFACTORED: Get enabled websites from configuration file
    enabled_sites = get_enabled_websites()
    logging.info(f'Step 3b: Found {len(enabled_sites)} enabled websites to process')
    
    # Initialize counters
    total_processed = 0
    total_new = 0
    total_changed = 0
    total_unchanged = 0
    total_uploaded = 0
    total_sites_processed = 0
    site_results = []
    
    # Get hashes once for all sites (efficiency improvement)
    previous_hashes = get_document_hashes_from_storage()
    all_current_hashes = {}
    
    # Process each enabled website
    for site_config in enabled_sites:
        total_sites_processed += 1
        logging.info(f'Step 4a: Processing site {total_sites_processed}/{len(enabled_sites)} - {site_config["name"]}')
        
        # REFACTORED: Use core crawling function
        crawl_result = crawl_website_core(site_config, previous_hashes)
        
        # Aggregate results
        total_processed += crawl_result["documents_processed"]
        total_new += crawl_result["documents_new"]
        total_changed += crawl_result["documents_changed"]
        total_unchanged += crawl_result["documents_unchanged"]
        total_uploaded += crawl_result["documents_uploaded"]
        
        # Merge current hashes
        all_current_hashes.update(crawl_result["current_hashes"])
        
        # Track site results
        site_results.append({
            "site_name": crawl_result["site_name"],
            "site_url": crawl_result["site_url"],
            "status": crawl_result["status"],
            "documents_found": crawl_result["documents_found"],
            "documents_processed": crawl_result["documents_processed"],
            "documents_uploaded": crawl_result["documents_uploaded"],
            "error": crawl_result.get("error")
        })
        
        logging.info(f'Site {site_config["name"]} complete - Found: {crawl_result["documents_found"]}, '
                    f'Processed: {crawl_result["documents_processed"]}, Uploaded: {crawl_result["documents_uploaded"]}')
    
    # Store all updated hashes once at the end (efficiency improvement)
    if all_current_hashes:
        store_success = store_document_hashes_to_storage(all_current_hashes)
        if store_success:
            logging.info(f'Successfully stored {len(all_current_hashes)} document hashes for all sites')
        else:
            logging.error('Failed to store document hashes')
    
    # Log comprehensive summary and store history
    crawl_summary = {
        "sites_processed": total_sites_processed,
        "documents_found": total_processed,
        "documents_new": total_new,
        "documents_changed": total_changed,
        "documents_unchanged": total_unchanged,
        "documents_uploaded": total_uploaded,
        "trigger_type": "scheduled"
    }
    
    # Store crawl history
    store_crawl_history(crawl_summary)
    
    logging.info(f'Step 3b: Multi-website scheduled crawl complete - Sites: {total_sites_processed}/{len(enabled_sites)}, Documents: {total_processed}, New: {total_new}, Changed: {total_changed}, Unchanged: {total_unchanged}, Uploaded: {total_uploaded}')

# ============================================================================
# DURABLE FUNCTIONS HTTP TRIGGERS
# ============================================================================

@app.route(route="orchestrators/web_crawler", methods=["POST"], auth_level=func.AuthLevel.ANONYMOUS)
@app.durable_client_input(client_name="client")
async def start_web_crawler_orchestration(req: func.HttpRequest, client) -> func.HttpResponse:
    """
    HTTP Trigger to start the web crawler orchestration
    
    POST /api/orchestrators/web_crawler
    
    Optional JSON body:
    {
        "force_crawl": false  // If true, crawls all sites regardless of config
    }
    
    Returns:
        Orchestration status URLs for tracking
    """
    logging.info('🚀 HTTP Trigger: Starting web crawler orchestration')
    
    try:
        # Parse request body (optional)
        request_body = {}
        try:
            request_body = req.get_json()
        except ValueError:
            pass
        
        # Start the orchestration
        instance_id = await client.start_new('web_crawler_orchestrator', None, None)
        
        logging.info(f'✅ Started orchestration with ID: {instance_id}')
        
        # Get status URLs
        response = client.create_check_status_response(req, instance_id)
        
        # Add custom response data
        response_data = {
            "orchestrationId": instance_id,
            "message": "Web crawler orchestration started successfully",
            "statusQueryGetUri": response.get_body().decode(),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        return func.HttpResponse(
            json.dumps(response_data, indent=2),
            status_code=202,
            mimetype="application/json"
        )
        
    except Exception as e:
        logging.error(f'❌ Error starting orchestration: {str(e)}')
        return func.HttpResponse(
            json.dumps({
                "error": str(e),
                "message": "Failed to start web crawler orchestration"
            }),
            status_code=500,
            mimetype="application/json"
        )

@app.route(route="orchestrators/web_crawler/{instanceId}", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
@app.durable_client_input(client_name="client")
async def get_orchestration_status(req: func.HttpRequest, client) -> func.HttpResponse:
    """
    HTTP Trigger to check orchestration status
    
    GET /api/orchestrators/web_crawler/{instanceId}
    
    Returns:
        Current orchestration status and results
    """
    instance_id = req.route_params.get('instanceId')
    
    logging.info(f'📊 HTTP Trigger: Checking orchestration status for ID: {instance_id}')
    
    try:
        status = await client.get_status(instance_id)
        
        if not status:
            return func.HttpResponse(
                json.dumps({
                    "error": "Orchestration not found",
                    "instanceId": instance_id
                }),
                status_code=404,
                mimetype="application/json"
            )
        
        # Format response
        response_data = {
            "instanceId": instance_id,
            "runtimeStatus": status.runtime_status.name if status.runtime_status else "Unknown",
            "createdTime": status.created_time.isoformat() if status.created_time else None,
            "lastUpdatedTime": status.last_updated_time.isoformat() if status.last_updated_time else None,
            "output": status.output,
            "customStatus": status.custom_status
        }
        
        # Add human-readable status
        if status.runtime_status:
            status_name = status.runtime_status.name
            if status_name == "Completed":
                response_data["message"] = "✅ Orchestration completed successfully"
            elif status_name == "Running":
                response_data["message"] = "🔄 Orchestration is currently running"
            elif status_name == "Failed":
                response_data["message"] = "❌ Orchestration failed"
            elif status_name == "Pending":
                response_data["message"] = "⏳ Orchestration is pending"
            else:
                response_data["message"] = f"Status: {status_name}"
        
        return func.HttpResponse(
            json.dumps(response_data, indent=2),
            status_code=200,
            mimetype="application/json"
        )
        
    except Exception as e:
        logging.error(f'❌ Error retrieving orchestration status: {str(e)}')
        return func.HttpResponse(
            json.dumps({
                "error": str(e),
                "message": "Failed to retrieve orchestration status",
                "instanceId": instance_id
            }),
            status_code=500,
            mimetype="application/json"
        )

@app.route(route="orchestrators/web_crawler/{instanceId}/terminate", methods=["POST"], auth_level=func.AuthLevel.ANONYMOUS)
@app.durable_client_input(client_name="client")
async def terminate_orchestration(req: func.HttpRequest, client) -> func.HttpResponse:
    """
    HTTP Trigger to terminate a running orchestration
    
    POST /api/orchestrators/web_crawler/{instanceId}/terminate
    
    Optional JSON body:
    {
        "reason": "Manual termination requested"
    }
    """
    instance_id = req.route_params.get('instanceId')
    
    logging.info(f'🛑 HTTP Trigger: Terminating orchestration ID: {instance_id}')
    
    try:
        # Parse reason from request body
        reason = "Manual termination"
        try:
            request_body = req.get_json()
            reason = request_body.get("reason", reason)
        except ValueError:
            pass
        
        # Terminate the orchestration
        await client.terminate(instance_id, reason)
        
        return func.HttpResponse(
            json.dumps({
                "message": "Orchestration terminated successfully",
                "instanceId": instance_id,
                "reason": reason,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }),
            status_code=200,
            mimetype="application/json"
        )
        
    except Exception as e:
        logging.error(f'❌ Error terminating orchestration: {str(e)}')
        return func.HttpResponse(
            json.dumps({
                "error": str(e),
                "message": "Failed to terminate orchestration",
                "instanceId": instance_id
            }),
            status_code=500,
            mimetype="application/json"
        )

# ============================================================================
# LEGACY HTTP TRIGGERS (Preserved for backwards compatibility)
# ============================================================================

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

@app.route(route="api/stats", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
def api_stats(req: func.HttpRequest) -> func.HttpResponse:
    """Comprehensive statistics API for dashboard"""
    logging.info('Statistics API called')
    
    try:
        # Get website configurations
        enabled_sites = get_enabled_websites()
        
        # Get storage statistics
        storage_stats = get_storage_statistics()
        
        # Get crawl history
        crawl_history = get_crawl_history()
        
        # Calculate recent activity (last 24 hours)
        recent_crawls = []
        if crawl_history:
            cutoff_time = datetime.now(timezone.utc) - timedelta(hours=24)
            for crawl in crawl_history:
                try:
                    crawl_time = datetime.fromisoformat(crawl["timestamp"].replace('Z', '+00:00'))
                    if crawl_time >= cutoff_time:
                        recent_crawls.append(crawl)
                except:
                    continue
        
        # Get system status
        system_status = {
            "status": "operational",
            "version": "v2.2.0",
            "uptime_check": "OK",
            "storage_accessible": storage_stats.get("error") is None,
            "last_scheduled_run": crawl_history[-1]["timestamp"] if crawl_history else "Never",
            "next_scheduled_run": "Every 4 hours"
        }
        
        # Compile comprehensive statistics
        # Phase 2: Calculate collision and validation metrics
        total_collisions_24h = sum(c.get("collision_count", 0) for c in recent_crawls)
        last_validation = crawl_history[-1].get("validation") if crawl_history else None
        
        stats = {
            "system": system_status,
            "websites": {
                "total_configured": len(enabled_sites),
                "enabled_count": len(enabled_sites),
                "sites": enabled_sites
            },
            "storage": storage_stats,
            "recent_activity": {
                "crawls_last_24h": len(recent_crawls),
                "documents_processed_24h": sum(c.get("documents_found", 0) for c in recent_crawls),
                "documents_uploaded_24h": sum(c.get("documents_uploaded", 0) for c in recent_crawls),
                "collisions_detected_24h": total_collisions_24h,  # Phase 2
                "last_crawl": crawl_history[-1] if crawl_history else None
            },
            "validation": {  # Phase 2: Storage validation metrics
                "last_check": last_validation.get("timestamp") if last_validation else "Never",
                "status": last_validation.get("status") if last_validation else "unknown",
                "uploaded_count": last_validation.get("uploaded_count") if last_validation else 0,
                "storage_count": last_validation.get("storage_count") if last_validation else 0,
                "accuracy_percentage": last_validation.get("accuracy_percentage") if last_validation else 0
            },
            "crawl_history": crawl_history[-10:],  # Last 10 crawls
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        # Ensure JSON serialization works
        try:
            json_response = json.dumps(stats, indent=2, ensure_ascii=False)
        except (TypeError, ValueError) as json_error:
            logging.error(f'JSON serialization error: {str(json_error)}')
            # Return minimal safe response
            safe_stats = {
                "system": {"status": "error", "message": "JSON serialization failed"},
                "error": str(json_error),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            json_response = json.dumps(safe_stats, indent=2)
        
        return func.HttpResponse(
            json_response,
            status_code=200,
            mimetype="application/json"
        )
        
    except Exception as e:
        logging.error(f'Statistics API error: {str(e)}')
        return func.HttpResponse(
            json.dumps({"error": str(e)}),
            status_code=500,
            mimetype="application/json"
        )

@app.route(route="dashboard", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
def dashboard(req: func.HttpRequest) -> func.HttpResponse:
    """Web Crawler Dashboard - HTML Interface"""
    logging.info('Dashboard accessed')
    
    dashboard_html = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Web Crawler Dashboard - British Transport Police</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            overflow: hidden;
        }
        
        .header {
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }
        
        .header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
        }
        
        .header p {
            font-size: 1.2em;
            opacity: 0.9;
        }
        
        .status-bar {
            background: #f8f9fa;
            padding: 15px 30px;
            border-bottom: 1px solid #dee2e6;
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
        }
        
        .status-indicator {
            display: flex;
            align-items: center;
            gap: 8px;
        }
        
        .status-dot {
            width: 12px;
            height: 12px;
            border-radius: 50%;
            background: #28a745;
            animation: pulse 2s infinite;
        }
        
        @keyframes pulse {
            0% { opacity: 1; }
            50% { opacity: 0.5; }
            100% { opacity: 1; }
        }
        
        .refresh-btn {
            background: #007bff;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 5px;
            cursor: pointer;
            font-size: 14px;
        }
        
        .refresh-btn:hover {
            background: #0056b3;
        }
        
        .dashboard-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 30px;
            padding: 30px;
        }
        
        .card {
            background: white;
            border-radius: 10px;
            padding: 25px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.08);
            border: 1px solid #e9ecef;
        }
        
        .card h3 {
            color: #2c3e50;
            margin-bottom: 20px;
            font-size: 1.3em;
            border-bottom: 2px solid #3498db;
            padding-bottom: 10px;
        }
        
        .metric {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 12px 0;
            border-bottom: 1px solid #f1f3f4;
        }
        
        .metric:last-child {
            border-bottom: none;
        }
        
        .metric-label {
            font-weight: 500;
            color: #495057;
        }
        
        .metric-value {
            font-weight: bold;
            color: #2c3e50;
            font-size: 1.1em;
        }
        
        .status-enabled {
            color: #28a745;
            font-weight: bold;
        }
        
        .status-disabled {
            color: #dc3545;
            font-weight: bold;
        }
        
        .website-item {
            background: #f8f9fa;
            border-radius: 8px;
            padding: 15px;
            margin-bottom: 15px;
            border-left: 4px solid #28a745;
        }
        
        .website-item.disabled {
            border-left-color: #dc3545;
            opacity: 0.7;
        }
        
        .website-name {
            font-weight: bold;
            color: #2c3e50;
            margin-bottom: 5px;
        }
        
        .website-url {
            color: #6c757d;
            font-size: 0.9em;
            word-break: break-all;
        }
        
        .loading {
            text-align: center;
            padding: 20px;
            color: #6c757d;
        }
        
        .error {
            background: #f8d7da;
            color: #721c24;
            padding: 15px;
            border-radius: 5px;
            margin: 10px 0;
        }
        
        .crawl-entry {
            background: #f8f9fa;
            border-radius: 8px;
            padding: 15px;
            margin-bottom: 10px;
            border-left: 4px solid #007bff;
        }
        
        .crawl-time {
            font-weight: bold;
            color: #2c3e50;
            margin-bottom: 8px;
        }
        
        .crawl-stats {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 10px;
            font-size: 0.9em;
        }
        
        .footer {
            background: #f8f9fa;
            text-align: center;
            padding: 20px;
            color: #6c757d;
            border-top: 1px solid #dee2e6;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🕷️ Web Crawler Dashboard</h1>
            <p>British Transport Police - Document Monitoring System v2.2.0</p>
        </div>
        
        <div class="status-bar">
            <div class="status-indicator">
                <div class="status-dot"></div>
                <span id="system-status">System Status: Loading...</span>
            </div>
            <div>
                <span id="last-update">Last Updated: Loading...</span>
                <button class="refresh-btn" onclick="loadDashboardData()">🔄 Refresh</button>
            </div>
        </div>
        
        <div class="dashboard-grid">
            <!-- System Overview Card -->
            <div class="card">
                <h3>📊 System Overview</h3>
                <div id="system-overview" class="loading">Loading system data...</div>
            </div>
            
            <!-- Monitored Websites Card -->
            <div class="card">
                <h3>🌐 Monitored Websites</h3>
                <div id="websites-list" class="loading">Loading websites...</div>
            </div>
            
            <!-- Document Storage Card -->
            <div class="card">
                <h3>📁 Document Storage</h3>
                <div id="storage-stats" class="loading">Loading storage data...</div>
            </div>
            
            <!-- Recent Activity Card -->
            <div class="card">
                <h3>⚡ Recent Activity</h3>
                <div id="recent-activity" class="loading">Loading activity data...</div>
            </div>
            
            <!-- Phase 2: Storage Validation Card -->
            <div class="card">
                <h3>✅ Storage Validation (Phase 2)</h3>
                <div id="validation-stats" class="loading">Loading validation data...</div>
            </div>
            
            <!-- Crawl History Card -->
            <div class="card" style="grid-column: 1 / -1;">
                <h3>📈 Recent Crawl History</h3>
                <div id="crawl-history" class="loading">Loading crawl history...</div>
            </div>
        </div>
        
        <div class="footer">
            <p>Web Crawler Dashboard - Last refreshed: <span id="refresh-time">Never</span></p>
        </div>
    </div>
    
    <script>
        function formatBytes(bytes) {
            if (bytes === 0) return '0 Bytes';
            const k = 1024;
            const sizes = ['Bytes', 'KB', 'MB', 'GB'];
            const i = Math.floor(Math.log(bytes) / Math.log(k));
            return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
        }
        
        function formatDateTime(isoString) {
            if (!isoString) return 'Never';
            try {
                return new Date(isoString).toLocaleString();
            } catch {
                return 'Invalid date';
            }
        }
        
        function loadDashboardData() {
            document.getElementById('system-status').textContent = 'System Status: Loading...';
            
            fetch('/api/api/stats')
                .then(response => {
                    if (!response.ok) {
                        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                    }
                    return response.text(); // Get as text first to debug
                })
                .then(text => {
                    try {
                        const data = JSON.parse(text);
                        updateSystemOverview(data.system);
                        updateWebsitesList(data.websites);
                        updateStorageStats(data.storage);
                        updateRecentActivity(data.recent_activity);
                        updateValidationStats(data.validation, data.recent_activity);  // Phase 2
                        updateCrawlHistory(data.crawl_history);
                        
                        document.getElementById('system-status').textContent = 'System Status: ' + data.system.status.toUpperCase();
                        document.getElementById('last-update').textContent = 'Last Updated: ' + formatDateTime(data.timestamp);
                        document.getElementById('refresh-time').textContent = new Date().toLocaleString();
                    } catch (parseError) {
                        console.error('JSON Parse Error:', parseError);
                        console.log('Response text length:', text.length);
                        console.log('Response start:', text.substring(0, 200));
                        console.log('Response end:', text.substring(text.length - 200));
                        throw new Error(`JSON parsing failed: ${parseError.message}`);
                    }
                })
                .catch(error => {
                    console.error('Error loading dashboard data:', error);
                    document.getElementById('system-status').textContent = 'System Status: ERROR';
                    showError('Failed to load dashboard data: ' + error.message);
                    
                    // Try fallback to basic status
                    loadFallbackData();
                });
        }
        
        function loadFallbackData() {
            fetch('/api/status')
                .then(response => response.json())
                .then(data => {
                    document.getElementById('system-overview').innerHTML = `
                        <div class="metric">
                            <span class="metric-label">Status (Fallback Mode)</span>
                            <span class="metric-value status-enabled">${data.status}</span>
                        </div>
                        <div class="metric">
                            <span class="metric-label">Version</span>
                            <span class="metric-value">${data.version}</span>
                        </div>
                        <div class="metric">
                            <span class="metric-label">Storage Account</span>
                            <span class="metric-value">${data.storage_account}</span>
                        </div>
                    `;
                    document.getElementById('system-status').textContent = 'System Status: ' + data.status.toUpperCase() + ' (Fallback)';
                })
                .catch(fallbackError => {
                    console.error('Fallback failed:', fallbackError);
                });
        }
        
        function updateSystemOverview(system) {
            const html = `
                <div class="metric">
                    <span class="metric-label">Version</span>
                    <span class="metric-value">${system.version}</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Status</span>
                    <span class="metric-value status-enabled">${system.status.toUpperCase()}</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Storage Access</span>
                    <span class="metric-value ${system.storage_accessible ? 'status-enabled' : 'status-disabled'}">
                        ${system.storage_accessible ? 'ACCESSIBLE' : 'ERROR'}
                    </span>
                </div>
                <div class="metric">
                    <span class="metric-label">Last Scheduled Run</span>
                    <span class="metric-value">${formatDateTime(system.last_scheduled_run)}</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Next Scheduled Run</span>
                    <span class="metric-value">${system.next_scheduled_run}</span>
                </div>
            `;
            document.getElementById('system-overview').innerHTML = html;
        }
        
        function updateWebsitesList(websites) {
            if (!websites.sites || websites.sites.length === 0) {
                document.getElementById('websites-list').innerHTML = '<p>No websites configured</p>';
                return;
            }
            
            let html = `
                <div class="metric">
                    <span class="metric-label">Total Configured</span>
                    <span class="metric-value">${websites.total_configured}</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Currently Enabled</span>
                    <span class="metric-value status-enabled">${websites.enabled_count}</span>
                </div>
                <hr style="margin: 15px 0;">
            `;
            
            websites.sites.forEach(site => {
                html += `
                    <div class="website-item">
                        <div class="website-name">${site.name}</div>
                        <div class="website-url">${site.url}</div>
                        <div style="margin-top: 5px; font-size: 0.8em; color: #6c757d;">${site.description}</div>
                    </div>
                `;
            });
            
            document.getElementById('websites-list').innerHTML = html;
        }
        
        function updateStorageStats(storage) {
            if (storage.error) {
                document.getElementById('storage-stats').innerHTML = `<div class="error">Storage Error: ${storage.error}</div>`;
                return;
            }
            
            let html = `
                <div class="metric">
                    <span class="metric-label">Total Documents</span>
                    <span class="metric-value">${storage.total_documents}</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Total Storage Used</span>
                    <span class="metric-value">${storage.total_size_mb} MB</span>
                </div>
                <hr style="margin: 15px 0;">
                <h4 style="margin-bottom: 10px; color: #495057;">Documents by Source:</h4>
            `;
            
            if (storage.site_breakdown) {
                Object.entries(storage.site_breakdown).forEach(([site, stats]) => {
                    if (stats.count > 0) {
                        html += `
                            <div class="metric">
                                <span class="metric-label">${site}</span>
                                <span class="metric-value">${stats.count} docs (${formatBytes(stats.size)})</span>
                            </div>
                        `;
                    }
                });
            }
            
            document.getElementById('storage-stats').innerHTML = html;
        }
        
        function updateRecentActivity(activity) {
            const html = `
                <div class="metric">
                    <span class="metric-label">Crawls (24h)</span>
                    <span class="metric-value">${activity.crawls_last_24h}</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Documents Processed (24h)</span>
                    <span class="metric-value">${activity.documents_processed_24h}</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Documents Uploaded (24h)</span>
                    <span class="metric-value">${activity.documents_uploaded_24h}</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Collisions Detected (24h)</span>
                    <span class="metric-value ${activity.collisions_detected_24h > 0 ? 'status-disabled' : 'status-enabled'}">
                        ${activity.collisions_detected_24h} ${activity.collisions_detected_24h === 0 ? '✓' : '⚠️'}
                    </span>
                </div>
                <div class="metric">
                    <span class="metric-label">Last Crawl</span>
                    <span class="metric-value">${activity.last_crawl ? formatDateTime(activity.last_crawl.timestamp) : 'Never'}</span>
                </div>
            `;
            document.getElementById('recent-activity').innerHTML = html;
        }
        
        function updateValidationStats(validation, activity) {
            // Phase 2: Display storage validation metrics
            const statusIcon = validation.status === 'match' ? '✅' : validation.status === 'mismatch' ? '⚠️' : '❓';
            const statusClass = validation.status === 'match' ? 'status-enabled' : 'status-disabled';
            
            const html = `
                <div class="metric">
                    <span class="metric-label">Validation Status</span>
                    <span class="metric-value ${statusClass}">${statusIcon} ${validation.status.toUpperCase()}</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Storage Accuracy</span>
                    <span class="metric-value ${validation.accuracy_percentage >= 99 ? 'status-enabled' : 'status-disabled'}">
                        ${validation.accuracy_percentage.toFixed(2)}%
                    </span>
                </div>
                <div class="metric">
                    <span class="metric-label">Last Validation Check</span>
                    <span class="metric-value">${formatDateTime(validation.last_check)}</span>
                </div>
                <hr style="margin: 15px 0;">
                <div class="metric">
                    <span class="metric-label">Uploaded This Session</span>
                    <span class="metric-value">${validation.uploaded_count}</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Verified in Storage</span>
                    <span class="metric-value">${validation.storage_count}</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Filename Collisions (24h)</span>
                    <span class="metric-value ${activity.collisions_detected_24h === 0 ? 'status-enabled' : 'status-disabled'}">
                        ${activity.collisions_detected_24h} ${activity.collisions_detected_24h === 0 ? '(Good ✓)' : '(Review Required)'}
                    </span>
                </div>
            `;
            document.getElementById('validation-stats').innerHTML = html;
        }
        
        function updateCrawlHistory(history) {
            if (!history || history.length === 0) {
                document.getElementById('crawl-history').innerHTML = '<p>No crawl history available</p>';
                return;
            }
            
            let html = '';
            history.slice(-5).reverse().forEach(crawl => {
                html += `
                    <div class="crawl-entry">
                        <div class="crawl-time">${formatDateTime(crawl.timestamp)} (${crawl.trigger_type})</div>
                        <div class="crawl-stats">
                            <div>Sites: ${crawl.sites_processed}</div>
                            <div>Found: ${crawl.documents_found}</div>
                            <div>New: ${crawl.documents_new}</div>
                            <div>Changed: ${crawl.documents_changed}</div>
                            <div>Unchanged: ${crawl.documents_unchanged}</div>
                            <div>Uploaded: ${crawl.documents_uploaded}</div>
                        </div>
                    </div>
                `;
            });
            
            document.getElementById('crawl-history').innerHTML = html;
        }
        
        function showError(message) {
            const cards = document.querySelectorAll('.card div[id]');
            cards.forEach(card => {
                if (card.textContent.includes('Loading')) {
                    card.innerHTML = `<div class="error">${message}</div>`;
                }
            });
        }
        
        // Load data on page load
        window.onload = function() {
            loadDashboardData();
            // Auto-refresh every 30 seconds
            setInterval(loadDashboardData, 30000);
        };
    </script>
</body>
</html>
    """
    
    return func.HttpResponse(
        dashboard_html,
        status_code=200,
        mimetype="text/html"
    )
    
    return func.HttpResponse(
        json.dumps({
            "status": "WORKING",
            "message": "Web crawler with NPCC and College of Policing integration - v2.2.0 Official Release",
            "version": "v2.2.0",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "storage_account": "stbtpuksprodcrawler01",
            "container": "documents",
            "features": [
                "Document discovery",
                "Real Azure Storage uploads", 
                "PDF and XML support",
                "4-hour timer scheduling",
                "NPCC Publications monitoring",
                "College of Policing (bot protection bypassed)",
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
        "college_of_policing": {
            "name": "College of Policing - App Portal",
            "url": "https://www.college.police.uk/app", 
            "enabled": True,
            "description": "College of Policing app portal - trying /app path to bypass bot protection",
            "document_types": ["pdf", "doc", "docx", "xml"]
        },
        "npcc_publications": {
            "name": "NPCC Publications - All Publications", 
            "url": "https://www.npcc.police.uk/publications/All-publications/",
            "enabled": True,
            "description": "NPCC All Publications page - comprehensive publication database",
            "document_types": ["pdf", "doc", "docx", "xml"]
        },
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

@app.route(route="initialize_folders", methods=["POST"], auth_level=func.AuthLevel.ANONYMOUS)
def initialize_folders(req: func.HttpRequest) -> func.HttpResponse:
    """Initialize storage folders for all configured websites"""
    logging.info('Initialize folders endpoint called')
    
    try:
        # Get all websites from websites.json
        websites_data = load_websites_config()
        
        if "error" in websites_data:
            return func.HttpResponse(
                json.dumps({"error": websites_data["error"]}),
                status_code=500,
                mimetype="application/json"
            )
        
        results = []
        success_count = 0
        fail_count = 0
        
        # websites_data["websites"] is a list, not a dict
        for website_config in websites_data.get("websites", []):
            website_name = website_config["name"]
            logging.info(f'Creating folder for: {website_name}')
            
            if ensure_website_folder_exists(website_name):
                results.append({
                    "website": website_name,
                    "status": "success",
                    "folder": get_folder_name_for_website(website_name)
                })
                success_count += 1
            else:
                results.append({
                    "website": website_name,
                    "status": "failed",
                    "folder": get_folder_name_for_website(website_name)
                })
                fail_count += 1
        
        return func.HttpResponse(
            json.dumps({
                "message": "Folder initialization complete",
                "total_websites": len(websites_data.get("websites", [])),
                "success_count": success_count,
                "fail_count": fail_count,
                "results": results,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }, indent=2),
            status_code=200,
            mimetype="application/json"
        )
        
    except Exception as e:
        logging.error(f'Initialize folders error: {str(e)}')
        return func.HttpResponse(
            json.dumps({"error": str(e)}),
            status_code=500,
            mimetype="application/json"
        )

@app.route(route="cleanup_uncategorized", methods=["GET", "POST"], auth_level=func.AuthLevel.ANONYMOUS)
def cleanup_uncategorized(req: func.HttpRequest) -> func.HttpResponse:
    """Clean up documents without proper folder structure (uncategorized documents)
    
    GET: List uncategorized documents (dry run)
    POST with {"dry_run": false}: Actually delete uncategorized documents
    """
    logging.info('Cleanup uncategorized endpoint called')
    
    try:
        dry_run = True  # Default to dry run for safety
        
        if req.method == "POST":
            try:
                req_body = req.get_json()
                dry_run = req_body.get('dry_run', True)
            except:
                dry_run = True
        
        result = delete_uncategorized_documents(dry_run=dry_run)
        
        if "error" in result:
            return func.HttpResponse(
                json.dumps(result),
                status_code=500,
                mimetype="application/json"
            )
        
        return func.HttpResponse(
            json.dumps(result, indent=2),
            status_code=200,
            mimetype="application/json"
        )
        
    except Exception as e:
        logging.error(f'Cleanup uncategorized error: {str(e)}')
        return func.HttpResponse(
            json.dumps({"error": str(e)}),
            status_code=500,
            mimetype="application/json"
        )

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

# ============================================================================
# SIMPLE TEST ENDPOINT - VERIFY DEPLOYMENT
# ============================================================================

@app.route(route="diagnostic", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
def diagnostic(req: func.HttpRequest) -> func.HttpResponse:
    """Diagnostic endpoint to check storage folders and document counts"""
    logging.info('Diagnostic endpoint called')
    
    try:
        # Get storage statistics
        storage_stats = get_storage_statistics()
        
        if "error" in storage_stats:
            return func.HttpResponse(
                json.dumps({"error": storage_stats["error"]}),
                status_code=500,
                mimetype="application/json"
            )
        
        # Get document hashes to check what we think is stored
        doc_hashes = get_document_hashes_from_storage()
        
        # Organize hashes by website
        hashes_by_site = {}
        for url, hash_info in doc_hashes.items():
            unique_filename = hash_info.get("unique_filename", "")
            if '/' in unique_filename:
                site_folder = unique_filename.split('/')[0]
                if site_folder not in hashes_by_site:
                    hashes_by_site[site_folder] = []
                hashes_by_site[site_folder].append({
                    "url": url,
                    "filename": hash_info.get("filename"),
                    "unique_filename": unique_filename,
                    "last_seen": hash_info.get("last_seen")
                })
        
        return func.HttpResponse(
            json.dumps({
                "message": "Diagnostic information",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "storage_stats": {
                    "total_documents": storage_stats.get("total_documents", 0),
                    "total_size_mb": storage_stats.get("total_size_mb", 0),
                    "site_breakdown": storage_stats.get("site_breakdown", {})
                },
                "document_hashes": {
                    "total_tracked": len(doc_hashes),
                    "by_site_folder": {k: len(v) for k, v in hashes_by_site.items()},
                    "sample_per_site": {k: v[:3] for k, v in hashes_by_site.items()}  # First 3 from each site
                }
            }, indent=2),
            status_code=200,
            mimetype="application/json"
        )
        
    except Exception as e:
        logging.error(f'Diagnostic error: {str(e)}')
        return func.HttpResponse(
            json.dumps({"error": str(e)}),
            status_code=500,
            mimetype="application/json"
        )

@app.route(route="trigger_crawl", methods=["POST"], auth_level=func.AuthLevel.ANONYMOUS)
@app.durable_client_input(client_name="client")
async def trigger_crawl(req: func.HttpRequest, client) -> func.HttpResponse:
    """
    HTTP-triggered endpoint to manually start the full website crawl orchestration.
    This bypasses the 4-hour timer and starts crawling immediately.
    
    Usage: POST to /api/trigger_crawl
    """
    logging.info('🚀 Manual crawl trigger: Starting orchestrated multi-website crawler')
    
    try:
        # Start the orchestration (same as scheduled_crawler_orchestrated)
        instance_id = await client.start_new('web_crawler_orchestrator', None, None)
        
        logging.info(f'✅ Manual crawl orchestration started with ID: {instance_id}')
        
        return func.HttpResponse(
            json.dumps({
                "status": "success",
                "message": "Crawl orchestration started successfully",
                "instance_id": instance_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "note": "Crawling all enabled websites in parallel. Check logs for progress."
            }, indent=2),
            status_code=200,
            mimetype="application/json"
        )
        
    except Exception as e:
        logging.error(f'❌ Error starting manual crawl orchestration: {str(e)}')
        return func.HttpResponse(
            json.dumps({
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }),
            status_code=500,
            mimetype="application/json"
        )

@app.route(route="ping", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
def ping(req: func.HttpRequest) -> func.HttpResponse:
    """Ultra-simple test endpoint to verify function app is working"""
    logging.info('Ping endpoint called')
    return func.HttpResponse(
        json.dumps({
            "status": "alive",
            "message": "Function app is running",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "version": "v2.7.3"
        }),
        status_code=200,
        mimetype="application/json"
    )