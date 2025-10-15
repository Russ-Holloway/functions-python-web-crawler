import azure.functions as func
import logging
import json
import urllib.request
import urllib.parse
import urllib.error
from datetime import datetime, timezone
from html.parser import HTMLParser
import re

class DocumentLinkParser(HTMLParser):
    """Simple HTML parser to find document links"""
    def __init__(self):
        super().__init__()
        self.document_links = []
        self.document_extensions = {'.pdf', '.doc', '.docx', '.txt', '.xls', '.xlsx'}
    
    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            for attr_name, attr_value in attrs:
                if attr_name == 'href' and attr_value:
                    # Check if link points to a document
                    lower_url = attr_value.lower()
                    if any(lower_url.endswith(ext) for ext in self.document_extensions):
                        self.document_links.append(attr_value)

def find_documents_in_html(html_content, base_url):
    """Parse HTML and find document links"""
    parser = DocumentLinkParser()
    try:
        parser.feed(html_content)
        
        # Convert relative URLs to absolute
        documents = []
        for link in parser.document_links:
            if link.startswith(('http://', 'https://')):
                absolute_url = link
            else:
                absolute_url = urllib.parse.urljoin(base_url, link)
            
            documents.append({
                "url": absolute_url,
                "filename": link.split('/')[-1],
                "extension": link.split('.')[-1].lower() if '.' in link else 'unknown'
            })
        
        return documents
    except Exception as e:
        logging.error(f'HTML parsing error: {str(e)}')
        return []

# Function App with function level authentication for security
app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)

# Timer trigger function that runs every 4 hours
@app.timer_trigger(schedule="0 0 */4 * * *", arg_name="mytimer", run_on_startup=False,
              use_monitor=False) 
def scheduled_crawler(mytimer: func.TimerRequest) -> None:
    """Timer trigger function that crawls websites every 4 hours"""
    logging.info('Scheduled crawler function started - with HTML parsing!')
    
    # Test basic crawling
    try:
        test_url = "https://httpbin.org/html"
        with urllib.request.urlopen(test_url, timeout=10) as response:
            content = response.read().decode('utf-8')
            documents = find_documents_in_html(content, test_url)
            logging.info(f'Found {len(documents)} documents on test site')
    except Exception as e:
        logging.error(f'Scheduled crawl failed: {str(e)}')

@app.route(route="manual_crawl", methods=["POST"])
def manual_crawl(req: func.HttpRequest) -> func.HttpResponse:
    """Manual trigger for crawling a specific website"""
    logging.info('Manual crawl function triggered - with HTML parsing!')
    
    try:
        req_body = req.get_json()
        url = req_body.get('url') if req_body else None
        
        if not url:
            url = "https://httpbin.org/html"  # Default test URL
        
        # Basic URL validation
        if not url.startswith(('http://', 'https://')):
            return func.HttpResponse(
                json.dumps({"error": "Invalid URL - must start with http:// or https://"}),
                status_code=400,
                mimetype="application/json"
            )
        
        with urllib.request.urlopen(url, timeout=10) as response:
            content = response.read().decode('utf-8')
            documents = find_documents_in_html(content, url)
            
        return func.HttpResponse(
            json.dumps({
                "message": "Web crawler with HTML parsing is working!",
                "url": url,
                "status_code": response.status,
                "documents_found": len(documents),
                "documents": documents[:5],  # Limit to first 5 for response size
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
    """Search a specific site for documents"""
    logging.info('Search site function triggered - with HTML parsing!')
    
    url = req.params.get('url', 'https://httpbin.org/html')
    
    # Basic URL validation
    if not url.startswith(('http://', 'https://')):
        return func.HttpResponse(
            json.dumps({"error": "Invalid URL - must start with http:// or https://"}),
            status_code=400,
            mimetype="application/json"
        )
    
    try:
        with urllib.request.urlopen(url, timeout=10) as response:
            content = response.read().decode('utf-8')
            documents = find_documents_in_html(content, url)
            
        return func.HttpResponse(
            json.dumps({
                "url": url,
                "status_code": response.status,
                "content_length": len(content),
                "documents_found": len(documents),
                "documents": documents,
                "message": "Document search with HTML parsing successful"
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