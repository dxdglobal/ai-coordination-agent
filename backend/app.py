from flask import Flask
from flask_cors import CORS
from config import Config

def create_app():
    """Create and configure Flask application"""
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Initialize extensions
    from models.models import db
    db.init_app(app)
    
    # Configure CORS with specific settings
    CORS(app, resources={
        r"/ai/*": {
            "origins": ["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:5174", "http://127.0.0.1:5174"],
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"]
        },
        r"/api/*": {
            "origins": ["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:5174", "http://127.0.0.1:5174"],
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"]
        }
    })
    
    # Register blueprints
    from routes.api import api_bp
    from routes.integrations import integrations_bp
    from routes.ai import ai_bp
    from routes.auth import auth_bp
    from routes.projects_api import projects_bp
    from routes.crm_tasks_api import crm_tasks_api
    
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(integrations_bp, url_prefix='/integrations')
    app.register_blueprint(ai_bp, url_prefix='/ai')
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(projects_bp, url_prefix='/api/projects')
    app.register_blueprint(crm_tasks_api, url_prefix='/api')
    
    # Health check endpoint
    @app.route('/health')
    def health_check():
        return {'status': 'healthy', 'service': 'AI Coordination Agent'}
    
    return app

# Create app instance for imports
app = create_app()

if __name__ == '__main__':
    app.run(debug=False, host='127.0.0.1', port=5001)
