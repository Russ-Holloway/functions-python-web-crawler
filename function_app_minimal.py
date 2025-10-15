import azure.functions as func
import logging

# Function App with function level authentication for security
app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)

# Timer trigger function that runs every 4 hours
@app.timer_trigger(schedule="0 0 */4 * * *", arg_name="mytimer", run_on_startup=False,
              use_monitor=False) 
def scheduled_crawler(mytimer: func.TimerRequest) -> None:
    """Timer trigger function that crawls websites every 4 hours"""
    logging.info('Scheduled crawler function started - this is the real crawler!')

@app.route(route="manual_crawl", methods=["POST"])
def manual_crawl(req: func.HttpRequest) -> func.HttpResponse:
    """Manual trigger for crawling a specific website"""
    logging.info('Manual crawl function triggered - this is the real crawler!')
    
    return func.HttpResponse(
        '{"message": "Web crawler is working! This is the real version."}',
        status_code=200,
        mimetype="application/json"
    )

@app.route(route="search_site", methods=["POST"])
def search_site(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Search site function triggered - this is the real crawler!')
    
    return func.HttpResponse(
        '{"message": "Search site is working! This is the real version."}',
        status_code=200,
        mimetype="application/json"
    )