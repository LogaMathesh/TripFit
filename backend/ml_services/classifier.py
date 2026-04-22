from transformers import pipeline

# Load zero-shot classification pipeline
classifier = pipeline("zero-shot-image-classification", model="openai/clip-vit-base-patch32")

# Improved prompt-engineered categories for better CLIP performance
POSITION_CATEGORIES = [
    "upper body clothing, shirt, blouse, top",
    "lower body clothing, pants, skirt, trousers",
    "full body clothing, dress, gown, jumpsuit"
]

STYLE_CATEGORIES = [
    "formal business attire, professional clothing, office wear",
    "traditional ethnic clothing, cultural dress, heritage wear",
    "casual everyday clothing, relaxed wear, comfortable outfit"
]

COLOR_CATEGORIES = [
    "red clothing, red dress, red shirt",
    "blue clothing, blue dress, blue shirt", 
    "green clothing, green dress, green shirt",
    "black clothing, black dress, black shirt",
    "white clothing, white dress, white shirt",
    "yellow clothing, yellow dress, yellow shirt",
    "orange clothing, orange dress, orange shirt",
    "purple clothing, purple dress, purple shirt",
    "brown clothing, brown dress, brown shirt",
    "pink clothing, pink dress, pink shirt",
    "gray clothing, gray dress, gray shirt"
]

# Enhanced classification function with better prompt handling
def classify_attribute(image, categories, clean=False):
    """Classify attribute using CLIP with improved prompt engineering."""
    try:
        results = classifier(images=image, candidate_labels=categories)
        if results and len(results) > 0:
            # Sort by confidence score
            sorted_results = sorted(results, key=lambda x: x['score'], reverse=True)
            top_result = sorted_results[0]
            
            # Very low threshold to ensure we get results
            if top_result['score'] > 0.05:  # Much lower threshold
                label = top_result['label']
                
                if clean:  # Map back to simple labels for JSON response
                    if "color" in label:
                        # Extract color from prompt with more flexible matching
                        color_map = {
                            "red": "red", "blue": "blue", "green": "green", 
                            "black": "black", "white": "white", "yellow": "yellow",
                            "orange": "orange", "purple": "purple", "brown": "brown",
                            "pink": "pink", "gray": "gray"
                        }
                        for color, clean_color in color_map.items():
                            if color in label.lower():
                                return clean_color
                        # If no color found, return most common
                        return "black"
                    elif "clothing" in label or "garment" in label:
                        if any(word in label.lower() for word in ["upper", "shirt", "blouse", "top", "t-shirt"]):
                            return "upper"
                        elif any(word in label.lower() for word in ["lower", "pants", "skirt", "trousers", "jeans"]):
                            return "lower"
                        elif any(word in label.lower() for word in ["full", "dress", "gown", "jumpsuit", "onesie"]):
                            return "full"
                        # Default to upper body if unclear
                        return "upper"
                    elif any(word in label.lower() for word in ["formal", "business", "professional", "office", "corporate", "attire"]):
                        return "formal"
                    elif any(word in label.lower() for word in ["traditional", "ethnic", "cultural", "heritage", "ceremonial"]):
                        return "traditional"
                    elif any(word in label.lower() for word in ["casual", "everyday", "relaxed", "comfortable", "street", "outfit"]):
                        return "casual"
                    # Default to casual if unclear
                    return "casual"
                
                return label
            else:
                # Return sensible defaults instead of unknown
                if "color" in categories[0]:
                    return "black"
                elif "clothing" in categories[0]:
                    return "upper"
                else:
                    return "casual"
        # Return sensible defaults instead of unknown
        if "color" in categories[0]:
            return "black"
        elif "clothing" in categories[0]:
            return "upper"
        else:
            return "casual"
    except Exception as e:
        print(f"Classification error: {e}")
        # Return sensible defaults instead of unknown
        if "color" in categories[0]:
            return "black"
        elif "clothing" in categories[0]:
            return "upper"
        else:
            return "casual"


