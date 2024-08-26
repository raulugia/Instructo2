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

#logger = logging.getLogger(__name__)
logger.remove()
logger.add(sys.stdout, format="{time} {level} {message}", level="INFO")

@shared_task
def upload_file_to_supabase(file_path, resource_id):
    logger.remove()
    logger.add(sys.stdout, format="{time} {level} {message}", level="INFO")
    logger.info("***********************WORKING WITH: {}", file_path)
    try:
        resource = Resource.objects.get(id=resource_id)
        logger.info("RESOURCE FOUND: {}", resource.title)

        file_name = f"{uuid.uuid4()}_{os.path.basename(file_path)}"
        logger.info("*************FILE NAME IN upload_file_to_supabase: {}", file_name)


        resource_url = upload_to_supabase(file_path, file_name)

        #encode url spaces (spaces will be replaced with %20)- avoid encoding colons and slashes
        encoded_url = urllib.parse.quote(resource_url, safe=":/")

        if "thumbnail" in os.path.basename(file_path).lower():
            logger.info("CASE THUMBNAIL: {}", encoded_url)
            resource.thumbnail = resource_url
        else:
            logger.info("CASE NOT THUMBNAIL: {}", encoded_url)
            resource.file = resource_url

        logger.info("RESOURCE FILE: {}", resource.file)
        resource.save()
    except Resource.DoesNotExist:
        logger.error("Resource with id {} does not exist", resource_id)
    except Exception as e:
        logger.error("Failed to upload: {}", str(e))
    finally:
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception as e:
            logger.error("Failed to remove file in upload_file_to_supabase: {}", str(e))

@shared_task
def create_thumbnail_and_upload(file_path, resource_id):
    logger.remove()
    logger.add(sys.stdout, format="{time} {level} {message}", level="INFO")
    logger.info("HERE in create_thumbnail_and_upload")
    #print("HERE")

    try:
        logger.info("creating thumbnail")
        resource = Resource.objects.get(id=resource_id)

        img = Image.open(file_path)
       
        max_width = 200
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

        original_file_url = upload_file_to_supabase(file_path, resource.id)
        logger.info("**********************ORIGINAL FILE URL: {}", original_file_url)
        thumbnail_url = upload_file_to_supabase(thumbnail_path, resource.id)
        logger.info("****************THUMBNAIL URL: {}", thumbnail_url)

    except Resource.DoesNotExist:
        logger.error("Resource with id {} does not exist", resource_id)
    except Exception as e:
        logger.error("Failed to create thumbnail and upload: {}", str(e))
    finally:
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
            if os.path.exists(thumbnail_path):
                os.remove(thumbnail_path)
        except Exception as e:
            logger.error("Failed to remove file: {}", str(e))
