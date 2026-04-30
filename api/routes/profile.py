from flask import Blueprint, request, jsonify
from database import get_connection

profile_bp = Blueprint('profile_bp', __name__)

@profile_bp.route('/profile', methods=['GET', 'POST', 'OPTIONS'])
def handle_profile():
    if request.method == 'OPTIONS':
        return jsonify({}), 200

    if request.method == 'GET':
        username = request.args.get('username')
        if not username:
            return jsonify({'error': 'Username is required'}), 400

        conn = get_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                SELECT gender, budget_level, sizes, style_preferences
                FROM user_profiles WHERE username = %s
            """, (username,))
            row = cur.fetchone()
            
            if row:
                return jsonify({
                    'gender': row[0] or '',
                    'budget_level': row[1] or '',
                    'sizes': row[2] or '',
                    'style_preferences': row[3] or ''
                }), 200
            else:
                return jsonify({
                    'gender': '',
                    'budget_level': '',
                    'sizes': '',
                    'style_preferences': ''
                }), 200
        except Exception as e:
            return jsonify({'error': 'Failed to fetch profile', 'details': str(e)}), 500
        finally:
            cur.close()
            conn.close()

    elif request.method == 'POST':
        data = request.get_json()
        if not data or not data.get('username'):
            return jsonify({'error': 'Username is required'}), 400

        username = data.get('username')
        gender = data.get('gender', '')
        budget_level = data.get('budget_level', '')
        sizes = data.get('sizes', '')
        style_preferences = data.get('style_preferences', '')

        conn = get_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                INSERT INTO user_profiles (username, gender, budget_level, sizes, style_preferences)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (username) DO UPDATE 
                SET gender = EXCLUDED.gender,
                    budget_level = EXCLUDED.budget_level,
                    sizes = EXCLUDED.sizes,
                    style_preferences = EXCLUDED.style_preferences,
                    updated_at = CURRENT_TIMESTAMP;
            """, (username, gender, budget_level, sizes, style_preferences))
            conn.commit()
            
            return jsonify({'message': 'Profile saved successfully'}), 200
        except Exception as e:
            conn.rollback()
            return jsonify({'error': 'Failed to save profile', 'details': str(e)}), 500
        finally:
            cur.close()
            conn.close()
