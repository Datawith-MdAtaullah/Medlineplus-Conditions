import json
import time
from datetime import datetime
from firebase_admin import storage as s


def log_condition_run(success_conditions, failed_conditions, total_conditions, bucket_path="genes/conditions_updated/"):
   
    bucket = s.bucket()

    run_start = time.time()
    timestamp = datetime.utcnow().strftime("%Y-%m-%dT%H-%M-%SZ")

    
    success_count = len(success_conditions)
    failed_count = len(failed_conditions)


    total_data_size_kb = 0

    for i in success_conditions:
        size = i.get("size_kb", 0)
        total_data_size_kb += size

    log_data = {
        "run_id": timestamp,
        "start_time": datetime.utcnow().isoformat() + "Z",
        "end_time": datetime.utcnow().isoformat() + "Z",
        "duration_seconds": round(time.time() - run_start, 2),
        "total_conditions": total_conditions,
        "success_conditions_count": success_count,
        "failed_conditions_count": failed_count,
        "success_conditions": success_conditions,
        "failed_conditions": failed_conditions,
        "total_data_size_kb": round(total_data_size_kb, 2),
        "bucket_path": bucket_path,
        "bucket_name": bucket.name,
        "status": "completed" if failed_count == 0 else "partial"
    }

    log_path = f"genes/logs/run_{timestamp}.json"
    blob = bucket.blob(log_path)
    blob.upload_from_string(
        json.dumps(log_data, indent=2, ensure_ascii=False),
        content_type="application/json"
    )
    
    return log_path
