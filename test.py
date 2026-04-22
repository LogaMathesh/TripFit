from serpapi import GoogleSearch
params = {
    "engine": "google_shopping",
    "q": "red dress for women party",
    "api_key": "435acae4d65c57ff252b7322c193b2ee5b7acb7c9b49f3e9222f2944a3b36deb"
}

search = GoogleSearch(params)
results = search.get_dict()

for item in results.get("shopping_results", []):
    print("Title:", item.get("title"))
    print("Price:", item.get("price"))
    
    # Try multiple possible keys
    link = item.get("link") or item.get("product_link") or item.get("product_page_url")
    print("Link:", link)
    
    print("Thumbnail:", item.get("thumbnail"))
    print("------")