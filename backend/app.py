import os
import logging
from flask import Flask
from flask_cors import CORS
from config import Config

# Establish basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def create_app():
    # Initialize Flask App
    app = Flask(__name__)
    app.config.from_object(Config)
    CORS(app)

    # Register blueprints
    from routes.auth import auth_bp
    from routes.uploads import uploads_bp
    from routes.maintenance import maintenance_bp
    from routes.chatbot import chatbot_bp
    from routes.idea_search import idea_search_bp
    from routes.profile import profile_bp
    from async_tasks.routes import async_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(uploads_bp)
    app.register_blueprint(maintenance_bp)
    app.register_blueprint(chatbot_bp)
    app.register_blueprint(idea_search_bp)
    app.register_blueprint(profile_bp)
    app.register_blueprint(async_bp)

    return app

app = create_app()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
