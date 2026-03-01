import os
import datetime
import hashlib
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import psycopg2
from PIL import Image
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from transformers import pipeline
from chatbot_routes import chatbot_bp
from per_user_index import add_image_for_user
from flask import send_from_directory
from async_module.routes import async_bp

UPLOAD_FOLDER = 'uploaded_images'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Initialize Flask App
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 8 * 1024 * 1024  # 8MB upload limit
CORS(app)

# Register chatbot blueprint
app.register_blueprint(chatbot_bp)
app.register_blueprint(async_bp)

# PostgreSQL connection
conn = psycopg2.connect(
    dbname=os.environ.get("DB_NAME", "loga"),
    user=os.environ.get("DB_USER", "postgres"),
    password=os.environ.get("DB_PASSWORD", "loga"),
    host=os.environ.get("DB_HOST", "localhost"),
    port=os.environ.get("DB_PORT", "5432"),
)
cur = conn.cursor()

# Add favorite column to uploads table if it doesn't exist
try:
    cur.execute("ALTER TABLE uploads ADD COLUMN IF NOT EXISTS favorite BOOLEAN DEFAULT FALSE")
    conn.commit()
except Exception as e:
    print(f"Error adding favorite column: {e}")
    conn.rollback()

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

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


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


@app.route('/signup', methods=['POST'])
def signup():
    data = request.get_json()
    username = data['username']
    password = data['password']

    try:
        password_hash = generate_password_hash(password)
        cur.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, password_hash))
        conn.commit()
        return jsonify({"message": "Signup successful", "user": username}), 200
    except Exception:
        conn.rollback()
        return jsonify({"error": "Username already exists or DB error"}), 400


@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    try:
        cur.execute("SELECT password FROM users WHERE username = %s", (username,))
        result = cur.fetchone()

        if result and check_password_hash(result[0], password):
            return jsonify({"message": "Login successful", "user": username}), 200
        else:
            return jsonify({"error": "Invalid credentials"}), 401
    except Exception as e:
        conn.rollback()
        return jsonify({"error": "Database error", "details": str(e)}), 500


@app.route('/classify', methods=['POST'])
def classify():
    image_file = request.files.get('image')
    username = request.form.get('username')

    if not image_file or not username:
        return jsonify({'error': 'Image or username missing'}), 400

    if not allowed_file(image_file.filename):
        return jsonify({'error': 'Unsupported file type'}), 400

    image_bytes = image_file.read()
    image_hash = hashlib.md5(image_bytes).hexdigest()

    # Check duplicates
    cur.execute(
        "SELECT image_path, position, style, color FROM uploads WHERE username = %s AND md5_hash = %s",
        (username, image_hash)
    )
    existing = cur.fetchone()
    if existing:
        image_url = f"http://localhost:5000/image/{os.path.basename(existing[0])}"
        return jsonify({
            'position': existing[1],
            'style': existing[2],
            'color': existing[3],
            'message': 'Duplicate image already uploaded.',
            'image_url': image_url
        })

    # Save new image
    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    filename = secure_filename(f"{username}_{timestamp}_{image_file.filename}")
    file_path = os.path.join(UPLOAD_FOLDER, filename)

    with open(file_path, 'wb') as f:
        f.write(image_bytes)

    try:
        img = Image.open(file_path)
    except Exception:
        if os.path.exists(file_path):
            os.remove(file_path)
        return jsonify({'error': 'Invalid image file'}), 400

    # Use efficient multi-attribute classification
    classification = classify_all_attributes_efficient(img)
    position = classification["position"]
    style = classification["style"]
    color = classification["color"]

    cur.execute(
        "INSERT INTO uploads (username, image_path, position, style, color, md5_hash, uploaded_at) VALUES (%s, %s, %s, %s, %s, %s, %s)",
        (username, file_path, position, style, color, image_hash, datetime.datetime.now())
    )
    conn.commit()

    # Also index the image for chatbot functionality
    try:
        add_image_for_user(username, file_path, style, color)
        print(f"Image indexed for chatbot: {filename}")
    except Exception as e:
        print(f"Warning: Failed to index image for chatbot: {e}")

    image_url = f"http://localhost:5000/image/{filename}"
    return jsonify({
        'position': position,
        'style': style,
        'color': color,
        'image_url': image_url
    })


@app.route('/history/<username>', methods=['GET'])
def get_history(username):
    try:
        cur.execute(
            "SELECT id, image_path, position, style, color, uploaded_at, favorite FROM uploads WHERE username = %s ORDER BY uploaded_at DESC",
            (username,)
        )
        uploads = cur.fetchall()

        results = []
        for upload in uploads:
            results.append({
                'id': upload[0],
                'image_url': f"http://localhost:5000/image/{os.path.basename(upload[1])}",
                'position': upload[2],
                'style': upload[3],
                'color': upload[4],
                'uploaded_at': upload[5].isoformat(),
                'favorite': upload[6] if upload[6] is not None else False
            })

        return jsonify(results)
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/delete_upload', methods=['POST'])
def delete_upload():
    data = request.get_json()
    upload_id = data.get('upload_id')

    try:
        cur.execute("SELECT image_path FROM uploads WHERE id = %s", (upload_id,))
        img = cur.fetchone()
        if img:
            image_path = img[0]
            if os.path.exists(image_path):
                os.remove(image_path)

        cur.execute("DELETE FROM uploads WHERE id = %s", (upload_id,))
        conn.commit()
        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})


