from flask import Blueprint, request, jsonify
import json
import re
from collections import Counter, defaultdict
from urllib.parse import parse_qsl, quote, urlencode, urlparse, urlunparse
import google.generativeai as genai
from config import Config
from database import get_connection
from prompts.gemini_prompts import SMART_FASHION_SEARCH_PROMPT

try:
    from serpapi import GoogleSearch
except ImportError:
    GoogleSearch = None

idea_search_bp = Blueprint('idea_search_bp', __name__)

# Amazon Affiliate Integration
AMAZON_AFFILIATE_TAG = "stylefinder00-21"
AMAZON_DOMAINS = {
    "amazon.in",
    "amazon.com",
    "amazon.co.uk",
    "amazon.ae",
    "amazon.ca",
    "amazon.de",
    "amazon.fr",
    "amazon.it",
    "amazon.es",
    "amazon.co.jp"
}

# Recommendation Engine V2
FASHION_KEYWORDS = {
    "shirt", "tshirt", "tee", "kurta", "kurti", "blazer", "suit", "linen",
    "cotton", "formal", "casual", "traditional", "ethnic", "dress", "gown",
    "saree", "lehenga", "jacket", "bomber", "denim", "jeans", "trouser",
    "trousers", "pants", "chinos", "sneakers", "loafers", "heels", "boots",
    "skirt", "top", "hoodie", "sweater", "cardigan", "coat", "waistcoat",
    "vest", "polo", "oversized", "slim", "regular", "relaxed", "party",
    "wedding", "office", "work", "date", "rooftop", "brunch", "vacation",
    "streetwear", "smart", "modern", "minimal", "vintage", "floral",
    "printed", "solid", "striped", "checked", "embroidered", "silk", "satin",
    "velvet", "leather", "wool", "chiffon", "georgette", "co-ord", "coord",
    "club", "night", "pub", "lounge", "beach", "resort", "summer", "relaxed",
    "temple", "festival", "fusion", "partywear", "travel", "sherwani",
    "shorts", "sandals"
}

OCCASION_EXPANSIONS = {
    "club": {
        "occasion_clusters": ["modern", "formal", "partywear", "smart_casual"],
        "category_pool": ["blazer", "satin shirt", "bomber jacket", "co-ord", "dress", "tailored trousers"]
    },
    "night": {
        "occasion_clusters": ["modern", "formal", "partywear", "smart_casual"],
        "category_pool": ["blazer", "satin shirt", "bomber jacket", "co-ord", "dress", "tailored trousers"]
    },
    "pub": {
        "occasion_clusters": ["modern", "formal", "partywear", "smart_casual"],
        "category_pool": ["blazer", "satin shirt", "bomber jacket", "co-ord", "dress", "tailored trousers"]
    },
    "lounge": {
        "occasion_clusters": ["modern", "formal", "partywear", "smart_casual"],
        "category_pool": ["blazer", "satin shirt", "bomber jacket", "co-ord", "dress", "tailored trousers"]
    },
    "rooftop": {
        "occasion_clusters": ["smart_casual", "formal", "modern", "partywear"],
        "category_pool": ["blazer", "linen shirt", "party jacket", "satin shirt", "tailored trousers", "modern fusion"]
    },
    "party": {
        "occasion_clusters": ["modern", "formal", "partywear", "smart_casual"],
        "category_pool": ["blazer", "satin shirt", "linen shirt", "bomber jacket", "co-ord", "dress"]
    },
    "wedding": {
        "occasion_clusters": ["formal", "ethnic", "dressy", "smart_casual"],
        "category_pool": ["suit", "blazer", "sherwani", "kurta", "dress", "fusion"]
    },
    "office": {
        "occasion_clusters": ["formal", "smart_casual", "minimal"],
        "category_pool": ["blazer", "formal shirt", "chinos", "tailored trousers", "loafers"]
    },
    "work": {
        "occasion_clusters": ["formal", "smart_casual", "minimal"],
        "category_pool": ["blazer", "formal shirt", "chinos", "tailored trousers", "loafers"]
    },
    "beach": {
        "occasion_clusters": ["casual", "summer", "relaxed"],
        "category_pool": ["linen shirt", "cotton shirt", "relaxed trousers", "shorts", "sundress", "sandals"]
    },
    "resort": {
        "occasion_clusters": ["casual", "summer", "relaxed"],
        "category_pool": ["linen shirt", "cotton shirt", "relaxed trousers", "shorts", "sundress", "sandals"]
    },
    "vacation": {
        "occasion_clusters": ["casual", "summer", "relaxed"],
        "category_pool": ["linen shirt", "cotton shirt", "relaxed trousers", "shorts", "sundress", "sandals"]
    },
    "brunch": {
        "occasion_clusters": ["smart_casual", "casual", "modern"],
        "category_pool": ["linen shirt", "polo", "chinos", "light jacket", "sneakers"]
    },
    "date": {
        "occasion_clusters": ["smart_casual", "modern", "formal"],
        "category_pool": ["blazer", "linen shirt", "jacket", "dark jeans", "loafers"]
    },
    "dinner": {
        "occasion_clusters": ["smart_casual", "formal", "modern"],
        "category_pool": ["blazer", "satin shirt", "linen shirt", "jacket", "tailored trousers"]
    },
    "temple": {
        "occasion_clusters": ["ethnic", "traditional"],
        "category_pool": ["kurta", "saree", "salwar suit", "traditional dress", "ethnic sandals"]
    },
    "festival": {
        "occasion_clusters": ["ethnic", "traditional"],
        "category_pool": ["kurta", "saree", "lehenga", "sherwani", "traditional dress"]
    }
}

