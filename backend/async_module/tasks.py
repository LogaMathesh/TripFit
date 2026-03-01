import os
import datetime
import psycopg2
from PIL import Image
from transformers import pipeline
from .celery_setup import celery_instance
from per_user_index import add_image_for_user

# 1. Initialize the ML model natively inside the Celery Worker
print("Loading CLIP Model into Celery Worker...")
try:
    classifier = pipeline("zero-shot-image-classification", model="openai/clip-vit-base-patch32")
    print("CLIP Model loaded successfully!")
except Exception as e:
    print(f"Failed to load model: {e}")

def get_db_connection():
    return psycopg2.connect(
        dbname=os.environ.get("DB_NAME", "loga"),
        user=os.environ.get("DB_USER", "postgres"),
        password=os.environ.get("DB_PASSWORD", "loga"),
        host=os.environ.get("DB_HOST", "localhost"),
        port=os.environ.get("DB_PORT", "5432"),
    )

# --- Helper AI Functions (Moved here so Celery owns them) ---
def generate_enhanced_prompts():
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

def process_confidence_boosted_results(results):
    classification = {"position": "upper", "style": "casual", "color": "black"}
    sorted_results = sorted(results, key=lambda x: x['score'], reverse=True)
    
    for result in sorted_results:
        if result['score'] < 0.05:
            continue
            
        label = result['label'].lower()
        
        if any(word in label for word in ["upper", "shirt", "blouse", "top", "t-shirt", "garment"]):
            classification["position"] = "upper"
        elif any(word in label for word in ["lower", "pants", "skirt", "trousers", "jeans", "garment"]):
            classification["position"] = "lower"
        elif any(word in label for word in ["full", "dress", "gown", "jumpsuit", "onesie", "garment"]):
            classification["position"] = "full"
        
        if any(word in label for word in ["formal", "professional", "business", "office", "corporate", "attire"]):
            classification["style"] = "formal"
        elif any(word in label for word in ["traditional", "cultural", "ethnic", "heritage", "ceremonial"]):
            classification["style"] = "traditional"
        elif any(word in label for word in ["casual", "relaxed", "everyday", "street", "comfortable", "outfit"]):
            classification["style"] = "casual"
        
        color_map = {
            "red": "red", "blue": "blue", "green": "green", "black": "black", 
            "white": "white", "yellow": "yellow", "orange": "orange", 
            "purple": "purple", "brown": "brown", "pink": "pink", "gray": "gray"
        }
        for color, clean_color in color_map.items():
            if color in label:
                classification["color"] = clean_color
                break
                
    return classification

@celery_instance.task(bind=True, name='tasks.process_classification')
def process_classification(self, file_path, username, image_hash):
    try:
        # 2. CRITICAL FIX: Convert image to RGB instantly to prevent Tensor shape crashes
        img = Image.open(file_path).convert('RGB')
        
        # 3. Run Classification
        enhanced_prompts = generate_enhanced_prompts()
        all_prompts = []
        for category_prompts in enhanced_prompts.values():
            all_prompts.extend(category_prompts)
        
        results = classifier(img, candidate_labels=all_prompts)
        
        if not results:
            classification = {"position": "upper", "style": "casual", "color": "black"}
        else:
            classification = process_confidence_boosted_results(results)
            
        position = classification["position"]
        style = classification["style"]
        color = classification["color"]

        # 4. Save to Database
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO uploads (username, image_path, position, style, color, md5_hash, uploaded_at) VALUES (%s, %s, %s, %s, %s, %s, %s)",
            (username, file_path, position, style, color, image_hash, datetime.datetime.now())
        )
        conn.commit()
        cur.close()
        conn.close()

        # 5. Index for Chatbot
        try:
            add_image_for_user(username, file_path, style, color)
        except Exception as e:
            print(f"Chatbot index warning: {e}")

        filename = os.path.basename(file_path)
        return {
            'status': 'completed',
            'position': position,
            'style': style,
            'color': color,
            'image_url': f"http://localhost:5000/image/{filename}"
        }
        
    except Exception as e:
        print(f"Task Failed: {e}")
        # Return a failure state instead of unknown so your frontend can show the error
        raise Exception(f"AI Classification failed: {str(e)}")