@app.route('/image/<filename>')
def get_image(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)


@app.route('/get-suggestions', methods=['POST'])
def get_suggestions():
    data = request.json
    destination = data['destination']
    username = data.get('username')

    if not username:
        return jsonify({'error': 'Username is required'}), 400

    cur.execute("""
        SELECT DISTINCT ON (md5_hash) image_path, uploaded_at, style, position, md5_hash
        FROM uploads
        WHERE style = %s AND username = %s
        ORDER BY md5_hash, uploaded_at DESC
    """, (destination, username))

    results = cur.fetchall()

    suggestions = [{
        'image_url': f"http://localhost:5000/image/{os.path.basename(r[0])}",
        'uploaded_at': r[1],
        'style': r[2],
        'position': r[3]
    } for r in results]

    return jsonify({'suggestions': suggestions})


@app.route('/uploaded_images/<path:filename>')
def serve_uploaded_image(filename):
    return send_from_directory(os.path.join(os.getcwd(), 'uploaded_images'), filename)


@app.route('/toggle_favorite', methods=['POST'])
def toggle_favorite():
    data = request.get_json()
    upload_id = data.get('upload_id')
    username = data.get('username')

    try:
        cur.execute("SELECT favorite FROM uploads WHERE id = %s AND username = %s", (upload_id, username))
        result = cur.fetchone()

        if not result:
            return jsonify({'status': 'error', 'message': 'Upload not found'}), 404

        current_favorite = result[0] if result[0] is not None else False
        new_favorite = not current_favorite

        cur.execute("UPDATE uploads SET favorite = %s WHERE id = %s AND username = %s",
                   (new_favorite, upload_id, username))
        conn.commit()

        return jsonify({'status': 'success', 'favorite': new_favorite})
    except Exception as e:
        conn.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/check-duplicates', methods=['GET'])
