import os
import json
from flask import Blueprint, request, jsonify
from database import cur, conn
from services.gemini_service import analyze_dress_image

maintenance_bp = Blueprint('maintenance_bp', __name__)

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
    """Analyze all existing images for a user that are missing gemini_metadata"""
    try:
        data = request.get_json()
        username = data.get('username')
        
        if not username:
            return jsonify({'error': 'Username required'}), 400
        
        # Only fetch images that haven't been analyzed by Gemini yet
        cur.execute(
            "SELECT id, image_path FROM uploads WHERE username = %s AND gemini_metadata IS NULL",
            (username,)
        )
        uploads = cur.fetchall()
        
        indexed_count = 0
        errors = []
        
        for upload_id, image_path in uploads:
            if os.path.exists(image_path):
                try:
                    # Run through Gemini
                    metadata = analyze_dress_image(image_path)
                    
                    # Also update fallback legacy fields
                    position = metadata.get("category", "upper")
                    style = metadata.get("style", "casual")
                    color = metadata.get("primary_color", "black")
                    gemini_metadata_json = json.dumps(metadata)
                    
                    cur.execute(
                        "UPDATE uploads SET gemini_metadata = %s, position = %s, style = %s, color = %s WHERE id = %s",
                        (gemini_metadata_json, position, style, color, upload_id)
                    )
                    conn.commit()
                    indexed_count += 1
                except Exception as e:
                    errors.append(f"Failed to analyze {os.path.basename(image_path)}: {str(e)}")
            else:
                errors.append(f"File not found: {image_path}")
        
        return jsonify({
            'message': f'Analyzed {indexed_count} images for Gemini Chatbot',
            'indexed_count': indexed_count,
            'total_pending': len(uploads),
            'errors': errors
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Database error', 'details': str(e)}), 500
