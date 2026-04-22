from flask import Blueprint, request, jsonify
import google.generativeai as genai
from serpapi import GoogleSearch
from config import Config

idea_search_bp = Blueprint('idea_search_bp', __name__)

@idea_search_bp.route('/search-ideas', methods=['POST'])
def search_ideas():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Invalid request'}), 400
        
    idea = data.get('idea')
    
    if not idea:
        return jsonify({'error': 'No idea provided'}), 400
        
    if not Config.GEMINI_API_KEY:
        return jsonify({'error': 'gemini_api_key_missing', 'message': 'Gemini API key is not configured in the backend .env file.'}), 500
        
    try:
        # 1. Prompt Gemini AI to generate a strong shopping query
        genai.configure(api_key=Config.GEMINI_API_KEY)
        model = genai.GenerativeModel('gemini-flash-latest')
        prompt = f"Convert the following description of a dress into exactly one highly optimized search query for Google Shopping (focusing on visual dress traits, style, and category). Reply ONLY with the concise search query string. Do not include quotes or conversational text.\n\nDescription: {idea}"
        
        response = model.generate_content(prompt)
        query = response.text.strip().replace('"', '')
        
        # 2. Search SerpAPI using the AI generated query
        if not Config.SERPAPI_KEY:
            return jsonify({'error': 'SerpAPI key not configured in .env file'}), 500
            
        params = {
            "engine": "google_shopping",
            "q": query,
            "api_key": Config.SERPAPI_KEY
        }
        
        search = GoogleSearch(params)
        results_dict = search.get_dict()
        
        shopping_results = results_dict.get("shopping_results", [])
        
        # 3. Clean up the payload before sending it to Frontend
        clean_results = []
        for item in shopping_results[:16]: # Return top 16 items
            link = item.get("link") or item.get("product_link") or item.get("product_page_url")
            clean_results.append({
                "title": item.get("title", 'Unknown Dress'),
                "price": item.get("price", ''),
                "link": link,
                "thumbnail": item.get("thumbnail", ''),
                "source": item.get("source", '')
            })
            
        return jsonify({
            'query_used': query,
            'results': clean_results
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Idea search pipeline failed', 'details': str(e)}), 500