CORE_CLUSTERS = ["ethnic", "formal", "modern", "casual", "smart_casual"]
ETHNIC_KEYWORDS = {"kurta", "kurti", "saree", "lehenga", "ethnic", "traditional", "embroidered", "sherwani"}

COLOR_KEYWORDS = {
    "black", "white", "blue", "navy", "green", "red", "maroon", "pink",
    "purple", "lavender", "yellow", "orange", "brown", "beige", "cream",
    "grey", "gray", "silver", "gold", "emerald", "olive", "teal", "tan",
    "khaki", "burgundy", "coral", "ivory", "pastel", "monochrome"
}

INTERACTION_WEIGHTS = {
    "save": 5,
    "like": 3,
    "dislike": -2
}


# Amazon Affiliate Integration
def is_amazon_link(link):
    try:
        parsed = urlparse(link or "")
        hostname = (parsed.hostname or "").lower()
        return any(hostname == domain or hostname.endswith(f".{domain}") for domain in AMAZON_DOMAINS)
    except Exception:
        return False


# Amazon Affiliate Integration
def add_amazon_affiliate(link):
    try:
        if not link or not is_amazon_link(link):
            return link

        parsed = urlparse(link)
        query_params = parse_qsl(parsed.query, keep_blank_values=True)
        query_params = [(key, value) for key, value in query_params if key.lower() != "tag"]
        query_params.append(("tag", AMAZON_AFFILIATE_TAG))

        return urlunparse((
            parsed.scheme,
            parsed.netloc,
            parsed.path,
            parsed.params,
            urlencode(query_params, doseq=True),
            parsed.fragment
        ))
    except Exception:
        return link


# Amazon Affiliate Integration
def build_amazon_search_link(title):
    try:
        if not title:
            return ""

        encoded_title = quote(str(title).strip())
        return f"https://www.amazon.in/s?k={encoded_title}&tag={AMAZON_AFFILIATE_TAG}"
    except Exception:
        return ""


# Direct Merchant Link Resolver
def resolve_direct_product_link(item):
    try:
        original_link = item.get("link") or item.get("product_link") or item.get("product_page_url") or ""
        source = (item.get("source") or "").lower()
        title = item.get("title") or ""

        if "amazon" in source:
            amazon_search_link = build_amazon_search_link(title)
            return amazon_search_link

        merchant_link = item.get("merchant_link") or item.get("seller_link") or ""
        if is_amazon_link(merchant_link):
            return add_amazon_affiliate(merchant_link)

        product_link = item.get("product_link") or item.get("product_page_url") or ""
        if is_amazon_link(product_link):
            return add_amazon_affiliate(product_link)

        if is_amazon_link(original_link):
            return add_amazon_affiliate(original_link)

        return original_link
    except Exception:
        return item.get("link") or item.get("product_link") or item.get("product_page_url") or ""


# Recommendation Engine V2
def extract_keywords(text):
    if not text:
        return []

    normalized = text.lower().replace("-", " ")
    words = re.findall(r"[a-z0-9]+", normalized)
    keywords = []
    for word in words:
        if word in FASHION_KEYWORDS or word in COLOR_KEYWORDS:
            keywords.append(word)
    return keywords


