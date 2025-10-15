import azure.functions as func
import logging
import json
import urllib.request
import urllib.parse
import urllib.error
from datetime import datetime, timezone

# Function App with function level authentication for security
app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)

# Timer trigger function that runs every 4 hours
@app.timer_trigger(schedule="0 0 */4 * * *", arg_name="mytimer", run_on_startup=False,
              use_monitor=False) 
def scheduled_crawler(mytimer: func.TimerRequest) -> None:
    """Timer trigger function that crawls websites every 4 hours"""
    logging.info('Scheduled crawler function started - using urllib!')
    
    # Test basic HTTP request using built-in urllib
    try:
        with urllib.request.urlopen("https://httpbin.org/json", timeout=10) as response:
            content = response.read().decode('utf-8')
            logging.info(f'Test request successful: {response.status}')
    except Exception as e:
        logging.error(f'Test request failed: {str(e)}')

@app.route(route="manual_crawl", methods=["POST"])
def manual_crawl(req: func.HttpRequest) -> func.HttpResponse:
    """Manual trigger for crawling a specific website"""
    logging.info('Manual crawl function triggered - using urllib!')
    
    try:
        # Test basic HTTP request using built-in urllib
        with urllib.request.urlopen("https://httpbin.org/json", timeout=10) as response:
            content = response.read().decode('utf-8')
            
        return func.HttpResponse(
            json.dumps({
                "message": "Web crawler with urllib is working!",
                "test_request_status": response.status,
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
    logging.info('Search site function triggered - using urllib!')
    
    url = req.params.get('url', 'https://httpbin.org')
    
    # Basic URL validation
    if not url.startswith(('http://', 'https://')):
        return func.HttpResponse(
            json.dumps({"error": "Invalid URL - must start with http:// or https://"}),
            status_code=400,
            mimetype="application/json"
        )
    
    try:
        # Test the provided URL using built-in urllib
        with urllib.request.urlopen(url, timeout=10) as response:
            content = response.read().decode('utf-8')
            
        return func.HttpResponse(
            json.dumps({
                "url": url,
                "status_code": response.status,
                "content_length": len(content),
                "message": "URL test with urllib successful"
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