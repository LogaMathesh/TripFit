import os
import datetime
import hashlib
from PIL import Image
from flask import Blueprint, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename
from database import cur, conn
from config import Config
from ml_services.classifier import classify_all_attributes_efficient
from ml_services.per_user_index import add_image_for_user

uploads_bp = Blueprint('uploads_bp', __name__)

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}
def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

@uploads_bp.route('/classify', methods=['POST'])
def classify():
    image_file = request.files.get('image')
    username = request.form.get('username')

    if not image_file or not username:
        return jsonify({'error': 'Image or username missing'}), 400

    if not allowed_file(image_file.filename):
        return jsonify({'error': 'Unsupported file type'}), 400

    image_bytes = image_file.read()
    image_hash = hashlib.md5(image_bytes).hexdigest()

    cur.execute(
        "SELECT image_path, position, style, color FROM uploads WHERE username = %s AND md5_hash = %s",
        (username, image_hash)
    )
    existing = cur.fetchone()
    if existing:
        image_url = f"http://localhost:5000/image/{os.path.basename(existing[0])}"
        return jsonify({
            'position': existing[1], 'style': existing[2], 'color': existing[3],
            'message': 'Duplicate image already uploaded.', 'image_url': image_url
        })

    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    filename = secure_filename(f"{username}_{timestamp}_{image_file.filename}")
    file_path = os.path.join(Config.UPLOAD_FOLDER, filename)

    with open(file_path, 'wb') as f:
        f.write(image_bytes)

    try:
        img = Image.open(file_path)
    except Exception:
        if os.path.exists(file_path):
            os.remove(file_path)
        return jsonify({'error': 'Invalid image file'}), 400

    classification = classify_all_attributes_efficient(img)
    position = classification["position"]
    style = classification["style"]
    color = classification["color"]

    cur.execute(
        "INSERT INTO uploads (username, image_path, position, style, color, md5_hash, uploaded_at) VALUES (%s, %s, %s, %s, %s, %s, %s)",
        (username, file_path, position, style, color, image_hash, datetime.datetime.now())
    )
    conn.commit()

    try:
        add_image_for_user(username, file_path, style, color)
    except Exception as e:
        print(f"Warning: Failed to index image: {e}")

    image_url = f"http://localhost:5000/image/{filename}"
    return jsonify({'position': position, 'style': style, 'color': color, 'image_url': image_url})


@uploads_bp.route('/history/<username>', methods=['GET'])
def get_history(username):
    try:
        cur.execute(
            "SELECT id, image_path, position, style, color, uploaded_at, favorite FROM uploads WHERE username = %s ORDER BY uploaded_at DESC",
            (username,)
        )
        uploads = cur.fetchall()

        results = [{
            'id': u[0], 'image_url': f"http://localhost:5000/image/{os.path.basename(u[1])}",
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


@uploads_bp.route('/image/<filename>')
def get_image(filename):
    return send_from_directory(Config.UPLOAD_FOLDER, filename)


@uploads_bp.route('/get-suggestions', methods=['POST'])
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
        'uploaded_at': r[1], 'style': r[2], 'position': r[3]
    } for r in results]

    return jsonify({'suggestions': suggestions})


@uploads_bp.route('/uploaded_images/<path:filename>')
def serve_uploaded_image(filename):
    return send_from_directory(Config.UPLOAD_FOLDER, filename)


@uploads_bp.route('/toggle_favorite', methods=['POST'])
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
