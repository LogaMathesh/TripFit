import os
import datetime
from PIL import Image
from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename
from database import cur, conn
from config import Config
from ml_services.classifier import classify_attribute, classify_all_attributes_efficient, classify_with_confidence_boost, POSITION_CATEGORIES, STYLE_CATEGORIES, COLOR_CATEGORIES
from ml_services.per_user_index import add_image_for_user

maintenance_bp = Blueprint('maintenance_bp', __name__)

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}
def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

@maintenance_bp.route('/check-duplicates', methods=['GET'])
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


@maintenance_bp.route('/clean-duplicates', methods=['POST'])
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


@maintenance_bp.route('/index-existing-images', methods=['POST'])
def index_existing_images():
    """Index all existing images for a user in the chatbot system"""
    try:
        data = request.get_json()
        username = data.get('username')
        
        if not username:
            return jsonify({'error': 'Username required'}), 400
        
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


@maintenance_bp.route('/test-classification', methods=['POST'])
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
        file_path = os.path.join(Config.UPLOAD_FOLDER, filename)
        
        with open(file_path, 'wb') as f:
            f.write(image_file.read())
        
        img = Image.open(file_path)
        
        results = {}
        
        # Method 1
        start_time = datetime.datetime.now()
        position1 = classify_attribute(img, POSITION_CATEGORIES, clean=True)
        style1 = classify_attribute(img, STYLE_CATEGORIES, clean=True)
        color1 = classify_attribute(img, COLOR_CATEGORIES, clean=True)
        time1 = (datetime.datetime.now() - start_time).total_seconds()
        
        results['method1_individual'] = {
            'position': position1, 'style': style1, 'color': color1,
            'time_seconds': time1, 'method': 'Individual CLIP calls'
        }
        
        # Method 2
        start_time = datetime.datetime.now()
        classification2 = classify_all_attributes_efficient(img)
        time2 = (datetime.datetime.now() - start_time).total_seconds()
        
        results['method2_efficient'] = {
            'position': classification2["position"], 'style': classification2["style"], 'color': classification2["color"],
            'time_seconds': time2, 'method': 'Single CLIP call'
        }
        
        # Method 3
        start_time = datetime.datetime.now()
        classification3 = classify_with_confidence_boost(img, "all")
        time3 = (datetime.datetime.now() - start_time).total_seconds()
        
        results['method3_enhanced'] = {
            'position': classification3["position"], 'style': classification3["style"], 'color': classification3["color"],
            'time_seconds': time3, 'method': 'Enhanced prompts'
        }
        
        if os.path.exists(file_path):
            os.remove(file_path)
        
        def get_recommendation(results):
            fastest = min(results.items(), key=lambda x: x[1]['time_seconds'])
            return f"Use {fastest[0]} as it's the fastest ({fastest[1]['time_seconds']:.2f}s)"

        return jsonify({
            'status': 'success',
            'results': results,
            'recommendation': get_recommendation(results)
        })
        
    except Exception as e:
        if 'file_path' in locals() and os.path.exists(file_path):
            os.remove(file_path)
        return jsonify({'error': 'Processing error', 'details': str(e)}), 500
