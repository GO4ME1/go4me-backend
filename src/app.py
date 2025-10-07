import os
from flask import Flask, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import database
from src.database import db, init_db

# Import routes
from src.routes.auth_routes import auth_bp
from src.routes.order_routes import order_bp
from src.routes.payment_routes import payment_bp, service_bp
from src.routes.agent_routes import agent_bp
from src.routes.simple_order_routes import simple_order_bp

def create_app():
    """Create and configure Flask application"""
    app = Flask(__name__)
    
    # Configuration
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key-change-in-production')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv(
        'DATABASE_URL',
        'sqlite:///go4me.db'  # Default to SQLite for development
    )
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['JSON_SORT_KEYS'] = False
    
    # Enable CORS - allow all origins for now
    CORS(app, resources={
        r"/*": {
            "origins": "*",
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"],
            "supports_credentials": False
        }
    })
    
    # Initialize database
    init_db(app)
    
    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(simple_order_bp)  # Simple order endpoint (no auth required)
    app.register_blueprint(order_bp)
    app.register_blueprint(payment_bp)
    app.register_blueprint(service_bp)
    app.register_blueprint(agent_bp)
    
    # Health check endpoint
    @app.route('/health', methods=['GET'])
    def health_check():
        return jsonify({
            'status': 'healthy',
            'service': 'Go4me.ai API',
            'version': '1.0.0'
        }), 200
    
    # Root endpoint
    @app.route('/', methods=['GET'])
    def root():
        return jsonify({
            'message': 'Welcome to Go4me.ai API',
            'version': '1.0.0',
            'endpoints': {
                'auth': '/api/auth',
                'orders': '/api/orders',
                'payments': '/api/payments',
                'services': '/api/services',
                'agents': '/api/agents'
            }
        }), 200
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'error': 'Resource not found'}), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({'error': 'Internal server error'}), 500
    
    return app


if __name__ == '__main__':
    app = create_app()
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
