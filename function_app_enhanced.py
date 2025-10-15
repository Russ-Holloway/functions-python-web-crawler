import azure.functions as func
import logging
import json
import urllib.request
import urllib.parse
import urllib.error
from datetime import datetime, timezone
from html.parser import HTMLParser
import re

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

# Function App with function level authentication for security
app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)

# Timer trigger function that runs every 4 hours
@app.timer_trigger(schedule="0 0 */4 * * *", arg_name="mytimer", run_on_startup=False,
              use_monitor=False) 
def scheduled_crawler(mytimer: func.TimerRequest) -> None:
    """Timer trigger function that crawls websites every 4 hours"""
    logging.info('Scheduled crawler function started - enhanced version!')
    
    # Test basic crawling
    try:
        test_url = "https://www.legislation.gov.uk/"
        with urllib.request.urlopen(test_url, timeout=15) as response:
            content = response.read().decode('utf-8')
            result = find_documents_in_html(content, test_url)
            logging.info(f'Found {len(result["documents"])} documents on test site')
    except Exception as e:
        logging.error(f'Scheduled crawl failed: {str(e)}')

@app.route(route="manual_crawl", methods=["POST"])
def manual_crawl(req: func.HttpRequest) -> func.HttpResponse:
    """Manual trigger for crawling a specific website"""
    logging.info('Manual crawl function triggered - enhanced version!')
    
    try:
        req_body = req.get_json()
        url = req_body.get('url') if req_body else None
        
        if not url:
            url = "https://www.legislation.gov.uk/"  # Default test URL
        
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
            
        return func.HttpResponse(
            json.dumps({
                "message": "Enhanced web crawler with debugging is working!",
                "url": url,
                "status_code": response.status,
                "documents_found": len(result["documents"]),
                "documents": result["documents"][:10],  # Limit to first 10
                "debug_info": {
                    "total_links_found": result["total_links_found"],
                    "sample_links": result["sample_links"]
                },
                "timestamp": datetime.now(timezone.utc).isoformat()
            }),
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
    logging.info('Search site function triggered - enhanced version!')
    
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
                "message": "Enhanced document search with debugging successful"
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