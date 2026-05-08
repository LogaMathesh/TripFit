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
  "https://res.cloudinary.com/example/image/upload/file1.jpg",
  "https://res.cloudinary.com/example/image/upload/file2.jpg"
]
Do not include any other text, markdown, or explanations. Only the raw JSON array.
"""

OUTFIT_RECOMMENDATION_PROMPT = """
You are a personal AI stylist. Please provide outfit recommendations based on the following context:
Context:
{context}

Provide your recommendations strictly as a JSON object containing a "recommendation" field with a string explanation, and a "suggested_items" array of strings.
"""

# Recommendation Engine V2.1
SMART_FASHION_SEARCH_PROMPT = """
You are an expert personal shopper and Google Shopping query strategist.

Inputs:
User Profile:
{user_profile}

Summarized Likes:
{summarized_likes}

Summarized Dislikes:
{summarized_dislikes}

Current Occasion Expansion:
{occasion_context}

Current User Idea:
{idea}

Generate ONE diversified Google Shopping search query.

Balance the query intent as:
- 50% current occasion relevance
- 30% user preference alignment
- 20% exploration / novelty

Rules:
- The query must be concrete and Google Shopping friendly.
- The query must include 4-6 compatible clothing categories across at least 3 clusters when the current idea is broad, such as party, rooftop, date, brunch, vacation, wedding, office, or formal.
- Use the Current Occasion Expansion as the main source of categories and clusters.
- Treat cluster_priority penalties as hard guidance. If ethnic is penalized, ethnic history is weak context only.
- Use an OR-separated query style so Google Shopping can return varied product categories.
- Good query style: blazer OR satin shirt OR bomber jacket OR tailored trousers OR modern fusion
- Bad query style: blazer satin shirt bomber jacket kurta
- Prefer specific clothing categories, colors, materials, fits, and occasion terms over abstract style labels.
- Avoid repeatedly recommending the same style cluster.
- Include variety in clothing categories in the query itself, for example blazer, linen shirt, jacket, kurta, trousers, suit, dress, or modern alternative as appropriate.
- Include safe recommendations and modern alternatives.
- Avoid overfitting to historical likes.
- If user history strongly prefers one cluster, include it as only one part of the query, never as the main or only category unless the current idea explicitly asks for it.
- If the user liked kurta or ethnic before but the current idea is rooftop party, the query must still include blazer or jacket and shirt categories.
- HARD CONSTRAINT: For western or social occasions such as club, rooftop, party, beach, brunch, office, travel, resort, vacation, date, dinner, pub, lounge, or night out, historical ethnic preferences may contribute AT MOST ONE clothing category in the final query.
- HARD CONSTRAINT: For those western or social occasions, never use kurta, ethnic, traditional, or indo-western as primary_cluster unless the user explicitly asks for a traditional outfit.
- For western or social occasions, prioritize blazer, shirt, jacket, dress, co-ord, trousers, linen shirt, modern fusion, satin shirt, bomber jacket, and partywear.
- Traditional or ethnic style may appear only as one optional alternative for western or social occasions.
- Use negative keywords ONLY for strongly disliked features.
- Do not permanently ban disliked styles unless the dislike summary is very strong.
- Keep the query concise enough for Google Shopping.

Output STRICT JSON only:
{{
  "query": "...",
  "primary_cluster": "...",
  "secondary_clusters": ["...", "..."],
  "diversity_score": 0.0
}}

No markdown. No explanations. No extra keys.
"""
