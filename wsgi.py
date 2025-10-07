"""WSGI entry point for production deployment"""
import sys
import os

# Add the project directory to the path
sys.path.insert(0, os.path.dirname(__file__))

# Set environment variables
os.environ['PYTHONPATH'] = os.path.dirname(__file__)

# Import the Flask app
from src.app import create_app

# Create the app instance
app = create_app()

if __name__ == "__main__":
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
