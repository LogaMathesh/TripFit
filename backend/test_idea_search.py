import os
from dotenv import load_dotenv
import google.generativeai as genai
from serpapi import GoogleSearch

load_dotenv()

def test_pipeline():
    idea = "A flowy emerald green dress perfect for a winter formal gala"
    print("Testing Gemini...")
    try:
        genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
        model = genai.GenerativeModel('gemini-2.5-flash')
        prompt = f"Convert the following description of a dress into exactly one highly optimized search query for Google Shopping (focusing on visual dress traits, style, and category). Reply ONLY with the concise search query string. Do not include quotes or conversational text.\n\nDescription: {idea}"
        
        response = model.generate_content(prompt)
        query = response.text.strip().replace('"', '')
        print("Gemini Query:", query)
    except Exception as e:
        print("Gemini Failed:", e)
        return

    print("Testing SerpAPI...")
    try:
        params = {
            "engine": "google_shopping",
            "q": query,
            "api_key": os.environ.get("SERPAPI_KEY")
        }
        search = GoogleSearch(params)
        results_dict = search.get_dict()
        
        shopping_results = results_dict.get("shopping_results", [])
        print("SerpAPI Success. Items:", len(shopping_results))
        if len(shopping_results) > 0:
            print("First item:", shopping_results[0])
        elif "error" in results_dict:
            print("SerpAPI returned an error in dict:", results_dict["error"])
    except Exception as e:
        print("SerpAPI Failed:", e)

if __name__ == '__main__':
    test_pipeline()
