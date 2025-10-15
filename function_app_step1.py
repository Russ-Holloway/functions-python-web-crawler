import azure.functions as func
import logging
import requests
import json
from datetime import datetime, timezone

# Function App with function level authentication for security
app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)

# Timer trigger function that runs every 4 hours
@app.timer_trigger(schedule="0 0 */4 * * *", arg_name="mytimer", run_on_startup=False,
              use_monitor=False) 
def scheduled_crawler(mytimer: func.TimerRequest) -> None:
    """Timer trigger function that crawls websites every 4 hours"""
    logging.info('Scheduled crawler function started - now with requests!')
    
    # Test basic HTTP request
    try:
        response = requests.get("https://httpbin.org/json", timeout=10)
        logging.info(f'Test request successful: {response.status_code}')
    except Exception as e:
        logging.error(f'Test request failed: {str(e)}')

@app.route(route="manual_crawl", methods=["POST"])
def manual_crawl(req: func.HttpRequest) -> func.HttpResponse:
    """Manual trigger for crawling a specific website"""
    logging.info('Manual crawl function triggered - now with requests!')
    
    try:
        # Test basic HTTP request
        response = requests.get("https://httpbin.org/json", timeout=10)
        
        return func.HttpResponse(
            json.dumps({
                "message": "Web crawler with requests is working!",
                "test_request_status": response.status_code,
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
    logging.info('Search site function triggered - now with requests!')
    
    url = req.params.get('url', 'https://httpbin.org')
    
    try:
        # Test the provided URL
        response = requests.get(url, timeout=10)
        
        return func.HttpResponse(
            json.dumps({
                "url": url,
                "status_code": response.status_code,
                "content_length": len(response.text),
                "message": "URL test with requests successful"
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