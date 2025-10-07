from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

db = SQLAlchemy()
migrate = Migrate()

def init_db(app):
    """Initialize database with app"""
    db.init_app(app)
    migrate.init_app(app, db)
    
    with app.app_context():
        # Import all models here to ensure they're registered
        from src.models import user, order, agent, service, payment, notification
        
        # Create all tables
        db.create_all()
        
    return db
