from flask import Blueprint, request, jsonify
from flask_cors import cross_origin
from database import cur, conn

interactions_bp = Blueprint('interactions_bp', __name__)

@interactions_bp.route('/interact', methods=['POST', 'OPTIONS'])
@cross_origin()
def handle_interaction():
    if request.method == 'OPTIONS':
        return jsonify({}), 200

    data = request.get_json()
    if not data or not data.get('username'):
        return jsonify({'error': 'Username is required'}), 400

    username = data.get('username')
    item = data.get('item', {})
    interaction_type = data.get('type') # 'like', 'dislike', 'save'

    if interaction_type not in ['like', 'dislike', 'save']:
        return jsonify({'error': 'Invalid interaction type'}), 400

    title = item.get('title', '')
    price = item.get('price', '')
    link = item.get('link', '')
    thumbnail = item.get('thumbnail', '')
    source = item.get('source', '')

    try:
        cur.execute("""
            INSERT INTO user_interactions (username, title, price, link, thumbnail, source, interaction_type)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (username, title, price, link, thumbnail, source, interaction_type))
        conn.commit()
        return jsonify({'message': f'Interaction {interaction_type} saved successfully'}), 200
    except Exception as e:
        conn.rollback()
        return jsonify({'error': 'Failed to save interaction', 'details': str(e)}), 500