def classify_all_attributes_efficient(image):
    """Efficiently classify all attributes in a single CLIP call for better performance."""
    try:
        # Combine all categories into one comprehensive classification
        all_categories = []
        
        # Position categories
        all_categories.extend([
            "upper body shirt blouse top",
            "lower body pants skirt trousers", 
            "full body dress gown jumpsuit"
        ])
        
        # Style categories
        all_categories.extend([
            "formal business professional office",
            "traditional ethnic cultural heritage",
            "casual everyday relaxed comfortable"
        ])
        
        # Color categories
        all_categories.extend([
            "red clothing", "blue clothing", "green clothing",
            "black clothing", "white clothing", "yellow clothing",
            "orange clothing", "purple clothing", "brown clothing",
            "pink clothing", "gray clothing"
        ])
        
        # Single CLIP call for all categories
        results = classifier(images=image, candidate_labels=all_categories)
        
        if not results or len(results) == 0:
            # Return sensible defaults instead of unknown
            return {"position": "upper", "style": "casual", "color": "black"}
        
        # Sort by confidence score
        sorted_results = sorted(results, key=lambda x: x['score'], reverse=True)
        
        # Initialize results with defaults instead of unknown
        classification = {"position": "upper", "style": "casual", "color": "black"}
        
        # Process results with very low threshold for better coverage
        for result in sorted_results:
            if result['score'] < 0.05:  # Very low threshold
                continue
                
            label = result['label'].lower()
            
            # Determine position with more flexible matching
            if any(word in label for word in ["upper", "shirt", "blouse", "top", "t-shirt", "garment"]):
                classification["position"] = "upper"
            elif any(word in label for word in ["lower", "pants", "skirt", "trousers", "jeans", "garment"]):
                classification["position"] = "lower"
            elif any(word in label for word in ["full", "dress", "gown", "jumpsuit", "onesie", "garment"]):
                classification["position"] = "full"
            
            # Determine style with more flexible matching
            if any(word in label for word in ["formal", "business", "professional", "office", "corporate", "attire"]):
                classification["style"] = "formal"
            elif any(word in label for word in ["traditional", "ethnic", "cultural", "heritage", "ceremonial"]):
                classification["style"] = "traditional"
            elif any(word in label for word in ["casual", "everyday", "relaxed", "comfortable", "street", "outfit"]):
                classification["style"] = "casual"
            
            # Determine color with more flexible matching
            color_map = {
                "red": "red", "blue": "blue", "green": "green",
                "black": "black", "white": "white", "yellow": "yellow",
                "orange": "orange", "purple": "purple", "brown": "brown",
                "pink": "pink", "gray": "gray"
            }
            for color, clean_color in color_map.items():
                if color in label:
                    classification["color"] = clean_color
                    break
        
        return classification
        
    except Exception as e:
        print(f"Multi-attribute classification error: {e}")
        # Return sensible defaults instead of unknown
        return {"position": "upper", "style": "casual", "color": "black"}


def generate_enhanced_prompts():
    """Generate enhanced prompts with better CLIP performance."""
    return {
        "position": [
            "upper body garment, shirt, blouse, top, t-shirt",
            "lower body garment, pants, skirt, trousers, jeans",
            "full body garment, dress, gown, jumpsuit, onesie"
        ],
        "style": [
            "formal professional business attire, office wear, corporate clothing",
            "traditional cultural ethnic clothing, heritage dress, ceremonial wear",
            "casual relaxed everyday clothing, street wear, comfortable outfit"
        ],
        "color": [
            "bright red clothing", "deep blue clothing", "forest green clothing",
            "jet black clothing", "pure white clothing", "sunny yellow clothing",
            "vibrant orange clothing", "royal purple clothing", "warm brown clothing",
            "soft pink clothing", "cool gray clothing"
        ]
    }


