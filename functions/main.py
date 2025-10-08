# Welcome to Cloud Functions for Firebase for Python!
# To get started, simply uncomment the below code or create your own.
# Deploy with `firebase deploy`

from firebase_functions import https_fn
from firebase_admin import initialize_app
from firebase_functions.https_fn import Request , Response
import json
from scraping.medlineAsyncNormal import async_cond_function
from api.condition_api import get_condition
from api.condition_indexing_api import find_conditions
from scraping.medlineasync import indexing_conditions_function


# For cost control, you can set the maximum number of containers that can be
# running at the same time. This helps mitigate the impact of unexpected
# traffic spikes by instead downgrading performance. This limit is a per-function
# limit. You can override the limit for each function using the max_instances
# parameter in the decorator, e.g. @https_fn.on_request(max_instances=5).

initialize_app()

@https_fn.on_request(timeout_sec=360)
def crawling_all_conditions_with_indexing(req:Request) -> Response:
    print("Crawling started...")
    total_conditions, msg = indexing_conditions_function()
    print("Crawling finished.")
    return Response( 
        json.dumps({"status": "success", "Total_conditions": total_conditions, "message": msg}), 
        mimetype="application/json" 
    )
    

@https_fn.on_request(timeout_sec=300)
def crawling_conditions(req:Request) -> Response:
    print("Crawl started...")
    total_conditions, msg = async_cond_function()
    print("Crawl finished.")
    return Response( 
        json.dumps({"status": "success", "Total_conditions": total_conditions, "message": msg}), 
        mimetype="application/json" 
    )
    
@https_fn.on_request()
def search_conditions_api(req:Request) -> Response:
    return get_condition(req)

@https_fn.on_request()
def getConditions(req:Request) -> Response:
    return find_conditions(req)
    