# Recommendation Engine V2
def infer_cluster(title):
    keywords = set(extract_keywords(title))
    text = (title or "").lower()

    if keywords & {"kurta", "kurti", "saree", "lehenga", "ethnic", "traditional", "embroidered"}:
        return "ethnic"
    if keywords & {"partywear", "satin", "co-ord", "coord"} or "co ord" in text:
        return "partywear"
    if keywords & {"blazer", "suit", "formal", "office", "work", "waistcoat"}:
        return "formal"
    if keywords & {"shirt", "linen", "polo", "chinos", "trouser", "trousers", "smart"}:
        return "smart_casual"
    if keywords & {"jacket", "bomber", "leather", "streetwear", "modern", "hoodie", "oversized"}:
        return "modern"
    if keywords & {"sneakers", "denim", "jeans", "tee", "tshirt", "casual", "summer", "relaxed", "shorts", "sandals"}:
        return "casual"
    if keywords & {"dress", "gown", "skirt", "top", "heels", "satin", "silk"}:
        return "dressy"
    return "general"


# Recommendation Engine V2.1
def get_occasion_cluster_priorities(idea):
    tokens = set(re.findall(r"[a-z0-9]+", (idea or "").lower()))
    joined = " ".join(tokens)

    if tokens & {"club", "night", "pub", "lounge"}:
        return {
            "type": "club",
            "boosts": {"modern": 1.45, "formal": 1.25, "partywear": 1.5, "smart_casual": 1.15},
            "penalties": {"ethnic": 0.2},
            "is_ethnic_occasion": False
        }
    if tokens & {"rooftop", "date", "dinner"}:
        return {
            "type": "rooftop",
            "boosts": {"smart_casual": 1.45, "formal": 1.3, "modern": 1.25, "partywear": 1.2},
            "penalties": {"ethnic": 0.35},
            "is_ethnic_occasion": False
        }
    if "party" in tokens:
        return {
            "type": "party",
            "boosts": {"modern": 1.35, "formal": 1.25, "partywear": 1.45, "smart_casual": 1.15},
            "penalties": {"ethnic": 0.3},
            "is_ethnic_occasion": False
        }
    if tokens & {"beach", "resort", "vacation", "travel"}:
        return {
            "type": "beach",
            "boosts": {"casual": 1.55, "summer": 1.45, "relaxed": 1.4, "smart_casual": 1.1},
            "penalties": {"ethnic": 0.15, "formal": 0.55},
            "is_ethnic_occasion": False
        }
    if tokens & {"office", "work"}:
        return {
            "type": "office",
            "boosts": {"formal": 1.5, "minimal": 1.35, "smart_casual": 1.25},
            "penalties": {"ethnic": 0.45, "partywear": 0.6},
            "is_ethnic_occasion": False
        }
    if tokens & {"temple", "festival"}:
        return {
            "type": "temple",
            "boosts": {"ethnic": 1.5, "traditional": 1.45},
            "penalties": {"partywear": 0.55, "modern": 0.75},
            "is_ethnic_occasion": True
        }
    if "wedding" in tokens:
        return {
            "type": "wedding",
            "boosts": {"ethnic": 1.15, "formal": 1.15, "fusion": 1.2, "dressy": 1.1},
            "penalties": {},
            "is_ethnic_occasion": True
        }

    return {
        "type": "general",
        "boosts": {"smart_casual": 1.15, "modern": 1.1, "formal": 1.05},
        "penalties": {"ethnic": 0.65} if "party" in joined or "brunch" in joined else {},
        "is_ethnic_occasion": False
    }


# Recommendation Engine V2.1
def apply_occasion_priority_to_clusters(cluster_scores, occasion_priority):
    adjusted_scores = dict(cluster_scores or {})
    for cluster, multiplier in occasion_priority.get("boosts", {}).items():
        adjusted_scores[cluster] = adjusted_scores.get(cluster, 0.7) * multiplier
    for cluster, multiplier in occasion_priority.get("penalties", {}).items():
        adjusted_scores[cluster] = adjusted_scores.get(cluster, 0.7) * multiplier
    return adjusted_scores


