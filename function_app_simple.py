import azure.functions as func
import logging

# Simple Function App to test deployment
app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)

@app.route(route="hello", methods=["GET", "POST"])
def hello_world(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')
    
    name = req.params.get('name')
    if not name:
        try:
            req_body = req.get_json()
        except ValueError:
            pass
        else:
            name = req_body.get('name')

    if name:
        return func.HttpResponse(f"Hello, {name}! This Azure Function is working.")
    else:
        return func.HttpResponse(
            "Hello! This Azure Function is working. Pass a name in the query string or request body.",
            status_code=200
        )

@app.timer_trigger(schedule="0 */5 * * * *", arg_name="mytimer", run_on_startup=False,
              use_monitor=False) 
def test_timer(mytimer: func.TimerRequest) -> None:
    """Test timer function that runs every 5 minutes"""
    logging.info('Test timer function executed.')