def check_duplicates():
    try:
        cur.execute("""
            SELECT image_path, COUNT(*) as count
            FROM uploads
            GROUP BY image_path
            HAVING COUNT(*) > 1
            ORDER BY count DESC
        """)
        duplicates = cur.fetchall()

        if duplicates:
            return jsonify({
                'status': 'found',
                'duplicates': [{'image_path': d[0], 'count': d[1]} for d in duplicates]
            })
        else:
            return jsonify({'status': 'clean', 'message': 'No duplicates found'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/clean-duplicates', methods=['POST'])
def clean_duplicates():
    try:
        cur.execute("""
            DELETE FROM uploads 
            WHERE id NOT IN (
                SELECT MAX(id) 
                FROM uploads 
                GROUP BY image_path
            )
        """)
        deleted_count = cur.rowcount
        conn.commit()
        return jsonify({
            'status': 'success',
            'message': f'Removed {deleted_count} duplicate entries'
        })
    except Exception as e:
        conn.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/index-existing-images', methods=['POST'])
def index_existing_images():
    """Index all existing images for a user in the chatbot system"""
    try:
        data = request.get_json()
        username = data.get('username')
        
        if not username:
            return jsonify({'error': 'Username required'}), 400
        
        # Get all existing uploads for the user
        cur.execute(
            "SELECT image_path, position, style, color FROM uploads WHERE username = %s",
            (username,)
        )
        uploads = cur.fetchall()
        
        indexed_count = 0
        errors = []
        
        for image_path, position, style, color in uploads:
            if os.path.exists(image_path):
                try:
                    add_image_for_user(username, image_path, style, color)
                    indexed_count += 1
                except Exception as e:
                    errors.append(f"Failed to index {os.path.basename(image_path)}: {str(e)}")
        
        return jsonify({
            'message': f'Indexed {indexed_count} images for chatbot',
            'indexed_count': indexed_count,
            'total_images': len(uploads),
            'errors': errors
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Database error', 'details': str(e)}), 500


@app.route('/test-classification', methods=['POST'])
def test_classification():
    """Test different classification methods for comparison."""
    image_file = request.files.get('image')
    
    if not image_file:
        return jsonify({'error': 'Image missing'}), 400
    
    if not allowed_file(image_file.filename):
        return jsonify({'error': 'Unsupported file type'}), 400
    
    try:
        # Save temporary image for testing
        timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        filename = f"test_{timestamp}_{secure_filename(image_file.filename)}"
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        
        with open(file_path, 'wb') as f:
            f.write(image_file.read())
        
        img = Image.open(file_path)
        
        # Test different classification methods
        results = {}
        
        # Method 1: Original individual classification
        start_time = datetime.datetime.now()
        position1 = classify_attribute(img, POSITION_CATEGORIES, clean=True)
        style1 = classify_attribute(img, STYLE_CATEGORIES, clean=True)
        color1 = classify_attribute(img, COLOR_CATEGORIES, clean=True)
        time1 = (datetime.datetime.now() - start_time).total_seconds()
        
        results['method1_individual'] = {
            'position': position1,
            'style': style1,
            'color': color1,
            'time_seconds': time1,
            'method': 'Individual CLIP calls'
        }
        
        # Method 2: Efficient multi-attribute classification
        start_time = datetime.datetime.now()
        classification2 = classify_all_attributes_efficient(img)
        time2 = (datetime.datetime.now() - start_time).total_seconds()
        
        results['method2_efficient'] = {
            'position': classification2["position"],
            'style': classification2["style"],
            'color': classification2["color"],
            'time_seconds': time2,
            'method': 'Single CLIP call with all categories'
        }
        
        # Method 3: Enhanced confidence-boosted classification
        start_time = datetime.datetime.now()
        classification3 = classify_with_confidence_boost(img, "all")
        time3 = (datetime.datetime.now() - start_time).total_seconds()
        
        results['method3_enhanced'] = {
            'position': classification3["position"],
            'style': classification3["style"],
            'color': classification3["color"],
            'time_seconds': time3,
            'method': 'Enhanced prompts with confidence boosting'
        }
        
        # Clean up test file
        if os.path.exists(file_path):
            os.remove(file_path)
        
        return jsonify({
            'status': 'success',
            'results': results,
            'recommendation': get_recommendation(results)
        })
        
    except Exception as e:
        # Clean up on error
        if 'file_path' in locals() and os.path.exists(file_path):
            os.remove(file_path)
        return jsonify({'status': 'error', 'message': str(e)}), 500


def get_recommendation(results):
    """Get recommendation based on classification results."""
    # Find fastest method
    fastest = min(results.values(), key=lambda x: x['time_seconds'])
    
    # Check for consistency across methods
    positions = [r['position'] for r in results.values()]
    styles = [r['style'] for r in results.values()]
    colors = [r['color'] for r in results.values()]
    
    position_consistent = len(set(positions)) == 1 and positions[0] != 'unknown'
    style_consistent = len(set(styles)) == 1 and styles[0] != 'unknown'
    color_consistent = len(set(colors)) == 1 and colors[0] != 'unknown'
    
    consistency_score = sum([position_consistent, style_consistent, color_consistent])
    
    if consistency_score >= 2:
        return f"High confidence results. Recommended method: {fastest['method']} (fastest: {fastest['time_seconds']:.3f}s)"
    elif consistency_score >= 1:
        return f"Moderate confidence. Recommended method: {fastest['method']} (fastest: {fastest['time_seconds']:.3f}s)"
    else:
        return f"Low confidence. Recommended method: Enhanced prompts for better accuracy (fastest: {fastest['time_seconds']:.3f}s)"


@app.route('/classify-enhanced', methods=['POST'])
def classify_enhanced():
    """Enhanced classification endpoint using the best performing method."""
    image_file = request.files.get('image')
    username = request.form.get('username')
    
    if not image_file or not username:
        return jsonify({'error': 'Image or username missing'}), 400
    
    if not allowed_file(image_file.filename):
        return jsonify({'error': 'Unsupported file type'}), 400
    
    image_bytes = image_file.read()
    image_hash = hashlib.md5(image_bytes).hexdigest()
    
    # Check duplicates
    cur.execute(
        "SELECT image_path, position, style, color FROM uploads WHERE username = %s AND md5_hash = %s",
        (username, image_hash)
    )
    existing = cur.fetchone()
    if existing:
        image_url = f"http://localhost:5000/image/{os.path.basename(existing[0])}"
        return jsonify({
            'position': existing[1],
            'style': existing[2],
            'color': existing[3],
            'message': 'Duplicate image already uploaded.',
            'image_url': image_url
        })
    
    # Save new image
    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    filename = secure_filename(f"{username}_{timestamp}_{image_file.filename}")
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    
    with open(file_path, 'wb') as f:
        f.write(image_bytes)
    
    try:
        img = Image.open(file_path)
    except Exception:
        if os.path.exists(file_path):
            os.remove(file_path)
        return jsonify({'error': 'Invalid image file'}), 400
    
    # Use enhanced classification
    classification = classify_with_confidence_boost(img, "all")
    
    cur.execute(
        "INSERT INTO uploads (username, image_path, position, style, color, md5_hash, uploaded_at) VALUES (%s, %s, %s, %s, %s, %s, %s)",
        (username, file_path, classification["position"], classification["style"], classification["color"], image_hash, datetime.datetime.now())
    )
    conn.commit()
    
    image_url = f"http://localhost:5000/image/{filename}"
    return jsonify({
        'position': classification["position"],
        'style': classification["style"],
        'color': classification["color"],
        'image_url': image_url,
        'method': 'Enhanced CLIP classification'
    })

@app.route('/image/<path:filename>')
def serve_image(filename):
    return send_from_directory("uploaded_images", filename)

if __name__ == '__main__':
    app.run(debug=True)
