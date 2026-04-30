import datetime
import hashlib
from flask import Blueprint, request, jsonify
from database import get_connection
from services.gemini_service import analyze_dress_image_url
import json

uploads_bp = Blueprint('uploads_bp', __name__)

@uploads_bp.route('/classify', methods=['POST'])
def classify():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Missing JSON body'}), 400

    image_url = data.get('image_url')
    username = data.get('username')

    if not image_url or not username:
        return jsonify({'error': 'image_url or username missing'}), 400

    # MD5 hash of URL to check for duplicate (since we don't have file bytes)
    image_hash = hashlib.md5(image_url.encode('utf-8')).hexdigest()

    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        "SELECT image_path, position, style, color FROM uploads WHERE username = %s AND md5_hash = %s",
        (username, image_hash)
    )
    existing = cur.fetchone()
    if existing:
        cur.close()
        conn.close()
        return jsonify({
            'position': existing[1], 'style': existing[2], 'color': existing[3],
            'message': 'Duplicate image already uploaded.', 'image_url': existing[0]
        })

    # Call Gemini API with the URL
    metadata = analyze_dress_image_url(image_url)
    
    # Map back to legacy fields
    position = metadata.get("category", "upper")
    style = metadata.get("style", "casual")
    color = metadata.get("primary_color", "black")
    
    gemini_metadata_json = json.dumps(metadata)

    cur.execute(
        "INSERT INTO uploads (username, image_path, position, style, color, md5_hash, uploaded_at, gemini_metadata) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
        (username, image_url, position, style, color, image_hash, datetime.datetime.now(), gemini_metadata_json)
    )
    conn.commit()
    cur.close()
    conn.close()

    return jsonify({'position': position, 'style': style, 'color': color, 'image_url': image_url})


@uploads_bp.route('/history/<username>', methods=['GET'])
def get_history(username):
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(
            "SELECT id, image_path, position, style, color, uploaded_at, favorite FROM uploads WHERE username = %s ORDER BY uploaded_at DESC",
            (username,)
        )
        uploads = cur.fetchall()
        cur.close()
        conn.close()

        results = [{
            'id': u[0], 'image_url': u[1],
            'position': u[2], 'style': u[3], 'color': u[4], 'uploaded_at': u[5].isoformat(),
            'favorite': u[6] if u[6] is not None else False
        } for u in uploads]

        return jsonify(results)
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@uploads_bp.route('/delete_upload', methods=['POST'])
def delete_upload():
    data = request.get_json()
    upload_id = data.get('upload_id')

    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM uploads WHERE id = %s", (upload_id,))
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})


@uploads_bp.route('/get-suggestions', methods=['POST'])
def get_suggestions():
    data = request.json
    destination = data['destination']
    username = data.get('username')

    if not username:
        return jsonify({'error': 'Username is required'}), 400

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT DISTINCT ON (md5_hash) image_path, uploaded_at, style, position, md5_hash
        FROM uploads
        WHERE style = %s AND username = %s
        ORDER BY md5_hash, uploaded_at DESC
    """, (destination, username))

    results = cur.fetchall()
    cur.close()
    conn.close()

    suggestions = [{
        'image_url': r[0],
        'uploaded_at': r[1], 'style': r[2], 'position': r[3]
    } for r in results]

    return jsonify({'suggestions': suggestions})


@uploads_bp.route('/toggle_favorite', methods=['POST'])
def toggle_favorite():
    data = request.get_json()
    upload_id = data.get('upload_id')
    username = data.get('username')

    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT favorite FROM uploads WHERE id = %s AND username = %s", (upload_id, username))
        result = cur.fetchone()

        if not result:
            cur.close()
            conn.close()
            return jsonify({'status': 'error', 'message': 'Upload not found'}), 404

        current_favorite = result[0] if result[0] is not None else False
        new_favorite = not current_favorite

        cur.execute("UPDATE uploads SET favorite = %s WHERE id = %s AND username = %s",
                   (new_favorite, upload_id, username))
        conn.commit()
        cur.close()
        conn.close()

        return jsonify({'status': 'success', 'favorite': new_favorite})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500
