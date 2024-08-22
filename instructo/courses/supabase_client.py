from supabase import create_client
from django.conf import settings
import os

def get_supabase_client():
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)

def upload_to_supabase(file_path: str, file_name: str) -> str:
    print("uploading to supabase")
    supabase = get_supabase_client()

    with open(file_path, "rb") as file:
        if file_name.lower().endswith(".pdf"):
            print("it is a PDF FILE")
            res = supabase.storage.from_(settings.SUPABASE_BUCKET).upload(file_name, file.read(), file_options={"content-type": "application/pdf"})
        else:
            res = supabase.storage.from_(settings.SUPABASE_BUCKET).upload(file_name, file.read())
        print("res: ", res)

    if res.status_code != 200:
        print("error: ", res.content)
        raise Exception(f"Failed to upload the file: {res.json()}")

    public_url_res = supabase.storage.from_(settings.SUPABASE_BUCKET).get_public_url(file_name)
    print("Public url: ", public_url_res)

    if not public_url_res:
        raise Exception(f"Failed to get the file URL for the uploaded file")
    
    return public_url_res