# Recommendation Engine V2
def build_occasion_context(idea):
    tokens = set(re.findall(r"[a-z0-9]+", (idea or "").lower()))
    clusters = []
    categories = []

    for trigger, expansion in OCCASION_EXPANSIONS.items():
        if trigger in tokens:
            clusters.extend(expansion["occasion_clusters"])
            categories.extend(expansion["category_pool"])

    if not clusters:
        clusters = ["smart_casual", "formal", "modern", "casual"]
    if not categories:
        categories = ["blazer", "shirt", "jacket", "trousers", "modern alternative"]

    return {
        "occasion_clusters": list(dict.fromkeys(clusters))[:5],
        "category_pool": list(dict.fromkeys(categories))[:7]
    }


# Recommendation Engine V2.1
def normalize_cluster_scores(cluster_counter):
    if not cluster_counter:
        return {}

    scores = {cluster: float(score) for cluster, score in cluster_counter.items() if score > 0}
    for cluster in CORE_CLUSTERS:
        scores.setdefault(cluster, 0.7)

    ordered = sorted(scores.items(), key=lambda item: item[1], reverse=True)
    if len(ordered) > 1:
        top_cluster, top_score = ordered[0]
        second_score = ordered[1][1]
        max_top_score = max(0.7, second_score * 2)
        scores[top_cluster] = min(top_score, max_top_score)

    second_reference = sorted(scores.values(), reverse=True)[1] if len(scores) > 1 else 1.0
    second_reference = max(second_reference, 0.1)
    normalized = {
        cluster: round(min(score / second_reference, 2.0), 2)
        for cluster, score in scores.items()
        if score > 0
    }

    return dict(sorted(normalized.items(), key=lambda item: item[1], reverse=True)[:6])


# Recommendation Engine V2.1
def summarize_interactions(interactions, occasion_priority=None):
    summary = {
        "liked_keywords": [],
        "liked_clusters": {},
        "liked_colors": [],
        "disliked_keywords": [],
        "disliked_clusters": [],
        "recent_shift": []
    }

    try:
        positive_keywords = Counter()
        positive_clusters = Counter()
        positive_colors = Counter()
        negative_keywords = Counter()
        negative_clusters = Counter()
        recent_signal = Counter()

        for index, row in enumerate(interactions or []):
            title = row[0] or ""
            interaction_type = row[1] or ""
            base_weight = INTERACTION_WEIGHTS.get(interaction_type, 0)
            if not base_weight:
                continue

            recency_multiplier = max(0.35, 1.0 - (index * 0.045))
            weighted_value = base_weight * recency_multiplier
            keywords = extract_keywords(title)
            cluster = infer_cluster(title)

            if weighted_value > 0:
                positive_clusters[cluster] += weighted_value
                recent_signal[cluster] += weighted_value
                for keyword in keywords:
                    positive_keywords[keyword] += weighted_value
                    recent_signal[keyword] += weighted_value
                    if keyword in COLOR_KEYWORDS:
                        positive_colors[keyword] += weighted_value
            else:
                negative_clusters[cluster] += abs(weighted_value)
                for keyword in keywords:
                    negative_keywords[keyword] += abs(weighted_value)

        if occasion_priority:
            ethnic_keyword_multiplier = occasion_priority.get("penalties", {}).get("ethnic")
            if ethnic_keyword_multiplier and ethnic_keyword_multiplier < 1:
                for keyword in ETHNIC_KEYWORDS:
                    if keyword in positive_keywords:
                        positive_keywords[keyword] *= ethnic_keyword_multiplier

        normalized_clusters = normalize_cluster_scores(positive_clusters)
        if occasion_priority:
            normalized_clusters = apply_occasion_priority_to_clusters(normalized_clusters, occasion_priority)
            normalized_clusters = normalize_cluster_scores(Counter(normalized_clusters))

        summary["liked_keywords"] = [word for word, _ in positive_keywords.most_common(5)]
        summary["liked_clusters"] = normalized_clusters
        summary["liked_colors"] = [color for color, _ in positive_colors.most_common(5)]
        summary["disliked_keywords"] = [word for word, _ in negative_keywords.most_common(5)]
        summary["disliked_clusters"] = [cluster for cluster, _ in negative_clusters.most_common(5)]
        summary["recent_shift"] = [signal for signal, _ in recent_signal.most_common(5)]
    except Exception as e:
        print(f"Failed to summarize interactions: {e}")

    return summary


