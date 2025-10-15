import azure.functions as func
import logging
import json

# Create function app
app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

@app.route(route="status", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
def status(req: func.HttpRequest) -> func.HttpResponse:
    """Simple status endpoint"""
    logging.info('Status endpoint called')
    
    return func.HttpResponse(
        json.dumps({
            "status": "WORKING",
            "message": "Fresh deployment test successful!",
            "timestamp": "2025-10-15"
        }),
        status_code=200,
        mimetype="application/json"
    )

@app.route(route="test", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
def test(req: func.HttpRequest) -> func.HttpResponse:
    """Test endpoint"""
    logging.info('Test endpoint called')
    
    return func.HttpResponse(
        json.dumps({"test": "success", "message": "Function is working"}),
        status_code=200,
        mimetype="application/json"
    )