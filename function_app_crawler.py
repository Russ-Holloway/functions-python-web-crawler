import azure.functions as func
import logging
import requests
import json
import hashlib
from datetime import datetime, timezone
from urllib.parse import urljoin, urlparse
from typing import List, Dict, Any

from bs4 import BeautifulSoup
import validators

# Function App with function level authentication for security
app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)

# Timer trigger function that runs every 4 hours
@app.timer_trigger(schedule="0 0 */4 * * *", arg_name="mytimer", run_on_startup=False,
              use_monitor=False) 
def scheduled_crawler(mytimer: func.TimerRequest) -> None:
    """Timer trigger function that crawls websites every 4 hours"""
    logging.info('Scheduled crawler function started!')
    
    # For now, just log that it's working
    # We'll add full functionality once basic crawling works
    test_url = "https://httpbin.org"
    documents = search_website_for_documents(test_url)
    logging.info(f'Found {len(documents)} documents on test site')

@app.route(route="manual_crawl", methods=["POST"])
def manual_crawl(req: func.HttpRequest) -> func.HttpResponse:
    """Manual trigger for crawling a specific website"""
    logging.info('Manual crawl function triggered!')
    
    try:
        req_body = req.get_json()
        url = req_body.get('url') if req_body else None
        
        if not url:
            return func.HttpResponse(
                json.dumps({"error": "URL is required"}),
                status_code=400,
                mimetype="application/json"
            )
            
        if not validators.url(url):
            return func.HttpResponse(
                json.dumps({"error": "Invalid URL"}),
                status_code=400,
                mimetype="application/json"
            )
        
        # Search for documents
        documents = search_website_for_documents(url)
        
        return func.HttpResponse(
            json.dumps({
                "message": f"Successfully crawled website: {url}",
                "documents_found": len(documents),
                "documents": documents[:5]  # Return first 5 for testing
            }),
            status_code=200,
            mimetype="application/json"
        )
        
    except Exception as e:
        logging.error(f"Error in manual crawl: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": str(e)}),
            status_code=500,
            mimetype="application/json"
        )

@app.route(route="search_site", methods=["POST"])
def search_site(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Search site function triggered!')
    
    try:
        url = req.params.get('url')
        if not url:
            req_body = req.get_json()
            url = req_body.get('url') if req_body else None

        if url and validators.url(url):
            documents = search_website_for_documents(url)
            return func.HttpResponse(
                json.dumps({"documents": documents, "count": len(documents)}),
                status_code=200,
                mimetype="application/json"
            )
        else:
            return func.HttpResponse(
                json.dumps({"error": "Valid URL required"}),
                status_code=400,
                mimetype="application/json"
            )
    except Exception as e:
        logging.error(f"Error in search_site: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": str(e)}),
            status_code=500,
            mimetype="application/json"
        )

def search_website_for_documents(base_url: str) -> List[Dict[str, Any]]:
    """Search a website for downloadable documents"""
    try:
        documents = []
        visited_urls = set()
        urls_to_visit = [(base_url, 0)]  # (url, depth)
        
        file_patterns = ['.pdf', '.doc', '.docx', '.txt', '.xls', '.xlsx']
        max_depth = 2  # Keep it simple for now
        
        while urls_to_visit:
            current_url, depth = urls_to_visit.pop(0)
            
            if current_url in visited_urls or depth > max_depth:
                continue
                
            visited_urls.add(current_url)
            
            try:
                response = requests.get(current_url, timeout=10, headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                })
                response.raise_for_status()
                
                # Check if this URL itself is a document
                if any(pattern in current_url.lower() for pattern in file_patterns):
                    doc_info = {
                        'url': current_url,
                        'title': current_url.split('/')[-1],
                        'size': len(response.content),
                        'content_type': response.headers.get('content-type', ''),
                        'found_at': datetime.now(timezone.utc).isoformat()
                    }
                    documents.append(doc_info)
                    continue
                
                # Parse HTML content for links to documents
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Find all links
                for link in soup.find_all('a', href=True):
                    href = link['href']
                    full_url = urljoin(current_url, href)
                    
                    # Check if it's a document link
                    if any(pattern in href.lower() for pattern in file_patterns):
                        doc_info = {
                            'url': full_url,
                            'title': link.get_text(strip=True) or href.split('/')[-1],
                            'found_at': datetime.now(timezone.utc).isoformat(),
                            'source_page': current_url
                        }
                        documents.append(doc_info)
                    
                    # Add internal links to visit (if within same domain and not too deep)
                    elif urlparse(full_url).netloc == urlparse(base_url).netloc and depth < max_depth:
                        if full_url not in visited_urls:
                            urls_to_visit.append((full_url, depth + 1))
                            
            except Exception as e:
                logging.warning(f"Error processing URL {current_url}: {str(e)}")
                continue
                
        logging.info(f"Found {len(documents)} documents on {base_url}")
        return documents
        
    except Exception as e:
        logging.error(f"Error searching website {base_url}: {str(e)}")
        return []