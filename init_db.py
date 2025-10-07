#!/usr/bin/env python3
"""Initialize database with sample data"""

from src.app import create_app
from src.database import db
from src.models import User, Service, Agent
from datetime import datetime

def init_database():
    """Initialize database with tables and sample data"""
    app = create_app()
    
    with app.app_context():
        # Drop all tables and recreate (WARNING: This deletes all data!)
        print("Creating database tables...")
        db.drop_all()
        db.create_all()
        
        # Create sample services
        print("Creating services...")
        services = [
            Service(
                name='In-N-Out Runs',
                slug='innout',
                description='Hot, fresh In-N-Out delivered to your door. We wait in line so you don\'t have to.',
                tagline='They wait. You eat.',
                base_price=10.00,
                price_display='$10 + food costs',
                icon='🍴',
                estimated_time=45,
                is_active=True,
                sort_order=1
            ),
            Service(
                name='DMV Proxy',
                slug='dmv',
                description='Skip the DMV nightmare. We handle registration, renewals, and more.',
                tagline='We brave the line.',
                base_price=12.00,
                price_display='$12 + DMV fees',
                icon='📄',
                estimated_time=120,
                is_active=True,
                sort_order=2
            ),
            Service(
                name='Eyes On',
                slug='eyes-on',
                description='Visual verification services. Get photo/video proof of anything, anywhere.',
                tagline='Photo/video proof on-site.',
                base_price=9.00,
                price_display='$9-12',
                icon='📷',
                estimated_time=30,
                is_active=True,
                sort_order=3
            ),
            Service(
                name='Lost & Found',
                slug='lost-found',
                description='Forgot something? We\'ll retrieve it for you.',
                tagline='Forgot it? We fetch it.',
                base_price=9.00,
                price_display='$9-12',
                icon='📦',
                estimated_time=60,
                is_active=True,
                sort_order=4
            ),
            Service(
                name='Dry Cleaning',
                slug='dry-cleaning',
                description='Pickup and drop-off dry cleaning service.',
                tagline='Pickup, drop, done.',
                base_price=10.00,
                price_display='$10 + cleaning costs',
                icon='👕',
                estimated_time=30,
                is_active=True,
                sort_order=5
            ),
            Service(
                name='Open Request',
                slug='custom',
                description='Have a unique task? Name it and we\'ll find an agent to handle it.',
                tagline='Name your task. We\'ll find an agent. (Beta)',
                base_price=15.00,
                price_display='Starting at $15',
                icon='✓',
                estimated_time=90,
                is_active=True,
                is_beta=True,
                sort_order=6
            ),
        ]
        
        for service in services:
            db.session.add(service)
        
        # Create sample admin user
        print("Creating admin user...")
        admin = User(
            email='admin@go4me.ai',
            first_name='Admin',
            last_name='User',
            phone='+15555551234',
            role='admin',
            is_active=True,
            is_verified=True
        )
        admin.set_password('admin123')  # Change this in production!
        db.session.add(admin)
        
        # Create sample customer
        print("Creating sample customer...")
        customer = User(
            email='customer@example.com',
            first_name='John',
            last_name='Doe',
            phone='+15555555678',
            role='customer',
            is_active=True,
            is_verified=True
        )
        customer.set_password('password123')
        db.session.add(customer)
        
        # Create sample agent
        print("Creating sample agent...")
        agent_user = User(
            email='agent@example.com',
            first_name='Jane',
            last_name='Smith',
            phone='+15555559012',
            role='agent',
            is_active=True,
            is_verified=True
        )
        agent_user.set_password('password123')
        db.session.add(agent_user)
        db.session.flush()  # Get the user ID
        
        agent_profile = Agent(
            user_id=agent_user.id,
            bio='Experienced gopher ready to help with any task!',
            is_available=True,
            background_check_status='approved',
            background_check_date=datetime.utcnow(),
            total_jobs=25,
            completed_jobs=23,
            cancelled_jobs=2,
            average_rating=4.8,
            total_earnings=575.00
        )
        db.session.add(agent_profile)
        
        # Commit all changes
        db.session.commit()
        
        print("\n✅ Database initialized successfully!")
        print("\nSample accounts created:")
        print("  Admin:    admin@go4me.ai / admin123")
        print("  Customer: customer@example.com / password123")
        print("  Agent:    agent@example.com / password123")
        print("\n⚠️  Remember to change these passwords in production!")

if __name__ == '__main__':
    init_database()
