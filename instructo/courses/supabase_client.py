from supabase import create_client
from django.conf import settings
import os

#All the code in this file was written without assistance

#method to create and return a Supabase client
def get_supabase_client():
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)

#method to upload a file to supabase storage
def upload_to_supabase(file_path: str, file_name: str) -> str:
    print("uploading to supabase")
    #get the supabase client
    supabase = get_supabase_client()

    #open the file in binary read mode
    with open(file_path, "rb") as file:
        #case the file is a pdf
        if file_name.lower().endswith(".pdf"):
            #upload the pdf with the right file_options
            res = supabase.storage.from_(settings.SUPABASE_BUCKET).upload(file_name, file.read(), file_options={"content-type": "application/pdf"})
        else:
            res = supabase.storage.from_(settings.SUPABASE_BUCKET).upload(file_name, file.read())
        print("res: ", res)

    #case there was an error - raise an exception
    if res.status_code != 200:
        print("error: ", res.content)
        raise Exception(f"Failed to upload the file: {res.json()}")

    #get the public url of the uploaded file
    public_url_res = supabase.storage.from_(settings.SUPABASE_BUCKET).get_public_url(file_name)
    print("Public url: ", public_url_res)

    #case there is no url - raise an error
    if not public_url_res:
        raise Exception(f"Failed to get the file URL for the uploaded file")
    
    #return the public url
    return public_url_res

#method to delete a file from supabase storage
def delete_from_supabase(file_url: str) -> None:
    #extract the name of the file from the url
    file_path = file_url.split("/")[-1].split("?")[0]
    print("file name: ", file_path)

    #get the supabase client
    supabase = get_supabase_client()

    #remove the file
    res = supabase.storage.from_(settings.SUPABASE_BUCKET).remove([file_path])


