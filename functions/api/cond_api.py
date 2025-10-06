from firebase_functions.https_fn import Request, Response
import json
from firebase_admin import storage as s
import re

my_bucket = "enigmagenomics-internship.firebasestorage.app"
file_path = "genes/conditions_updated/"

def safe_name(name):
    fi_name = re.sub(r"[^a-zA-Z0-9]+", "_", name.lower())
    fi_name = re.sub(r'_+', '_', fi_name).strip('_')
    return fi_name

def matching_value(name):
    s = safe_name(name)
    s = s.replace("_", "")
    return s

def get_cond(req: Request) -> Response:
    z = req.args.get("search")
    
    if not z:
        return Response(
            json.dumps({"error": "Missing ?search=Condition(s) to find"}),
            status=400,
            mimetype="application/json"
        )

    Total_cond = z.split(",")
    cond_list =[]
    for g in Total_cond:
        if g.strip():
            x = g.strip()
            cond_list.append(x)
    
    if len(cond_list) > 20:
        return Response(
            json.dumps({"error": "Maximum 20 conditions allowed per request"}),
            status=400,
            mimetype="application/json"
        )

    bucket = s.bucket(my_bucket)
    results = []

    for c in cond_list:
        search_value = matching_value(c)
        try:
            blobs = list(bucket.list_blobs(prefix=file_path))
            matched_blob = None
            for b in blobs:
                fname = b.name
                fname = fname.split("/")
                fname = fname[-1]
                fname = fname.replace(".json", "")
                fname = fname.replace("_", "")
                if fname == search_value:
                    matched_blob = b
                    break

            if matched_blob:
                data = matched_blob.download_as_text()
                results.append(json.loads(data))
            else:
                results.append({"error": f"Condition '{c}' not found"})

        except Exception as e:
            results.append({"error": str(e)})

    return Response(
        json.dumps(results, indent=2),
        status=200,
        mimetype="application/json"
    )