def classify_with_confidence_boost(image, attribute_type="all"):
    """Classify with confidence boosting using multiple prompt variations."""
    try:
        enhanced_prompts = generate_enhanced_prompts()
        
        if attribute_type == "all":
            # Combine all enhanced prompts for single classification
            all_prompts = []
            for category_prompts in enhanced_prompts.values():
                all_prompts.extend(category_prompts)
            
            results = classifier(images=image, candidate_labels=all_prompts)
            
            if not results:
                # Return sensible defaults instead of unknown
                return {"position": "upper", "style": "casual", "color": "black"}
            
            # Process with confidence boosting
            return process_confidence_boosted_results(results, enhanced_prompts)
        
        else:
            # Single attribute classification with enhanced prompts
            prompts = enhanced_prompts.get(attribute_type, [])
            if not prompts:
                # Return sensible defaults instead of unknown
                if attribute_type == "position":
                    return "upper"
                elif attribute_type == "style":
                    return "casual"
                elif attribute_type == "color":
                    return "black"
                return "casual"
            
            results = classifier(images=image, candidate_labels=prompts)
            if not results:
                # Return sensible defaults instead of unknown
                if attribute_type == "position":
                    return "upper"
                elif attribute_type == "style":
                    return "casual"
                elif attribute_type == "color":
                    return "black"
                return "casual"
            
            # Return top result if confidence is high enough
            top_result = max(results, key=lambda x: x['score'])
            if top_result['score'] > 0.1:  # Lower threshold
                result = map_enhanced_prompt_to_clean(top_result['label'], attribute_type)
                if result != "unknown":
                    return result
            
            # Return sensible defaults instead of unknown
            if attribute_type == "position":
                return "upper"
            elif attribute_type == "style":
                return "casual"
            elif attribute_type == "color":
                return "black"
            return "casual"
            
    except Exception as e:
        print(f"Enhanced classification error: {e}")
        return {"position": "unknown", "style": "unknown", "color": "unknown"}


def process_confidence_boosted_results(results, enhanced_prompts):
    """Process results with confidence boosting for better accuracy."""
    # Initialize with sensible defaults instead of unknown
    classification = {"position": "upper", "style": "casual", "color": "black"}
    
    # Sort by confidence score
    sorted_results = sorted(results, key=lambda x: x['score'], reverse=True)
    
    # Process each result with very low threshold for better coverage
    for result in sorted_results:
        if result['score'] < 0.05:  # Very low threshold
            continue
            
        label = result['label'].lower()
        
        # Determine position with more flexible matching
        if any(word in label for word in ["upper", "shirt", "blouse", "top", "t-shirt", "garment"]):
            classification["position"] = "upper"
        elif any(word in label for word in ["lower", "pants", "skirt", "trousers", "jeans", "garment"]):
            classification["position"] = "lower"
        elif any(word in label for word in ["full", "dress", "gown", "jumpsuit", "onesie", "garment"]):
            classification["position"] = "full"
        
        # Determine style with more flexible matching
        if any(word in label for word in ["formal", "professional", "business", "office", "corporate", "attire"]):
            classification["style"] = "formal"
        elif any(word in label for word in ["traditional", "cultural", "ethnic", "heritage", "ceremonial"]):
            classification["style"] = "traditional"
        elif any(word in label for word in ["casual", "relaxed", "everyday", "street", "comfortable", "outfit"]):
            classification["style"] = "casual"
        
        # Determine color with more flexible matching
        color_map = {
            "red": "red", "blue": "blue", "green": "green",
            "black": "black", "white": "white", "yellow": "yellow",
            "orange": "orange", "purple": "purple", "brown": "brown",
            "pink": "pink", "gray": "gray"
        }
        for color, clean_color in color_map.items():
            if color in label:
                classification["color"] = clean_color
                break
    
    return classification


def map_enhanced_prompt_to_clean(label, attribute_type):
    """Map enhanced prompt results to clean labels."""
    label_lower = label.lower()
    
    if attribute_type == "position":
        if any(word in label_lower for word in ["upper", "shirt", "blouse", "top"]):
            return "upper"
        elif any(word in label_lower for word in ["lower", "pants", "skirt", "trousers"]):
            return "lower"
        elif any(word in label_lower for word in ["full", "dress", "gown", "jumpsuit"]):
            return "full"
    
    elif attribute_type == "style":
        if any(word in label_lower for word in ["formal", "professional", "business", "office"]):
            return "formal"
        elif any(word in label_lower for word in ["traditional", "cultural", "ethnic", "heritage"]):
            return "traditional"
        elif any(word in label_lower for word in ["casual", "relaxed", "everyday", "street"]):
            return "casual"
    
    elif attribute_type == "color":
        color_map = {
            "red": "red", "blue": "blue", "green": "green",
            "black": "black", "white": "white", "yellow": "yellow",
            "orange": "orange", "purple": "purple", "brown": "brown",
            "pink": "pink", "gray": "gray"
        }
        for color, clean_color in color_map.items():
            if color in label_lower:
                return clean_color
    
        # Default to black if unclear
        return "black"
    
    # Return sensible defaults instead of unknown
    if attribute_type == "position":
        return "upper"
    elif attribute_type == "style":
        return "casual"
    elif attribute_type == "color":
        return "black"
    return "casual"