# Recommendation Engine V2
def build_debug_results():
    return [
        {"title": "Men's Slim Fit Party Blazer - Black", "price": "Debug", "link": "", "thumbnail": "", "source": "Local Debug"},
        {"title": "Men's Linen Shirt for Rooftop Party - White", "price": "Debug", "link": "", "thumbnail": "", "source": "Local Debug"},
        {"title": "Men's Modern Kurta Jacket Set - Ivory", "price": "Debug", "link": "", "thumbnail": "", "source": "Local Debug"},
        {"title": "Men's Bomber Jacket Evening Outfit - Navy", "price": "Debug", "link": "", "thumbnail": "", "source": "Local Debug"},
        {"title": "Men's Smart Casual Blazer with Trousers", "price": "Debug", "link": "", "thumbnail": "", "source": "Local Debug"},
        {"title": "Men's Satin Party Shirt - Emerald Green", "price": "Debug", "link": "", "thumbnail": "", "source": "Local Debug"},
        {"title": "Men's White Silk Blend Kurta", "price": "Debug", "link": "", "thumbnail": "", "source": "Local Debug"},
        {"title": "Men's Tailored Chinos for Evening Party", "price": "Debug", "link": "", "thumbnail": "", "source": "Local Debug"},
        {"title": "Men's Leather Jacket Night Out Look", "price": "Debug", "link": "", "thumbnail": "", "source": "Local Debug"},
        {"title": "Men's Navy Suit Separates for Party", "price": "Debug", "link": "", "thumbnail": "", "source": "Local Debug"},
        {"title": "Men's Printed Casual Shirt Rooftop Wear", "price": "Debug", "link": "", "thumbnail": "", "source": "Local Debug"},
        {"title": "Men's Ethnic Nehru Vest with Shirt", "price": "Debug", "link": "", "thumbnail": "", "source": "Local Debug"},
        {"title": "Men's Denim Jacket Casual Party Outfit", "price": "Debug", "link": "", "thumbnail": "", "source": "Local Debug"},
        {"title": "Men's Black Loafers Evening Wear", "price": "Debug", "link": "", "thumbnail": "", "source": "Local Debug"},
        {"title": "Men's Relaxed Fit Party Shirt - Blue", "price": "Debug", "link": "", "thumbnail": "", "source": "Local Debug"},
        {"title": "Men's Embroidered Kurta for Evening", "price": "Debug", "link": "", "thumbnail": "", "source": "Local Debug"}
    ]


