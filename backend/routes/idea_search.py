from flask import Blueprint, request, jsonify
import google.generativeai as genai
from serpapi import GoogleSearch
from config import Config
from database import cur, conn

idea_search_bp = Blueprint('idea_search_bp', __name__)

@idea_search_bp.route('/search-ideas', methods=['POST'])
def search_ideas():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Invalid request'}), 400
        
    idea = data.get('idea')
    username = data.get('username')
    
    if not idea:
        return jsonify({'error': 'No idea provided'}), 400
        
    if not Config.GEMINI_API_KEY:
        return jsonify({'error': 'gemini_api_key_missing', 'message': 'Gemini API key is not configured in the backend .env file.'}), 500
        
    try:
        # 1. Fetch user profile context if username is provided
        profile_context = ""
        if username:
            cur.execute("SELECT gender, budget_level, sizes, style_preferences FROM user_profiles WHERE username = %s", (username,))
            row = cur.fetchone()
            if row:
                gender, budget, sizes, style = row
                profile_parts = []
                if gender: profile_parts.append(f"Gender: {gender}")
                if budget: profile_parts.append(f"Budget Level: {budget}")
                if sizes: profile_parts.append(f"Sizes: {sizes}")
                if style: profile_parts.append(f"Style Preferences: {style}")
                
                if profile_parts:
                    profile_context = "\nUser Profile Constraints:\n" + "\n".join(profile_parts) + "\nIncorporate these profile preferences into the search query if they make sense, but prioritize the user's explicit description."

        # 2. Prompt Gemini AI to generate a strong shopping query
        genai.configure(api_key=Config.GEMINI_API_KEY)
        model = genai.GenerativeModel('gemini-2.5-flash')
        prompt = f"""You are an expert personal shopper and SEO specialist. 
The user wants to find a specific outfit based on their description. 
Convert the following description of an outfit into exactly one highly optimized search query for Google Shopping. 
The query should focus on visual traits, style, color, pattern, and category. 
It should be concise, using keywords that yield the best product matches on an e-commerce search engine. 
Reply ONLY with the exact search query string. Do NOT include quotes, explanations, preambles, or any conversational text.
{profile_context}

User Description: {idea}
Search Query:"""
        
        response = model.generate_content(prompt)
        query = response.text.strip().replace('"', '')
        
        # 3. Save to search logs
        if username:
            try:
                cur.execute(
                    "INSERT INTO search_logs (username, raw_prompt, generated_query) VALUES (%s, %s, %s)",
                    (username, idea, query)
                )
                conn.commit()
            except Exception as e:
                conn.rollback()
                print(f"Failed to log search: {e}")

        # 4. Search SerpAPI using the AI generated query
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
        
        # 5. Clean up the payload before sending it to Frontend
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
