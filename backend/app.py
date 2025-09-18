from flask import Flask
from flask_cors import CORS
from config import Config
import os

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Initialize extensions
    from models.models import db
    db.init_app(app)
    CORS(app)
    
    # Register blueprints
    from routes.api import api_bp
    from routes.integrations import integrations_bp
    from routes.ai import ai_bp
    
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(integrations_bp, url_prefix='/integrations')
    app.register_blueprint(ai_bp, url_prefix='/ai')
    
    # Create tables
    with app.app_context():
        db.create_all()
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000)