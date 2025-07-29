"""
Cancer Data Analysis Platform - Main Flask Application
"""

import os
from flask import Flask
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from config.config import Config

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()

def create_app(config_class=Config):
    """Application factory pattern"""
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    CORS(app, origins=['http://localhost:3000'])  # Allow React frontend
    
    # Register blueprints
    from app.routes.data_routes import data_bp
    from app.routes.ml_routes import ml_bp
    from app.routes.visualization_routes import viz_bp
    from app.routes.auth_routes import auth_bp
    
    app.register_blueprint(data_bp, url_prefix='/api/data')
    app.register_blueprint(ml_bp, url_prefix='/api/ml')
    app.register_blueprint(viz_bp, url_prefix='/api/viz')
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    
    # Health check endpoint
    @app.route('/api/health')
    def health_check():
        return {'status': 'healthy', 'service': 'cancer-analysis-platform'}
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000)