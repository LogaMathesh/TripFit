from flask import Blueprint, request, jsonify
from services.gemini_service import suggest_matching_items
from database import get_connection

# Create blueprint for chatbot routes
chatbot_bp = Blueprint('chatbot', __name__)

@chatbot_bp.route('/chatbot/query', methods=['POST'])
def chatbot_query():
    """Query chatbot for similar images"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
        
        user_id = data.get('user_id')
        query_text = data.get('query', '').strip()
        
        if not user_id:
            return jsonify({'error': 'User ID required'}), 400
        
        if not query_text:
            return jsonify({'error': 'Query text required'}), 400
        
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT image_path, style, color, position, gemini_metadata FROM uploads WHERE username = %s", (user_id,))
        rows = cur.fetchall()
        cur.close()
        conn.close()
        
        wardrobe_items = []
        for r in rows:
            url = r[0]
            meta = r[4] if r[4] else {}
            wardrobe_items.append({
                'url': url,
                'style': r[1],
                'color': r[2],
                'position': r[3],
                'metadata': meta
            })

        # If no items, return empty
        if not wardrobe_items:
            return jsonify({
                'results': [],
                'query': query_text,
                'count': 0
            }), 200

        # Ask Gemini to rank items
        matched_urls = suggest_matching_items(query_text, wardrobe_items)
        
        formatted_results = []
        for url in matched_urls:
            # find style, color for this url
            item = next((x for x in wardrobe_items if x['url'] == url), None)
            if item:
                formatted_results.append({
                    'url': url,
                    'style': item['style'],
                    'color': item['color'],
                    'score': 1.0 # Placeholder since Gemini doesn't return exact distances
                })
        
        return jsonify({
            'results': formatted_results,
            'query': query_text,
            'count': len(formatted_results)
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Query failed: {str(e)}'}), 500

@chatbot_bp.route('/chatbot/status', methods=['GET'])
def chatbot_status():
    """Check chatbot service status"""
    return jsonify({
        'status': 'active',
        'message': 'Chatbot service is running'
    }), 200
