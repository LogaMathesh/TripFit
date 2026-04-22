import os
os.environ["TF_USE_LEGACY_KERAS"] = "1"
os.environ["PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"] = "python"
from dotenv import load_dotenv
import os

# Explicitly load the local .env to absolutely guarantee it catches your GEMINI_API_KEY
env_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path=env_path)


class Config:
    UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploaded_images')
    MAX_CONTENT_LENGTH = 8 * 1024 * 1024  # 8 MB upload limit
    SERPAPI_KEY = os.environ.get("SERPAPI_KEY")
    GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# Create upload folder if it doesn't exist
os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
