import os
import json
import logging
import google.generativeai as genai
from PIL import Image
from dotenv import load_dotenv
from prompts.gemini_prompts import (
    DRESS_ANALYSIS_PROMPT,
    WARDROBE_MATCHING_PROMPT,
    OUTFIT_RECOMMENDATION_PROMPT
)

load_dotenv()

# Setup basic logging
logger = logging.getLogger(__name__)

def _get_client():
    if not os.environ.get("GEMINI_API_KEY"):
        raise ValueError("GEMINI_API_KEY is not configured.")
    genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
    return genai

def _clean_json_response(text: str) -> str:
    """Removes markdown backticks and formatting from LLM response to parse JSON safely."""
    text = text.strip()
    if text.startswith("```json"):
        text = text[7:]
    elif text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    return text.strip()

def analyze_dress_image(image_path: str) -> dict:
    """
    Sends the dress image to Gemini Vision API and returns a structured JSON metadata.
    """
    try:
        client = _get_client()

        # Load image using PIL
        img = Image.open(image_path)

        # Call API
        model = genai.GenerativeModel('gemini-2.5-flash')
        response = model.generate_content([DRESS_ANALYSIS_PROMPT, img])
        
        if not response.text:
            raise ValueError("Empty response from Gemini API.")
            
        json_str = _clean_json_response(response.text)
        data = json.loads(json_str)
        return data

    except Exception as e:
        logger.error(f"Error in analyze_dress_image: {e}")
        # Return a safe fallback schema in case of total failure
        return {
            "category": "upper",
            "style": "casual",
            "primary_color": "black",
            "secondary_colors": [],
            "fit": "regular",
            "pattern": "solid",
            "occasion": ["casual"],
            "season": ["all"],
            "gender": "unisex",
            "confidence": 0.0,
            "description": "Failed to analyze image."
        }

def suggest_matching_items(query: str, wardrobe_items: list) -> list:
    """
    Given a user's text query and a list of wardrobe JSON dictionaries, 
    ask Gemini to pick the top 3 items matching the query.
    Returns a list of URLs.
    """
    try:
        client = _get_client()
        
        # Prepare wardrobe data as a JSON string to pass in prompt
        wardrobe_json_str = json.dumps(wardrobe_items, indent=2)
        
        prompt = WARDROBE_MATCHING_PROMPT.format(
            query=query,
            wardrobe_items=wardrobe_json_str
        )
        
        model = genai.GenerativeModel('gemini-2.5-flash')
        response = model.generate_content(prompt)
        
        if not response.text:
            return []
            
        json_str = _clean_json_response(response.text)
        urls = json.loads(json_str)
        if isinstance(urls, list):
            return urls[:3]
        return []
    except Exception as e:
        logger.error(f"Error in suggest_matching_items: {e}")
        return []

def generate_outfit_recommendation(context: dict) -> dict:
    """
    Given a context (e.g., weather, occasion), generate an outfit recommendation.
    """
    try:
        client = _get_client()
        context_str = json.dumps(context, indent=2)
        prompt = OUTFIT_RECOMMENDATION_PROMPT.format(context=context_str)
        
        model = genai.GenerativeModel('gemini-2.5-flash')
        response = model.generate_content(prompt)
        json_str = _clean_json_response(response.text)
        return json.loads(json_str)
    except Exception as e:
        logger.error(f"Error in generate_outfit_recommendation: {e}")
        return {"recommendation": "Unable to generate recommendation.", "suggested_items": []}
