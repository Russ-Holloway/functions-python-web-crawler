"""
Simple test function to verify Azure Functions runtime is working
This is a standalone test - delete after verification
"""
import azure.functions as func
import logging

# Create a simple FunctionApp (not DFApp)
test_app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

@test_app.route(route="test", methods=["GET"])
def test_function(req: func.HttpRequest) -> func.HttpResponse:
    """Simple test function"""
    logging.info('Test function triggered')
    return func.HttpResponse(
        "TEST FUNCTION WORKS! If you see this, Azure Functions runtime is discovering functions.",
        status_code=200
    )
