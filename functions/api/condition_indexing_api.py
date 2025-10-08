from firebase_functions.https_fn import Request, Response
from firebase_admin import storage as s
import json
import re

BUCKET_NAME = "enigmagenomics-internship.firebasestorage.app"
INDEX_FILE_PATH = "genes/index/condition_index.json"

def safe_name(name):
    
    name = name.lower()
    name = re.sub(r"[^a-zA-Z0-9]+", "_", name)
    name = re.sub(r"_+", "_", name).strip("_")
    return name

def matching_name(name):
    
    s = safe_name(name)
    s = s.replace("_", "")
    return s

def find_conditions(req: Request) -> Response:
    
    z = req.args.get("search")
    if not z:
        return Response(
            json.dumps({"error": "Please provide ?search=Condition(s) to find"}),
            status=400,
            mimetype="application/json"
        )

    Total_conditions = z.split(",")
    conditions_list =[]
    for g in Total_conditions:
        if g.strip():
            x = g.strip()
            conditions_list.append(x)


    if len(conditions_list) > 20:
        return Response(
            json.dumps({"error": "Maximum 20 conditions allowed per request"}),
            status=400,
            mimetype="application/json"
        )

    bucket = s.bucket(BUCKET_NAME)

    try:
        index_blob = bucket.blob(INDEX_FILE_PATH)
        index_d  = index_blob.download_as_text()
        index = json.loads(index_d)
    except Exception as e:
        return Response(
            json.dumps({"error": f"Failed to load condition index: {str(e)}"}),
            status=500,
            mimetype="application/json"
        )
        
    results = []

    for c in conditions_list:
        search_val = matching_name(c)
        match = []

        for k in index:
            if search_val in k.replace("_", ""):
                
                try:
                    path = index[k]
                    cond_blob = bucket.blob(path)
                    data = cond_blob.download_as_text()
                    cond_data = json.loads(data)
                    match.append(cond_data)
                except Exception as e:
                    match.append({"error": str(e)})

        if not match:
            match.append({"error": f"No match found for '{c}'"})

        results.extend(match)

    return Response(
        json.dumps(results, indent=2),
        status=200,
        mimetype="application/json"
    )
