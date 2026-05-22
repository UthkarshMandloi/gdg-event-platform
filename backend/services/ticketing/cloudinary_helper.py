import cloudinary
import cloudinary.uploader
import os

class CloudinaryHelper:
    def __init__(self, config):
        try:
            cloudinary.config(
                cloud_name=config.cloudinary_cloud_name,
                api_key=config.cloudinary_api_key,
                api_secret=config.cloudinary_api_secret,
                secure=True
            )
        except Exception as e:
            raise Exception(f"Cloudinary Configuration Failed: {e}")

    def upload_file(self, file_obj, folder_name="event_uploads", public_id=None):
        try:
            # Force PDFs to upload as raw files so the browser downloads/opens them correctly
            is_pdf = file_obj.name.lower().endswith('.pdf')
            res_type = "raw" if is_pdf else "auto"

            response = cloudinary.uploader.upload(
                file_obj, 
                folder=folder_name,
                public_id=public_id,
                resource_type=res_type 
            )
            
            # If it's a raw file (PDF), we make sure it returns the exact secure URL
            return response.get('secure_url')
        except Exception as e:
            print(f"[Cloudinary] Upload failed: {e}")
            return None