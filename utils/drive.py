# utils/drive.py

import os
import cloudinary
import cloudinary.uploader
import streamlit as st

# Load from Hugging Face Secrets or .env
CLOUD_NAME = os.getenv("CLOUDINARY_CLOUD_NAME")
API_KEY = os.getenv("CLOUDINARY_API_KEY")
API_SECRET = os.getenv("CLOUDINARY_API_SECRET")

# Configure Cloudinary
cloudinary.config(
    cloud_name=CLOUD_NAME,
    api_key=API_KEY,
    api_secret=API_SECRET
)


def upload_file(file, issue_id):
    """
    Upload file to Cloudinary and return public URL
    """

    try:
        # Generate unique filename
        filename = f"{issue_id}_{file.name}"

        # Upload
        result = cloudinary.uploader.upload(
            file,
            public_id=filename,
            folder="ticketing_system",
            resource_type="auto"
        )

        return result.get("secure_url")

    except Exception as e:
        st.warning("Cloud upload failed, using local fallback")
        return save_locally(file, issue_id)


def save_locally(file, issue_id):
    """
    Fallback if Cloudinary fails (for local dev)
    """

    os.makedirs("uploads", exist_ok=True)
    file_path = f"uploads/{issue_id}_{file.name}"

    with open(file_path, "wb") as f:
        f.write(file.getbuffer())

    return file_path# Return drive_link if successful
