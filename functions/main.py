# Welcome to Cloud Functions for Firebase for Python!
# To get started, simply uncomment the below code or create your own.
# Deploy with `firebase deploy`

from firebase_functions import https_fn
from firebase_functions.options import set_global_options
from firebase_admin import initialize_app
from firebase_functions.https_fn import Request , Response
from scraping.medlineplus_conditions import condition_function
import json

# For cost control, you can set the maximum number of containers that can be
# running at the same time. This helps mitigate the impact of unexpected
# traffic spikes by instead downgrading performance. This limit is a per-function
# limit. You can override the limit for each function using the max_instances
# parameter in the decorator, e.g. @https_fn.on_request(max_instances=5).
set_global_options(max_instances=10)

initialize_app()

@https_fn.on_request(timeout_sec=360)
def crawling_conditions(req:Request) -> Response:
    
    total_genes, msg = condition_function()
    return Response( 
        json.dumps({"status": "success", "Total_genes": total_genes, "message": msg}), 
        mimetype="application/json" 
    )
    