# Recommendation Engine V2.1
def rerank_results(results, idea, preference_summary, occasion_priority=None):
    try:
        occasion_priority = occasion_priority or get_occasion_cluster_priorities(idea)
        occasion_terms = set(extract_keywords(idea))
        idea_tokens = set(re.findall(r"[a-z0-9]+", (idea or "").lower()))
        occasion_terms.update(idea_tokens)

        liked_keywords = set(preference_summary.get("liked_keywords", []))
        liked_keywords.update(preference_summary.get("liked_colors", []))
        liked_cluster_scores = preference_summary.get("liked_clusters", {}) or {}
        if isinstance(liked_cluster_scores, list):
            liked_cluster_scores = {cluster: 1.0 for cluster in liked_cluster_scores}
        historical_clusters = set(liked_cluster_scores.keys())
        historical_clusters.update(preference_summary.get("disliked_clusters", []))
        disliked_keywords = set(preference_summary.get("disliked_keywords", []))

        scored_results = []
        for original_index, item in enumerate(results or []):
            title = item.get("title", "")
            title_keywords = set(extract_keywords(title))
            title_tokens = set(re.findall(r"[a-z0-9]+", (title or "").lower()))
            cluster = infer_cluster(title)

            occasion_overlap = occasion_terms.intersection(title_keywords.union(title_tokens))
            occasion_match = min(1.0, len(occasion_overlap) / 3.0)

            preference_hits = len(title_keywords.intersection(liked_keywords))
            preference_hits += float(liked_cluster_scores.get(cluster, 0))
            if title_keywords.intersection(disliked_keywords):
                preference_hits -= 0.75
            preference_match = max(0.0, min(1.0, preference_hits / 3.0))

            novelty = 0.2 if cluster in historical_clusters else 1.0
            diversity_bonus = 1.0

            score = (
                0.5 * occasion_match
                + 0.25 * preference_match
                + 0.15 * novelty
                + 0.10 * diversity_bonus
            )

            if cluster == "ethnic" and not occasion_priority.get("is_ethnic_occasion"):
                score *= 0.55
                if occasion_priority.get("type") == "club":
                    score *= 0.30
                elif occasion_priority.get("type") == "beach":
                    score *= 0.20
                elif occasion_priority.get("type") == "rooftop":
                    score *= 0.45
            elif cluster == "ethnic" and occasion_priority.get("is_ethnic_occasion"):
                score *= 1.35

            score *= occasion_priority.get("boosts", {}).get(cluster, 1.0)
            score *= occasion_priority.get("penalties", {}).get(cluster, 1.0)

            # Mild Amazon Ranking Boost
            if "amazon" in (item.get("source") or "").lower():
                score += 0.12

            scored_results.append({
                "item": item,
                "cluster": cluster,
                "score": score,
                "original_index": original_index
            })

        scored_results.sort(key=lambda result: (-result["score"], result["original_index"]))

        selected = []
        selected_counts = defaultdict(int)
        remaining = scored_results[:]
        target_limit = 16
        cluster_cap = 5

        while remaining and len(selected) < target_limit:
            best_index = 0
            best_adjusted_score = None
            for index, result in enumerate(remaining):
                cluster_count = selected_counts[result["cluster"]]
                if cluster_count >= cluster_cap and len(remaining) >= target_limit - len(selected):
                    continue
                repeat_penalty = 0.30 * max(0, cluster_count - 2)
                adjusted_score = result["score"] - repeat_penalty
                if best_adjusted_score is None or adjusted_score > best_adjusted_score:
                    best_adjusted_score = adjusted_score
                    best_index = index

            chosen = remaining.pop(best_index)
            selected.append(chosen["item"])
            selected_counts[chosen["cluster"]] += 1

        if len(selected) < len(scored_results):
            selected_ids = {id(item) for item in selected}
            selected.extend(
                result["item"]
                for result in scored_results
                if id(result["item"]) not in selected_ids
            )

        cluster_counter = Counter(infer_cluster(item.get("title", "")) for item in selected[:16])
        print("Final cluster counts:", dict(cluster_counter))

        return selected
    except Exception as e:
        print(f"Failed to rerank results: {e}")
        return results


