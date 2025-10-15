import azure.functions as func
import logging

# Simple test function app
app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

@app.route(route="test", methods=["GET"])
def test_function(req: func.HttpRequest) -> func.HttpResponse:
    """Ultra simple test function"""
    logging.info('Test function called')
    
    return func.HttpResponse(
        '{"status": "SUCCESS", "message": "Test function is working!"}',
        status_code=200,
        mimetype="application/json"
    )