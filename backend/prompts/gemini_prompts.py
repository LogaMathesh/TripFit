import json

# JSON Schema definition for dress analysis to enforce structure
DRESS_ANALYSIS_SCHEMA = {
    "type": "object",
    "properties": {
        "category": {"type": "string"},
        "style": {"type": "string"},
        "primary_color": {"type": "string"},
        "secondary_colors": {"type": "array", "items": {"type": "string"}},
        "fit": {"type": "string"},
        "pattern": {"type": "string"},
        "occasion": {"type": "array", "items": {"type": "string"}},
        "season": {"type": "array", "items": {"type": "string"}},
        "gender": {"type": "string"},
        "confidence": {"type": "number"},
        "description": {"type": "string"}
    },
    "required": [
        "category", "style", "primary_color", "secondary_colors", "fit",
        "pattern", "occasion", "season", "gender", "confidence", "description"
    ]
}

DRESS_ANALYSIS_PROMPT = f"""
You are an expert AI fashion assistant. Please analyze the provided clothing image.
Return your findings strictly as a JSON object matching the following schema.
Do not include any markdown formatting like ```json or any other text outside the JSON object.

Schema:
{json.dumps(DRESS_ANALYSIS_SCHEMA, indent=2)}

Guidelines:
- category: e.g., 'upper', 'lower', 'full', 'shoes', 'accessories'
- style: e.g., 'casual', 'formal', 'streetwear', 'traditional', 'sportswear', 'vintage'
- primary_color: the dominant color of the item
- fit: e.g., 'slim', 'regular', 'loose', 'oversized'
- description: A short, compelling description of the item.
"""

WARDROBE_MATCHING_PROMPT = """
You are a personal AI stylist. The user is asking to find an item in their wardrobe.
Below is the user's query and a list of JSON objects representing their wardrobe items.

Query: "{query}"

Wardrobe Items:
{wardrobe_items}

Please find the top 3 best matching items for the user's query.
Return your response STRICTLY as a JSON array containing ONLY the string URLs (the "url" field) of the top 3 matches. Order them from best match to worst match.
Example valid response:
[
  "http://localhost:5000/image/file1.jpg",
  "http://localhost:5000/image/file2.jpg"
]
Do not include any other text, markdown, or explanations. Only the raw JSON array.
"""

OUTFIT_RECOMMENDATION_PROMPT = """
You are a personal AI stylist. Please provide outfit recommendations based on the following context:
Context:
{context}

Provide your recommendations strictly as a JSON object containing a "recommendation" field with a string explanation, and a "suggested_items" array of strings.
"""
