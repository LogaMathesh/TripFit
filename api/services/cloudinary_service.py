import os
import cloudinary
import cloudinary.uploader

# Configure Cloudinary
# Ensure that these environment variables are set in the production environment
cloudinary.config(
    cloud_name=os.environ.get("CLOUDINARY_CLOUD_NAME"),
    api_key=os.environ.get("CLOUDINARY_API_KEY"),
    api_secret=os.environ.get("CLOUDINARY_API_SECRET"),
    secure=True
)

def upload_image_to_cloudinary(file_path):
    """
    Uploads a local image file to Cloudinary and returns the secure URL.
    """
    try:
        response = cloudinary.uploader.upload(
            file_path,
            folder=os.environ.get("CLOUDINARY_FOLDER", "my_dress_app"),
            resource_type="image",
            quality="auto:eco",
            fetch_format="auto",
            transformation=[
                {"width": 1200, "height": 1200, "crop": "limit"},
            ],
        )
        return response.get("secure_url")
    except Exception as e:
        print(f"Cloudinary upload error: {e}")
        return None
