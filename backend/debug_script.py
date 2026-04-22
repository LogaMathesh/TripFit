import google.generativeai as genai
from config import Config
import json

try:
    genai.configure(api_key=Config.GEMINI_API_KEY)
    models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
    with open('error_log.txt', 'w') as f:
        f.write(json.dumps(models))
except Exception as e:
    with open('error_log.txt', 'w') as f:
        f.write(str(e))