@idea_search_bp.route('/search-ideas', methods=['POST'])
def search_ideas():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Invalid request'}), 400
        
    idea = data.get('idea')
    username = data.get('username')
    debug_no_serpapi = data.get('debug_no_serpapi') is True
    
    if not idea:
        return jsonify({'error': 'No idea provided'}), 400
        
    if not Config.GEMINI_API_KEY:
        return jsonify({'error': 'gemini_api_key_missing', 'message': 'Gemini API key is not configured in the backend .env file.'}), 500
        
    try:
        conn = get_connection()
        cur = conn.cursor()
        # 1. Fetch user profile context if username is provided
        profile_context = ""
        occasion_context = build_occasion_context(idea)
        occasion_priority = get_occasion_cluster_priorities(idea)
        preference_summary = {
            "liked_keywords": [],
            "liked_clusters": {},
            "liked_colors": [],
            "disliked_keywords": [],
            "disliked_clusters": [],
            "recent_shift": []
        }
        if username:
            # Fetch static profile
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
                    profile_context += "\nUser Profile Constraints:\n" + "\n".join(profile_parts) + "\nIncorporate these profile preferences into the search query if they make sense, but prioritize the user's explicit description."

            # Fetch dynamic interactions (Phase 2 feedback loop)
            cur.execute("""
                SELECT title, interaction_type 
                FROM user_interactions 
                WHERE username = %s 
                ORDER BY created_at DESC LIMIT 15
            """, (username,))
            interactions = cur.fetchall()
            preference_summary = summarize_interactions(interactions, occasion_priority)

        print("Normalized preference:", preference_summary)
        print("Occasion priority:", occasion_priority)

        # 2. Prompt Gemini AI to generate a strong shopping query
        genai.configure(api_key=Config.GEMINI_API_KEY)
        model = genai.GenerativeModel(Config.GEMINI_MODEL)
        occasion_context_for_prompt = dict(occasion_context)
        occasion_context_for_prompt["cluster_priority"] = occasion_priority
        prompt = SMART_FASHION_SEARCH_PROMPT.format(
            user_profile=profile_context or "No saved profile constraints.",
            summarized_likes=json.dumps({
                "liked_keywords": preference_summary.get("liked_keywords", []),
                "liked_clusters": preference_summary.get("liked_clusters", []),
                "liked_colors": preference_summary.get("liked_colors", []),
                "recent_shift": preference_summary.get("recent_shift", [])
            }),
            summarized_dislikes=json.dumps({
                "disliked_keywords": preference_summary.get("disliked_keywords", []),
                "disliked_clusters": preference_summary.get("disliked_clusters", [])
            }),
            occasion_context=json.dumps(occasion_context_for_prompt),
            idea=idea
        )
        
        response = model.generate_content(prompt)
        fallback_parts = [idea or "outfit"]
        profile_keywords = extract_keywords(profile_context)
        if profile_keywords:
            fallback_parts.extend(profile_keywords[:3])
        fallback_parts.append("outfit clothing")
        fallback_query = " ".join(fallback_parts).strip()
        query = fallback_query

        try:
            cleaned_response = (response.text or "").strip()
            if cleaned_response.startswith("```"):
                cleaned_response = cleaned_response.strip("`")
                cleaned_response = cleaned_response.replace("json", "", 1).strip()
            parsed_response = json.loads(cleaned_response)
            parsed_query = (parsed_response.get("query") or "").strip()
            if parsed_query:
                query = parsed_query.replace('"', "")
        except Exception as e:
            print(f"Failed to parse Gemini search JSON: {e}")
        print("Generated query:", query)
        
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
        cur.close()
        conn.close()

        if debug_no_serpapi:
            shopping_results = rerank_results(build_debug_results(), idea, preference_summary, occasion_priority)
            clean_results = []
            amazon_count = 0
            sample_amazon_link = ""
            for item in shopping_results[:16]:
                link = resolve_direct_product_link(item)
                source = item.get("source", "")
                if "amazon" in source.lower() and link:
                    amazon_count += 1
                    if not sample_amazon_link:
                        sample_amazon_link = link
                clean_results.append({
                    "title": item.get("title", 'Unknown Dress'),
                    "price": item.get("price", ''),
                    "link": link,
                    "thumbnail": item.get("thumbnail", ''),
                    "source": item.get("source", '')
                })
            print("Amazon direct links generated:", amazon_count)
            print("Sample amazon link:", sample_amazon_link)

            return jsonify({
                'query_used': query,
                'results': clean_results
            }), 200

        # 4. Search SerpAPI using the AI generated query
        if not Config.SERPAPI_KEY:
            return jsonify({'error': 'SerpAPI key not configured in .env file'}), 500
        if GoogleSearch is None:
            return jsonify({'error': 'SerpAPI client is not installed. Install google-search-results==2.4.2.'}), 500
            
        params = {
            "engine": "google_shopping",
            "q": query,
            "gl": "in",
            "hl": "en",
            "location": "India",
            "google_domain": "google.co.in",
            "api_key": Config.SERPAPI_KEY
        }
        
        search = GoogleSearch(params)
        results_dict = search.get_dict()
        
        shopping_results = results_dict.get("shopping_results", [])
        shopping_results = rerank_results(shopping_results, idea, preference_summary, occasion_priority)
        
        # 5. Clean up the payload before sending it to Frontend
        clean_results = []
        amazon_count = 0
        sample_amazon_link = ""
        for item in shopping_results[:16]: # Return top 16 items
            affiliate_link = resolve_direct_product_link(item)
            source = item.get("source", "")
            if "amazon" in source.lower() and affiliate_link:
                amazon_count += 1
                if not sample_amazon_link:
                    sample_amazon_link = affiliate_link
            clean_results.append({
                "title": item.get("title", 'Unknown Dress'),
                "price": item.get("price", ''),
                "link": affiliate_link,
                "thumbnail": item.get("thumbnail", ''),
                "source": item.get("source", '')
            })
        print("Amazon direct links generated:", amazon_count)
        print("Sample amazon link:", sample_amazon_link)
            
        return jsonify({
            'query_used': query,
            'results': clean_results
        }), 200
        
    except Exception as e:
        try:
            cur.close()
            conn.close()
        except Exception:
            pass
        return jsonify({'error': 'Idea search pipeline failed', 'details': str(e)}), 500
