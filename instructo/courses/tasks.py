import os
from .models import Resource
from celery import shared_task
from PIL import Image
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import requests
from .supabase_client import upload_to_supabase
import logging
from loguru import logger
import sys
import uuid
import urllib.parse

#All the code in this file was written without assistance

#remove the default logger config and add a new one 
logger.remove()
logger.add(sys.stdout, format="{time} {level} {message}", level="INFO")

#task to upload resource to supabase storage and update and save Resource instance
@shared_task
def upload_file_to_supabase(file_path, resource_id):
    #remove the default logger config and add a new one 
    logger.remove()
    logger.add(sys.stdout, format="{time} {level} {message}", level="INFO")
    
    #log the current file path being processed
    logger.info("WORKING WITH: {}", file_path)

    try:
        #fetch the resource with the provided id
        resource = Resource.objects.get(id=resource_id)

        #log the resource title
        logger.info("RESOURCE FOUND: {}", resource.title)

        #generate a unique file name - avoid errors with supabase storage as duplicated names are not allowed
        file_name = f"{uuid.uuid4()}_{os.path.basename(file_path)}"
        #log the file name
        logger.info("FILE NAME IN upload_file_to_supabase: {}", file_name)

        #upload the file to supabase and store the public url
        resource_url = upload_to_supabase(file_path, file_name)

        #encode url spaces (spaces will be replaced with %20)- avoid encoding colons and slashes
        encoded_url = urllib.parse.quote(resource_url, safe=":/")

        #case thumbnail 
        if "thumbnail" in os.path.basename(file_path).lower():
            #log the encoded url
            logger.info("CASE THUMBNAIL: {}", encoded_url)
            #set the resource's thumbnail (url)
            resource.thumbnail = resource_url
        #case no thumbnail
        else:
            #log the encoded url
            logger.info("CASE NOT THUMBNAIL: {}", encoded_url)
            #set the resource's file (url)
            resource.file = resource_url

        #save the resource
        resource.save()
    
    #log errors
    except Resource.DoesNotExist:
        logger.error("Resource with id {} does not exist", resource_id)
    except Exception as e:
        logger.error("Failed to upload: {}", str(e))
    finally:
        try:
            #remove the file from the local file system
            if os.path.exists(file_path):
                os.remove(file_path)
        #log error
        except Exception as e:
            logger.error("Failed to remove file in upload_file_to_supabase: {}", str(e))


#task to create a thumbnail
@shared_task
def create_thumbnail_and_upload(file_path, resource_id):
    #remove the default logger config and add a new one
    logger.remove()
    logger.add(sys.stdout, format="{time} {level} {message}", level="INFO")
    
    #log to know the task is running
    logger.info("In create_thumbnail_and_upload")

    try:
        logger.info("creating thumbnail")
        #fetch resource based on the provided id
        resource = Resource.objects.get(id=resource_id)

        #open the image file with PIL
        img = Image.open(file_path)
       
        #set the max width of the thumbnail
        max_width = 200
        #calculate the scaling factor
        x_scale_factor = img.size[0] / max_width

        #create the thumbnail name
        thumbnail_name = f"thumbnail_{os.path.basename(file_path)}"
        #save thumbnail in a temporary file
        thumbnail_path = os.path.join("/tmp", thumbnail_name)
        logger.info("thumbnail path: {}", thumbnail_path)

        #resize the original image
        thumbnail = img.resize((max_width, int(img.size[1] / x_scale_factor)))
        #save the thumbnail
        thumbnail.save(thumbnail_path)

        #upload the original file to supabase storage and store the public url
        original_file_url = upload_file_to_supabase(file_path, resource.id)
        logger.info("ORIGINAL FILE URL: {}", original_file_url)

        #upload the thumbnail to supabase storage and store the public url
        thumbnail_url = upload_file_to_supabase(thumbnail_path, resource.id)
        logger.info("THUMBNAIL URL: {}", thumbnail_url)

    #log errors
    except Resource.DoesNotExist:
        logger.error("Resource with id {} does not exist", resource_id)
    except Exception as e:
        logger.error("Failed to create thumbnail and upload: {}", str(e))
    finally:
        try:
            #delete the original/thumbnail file from the local file system
            if os.path.exists(file_path):
                os.remove(file_path)
            if os.path.exists(thumbnail_path):
                os.remove(thumbnail_path)
        except Exception as e:
            logger.error("Failed to remove file: {}", str(e))
