from firebase_admin import storage as s
 
def save_conditions(data, bucket_name, file_name): 
    b = s.bucket(bucket_name) 
    o = b.blob(file_name) 
    o.upload_from_string(data, content_type="application/json")