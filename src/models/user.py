from datetime import datetime
from src.database import db
from werkzeug.security import generate_password_hash, check_password_hash

class User(db.Model):
    """User model for customers, agents, and admins"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    
    # User role: 'customer', 'agent', 'admin'
    role = db.Column(db.String(20), nullable=False, default='customer')
    
    # Account status
    is_active = db.Column(db.Boolean, default=True)
    is_verified = db.Column(db.Boolean, default=False)
    
    # Stripe customer ID
    stripe_customer_id = db.Column(db.String(100), unique=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    # Relationships
    orders = db.relationship('Order', back_populates='customer', foreign_keys='Order.customer_id', lazy='dynamic')
    agent_profile = db.relationship('Agent', back_populates='user', uselist=False)
    payments = db.relationship('Payment', back_populates='user', lazy='dynamic')
    
    def set_password(self, password):
        """Hash and set password"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Verify password"""
        return check_password_hash(self.password_hash, password)
    
    @property
    def full_name(self):
        """Get full name"""
        return f"{self.first_name} {self.last_name}"
    
    def to_dict(self, include_sensitive=False):
        """Convert user to dictionary"""
        data = {
            'id': self.id,
            'email': self.email,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'full_name': self.full_name,
            'phone': self.phone,
            'role': self.role,
            'is_active': self.is_active,
            'is_verified': self.is_verified,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None,
        }
        
        if include_sensitive:
            data['stripe_customer_id'] = self.stripe_customer_id
            data['updated_at'] = self.updated_at.isoformat() if self.updated_at else None
            
        return data
    
    def __repr__(self):
        return f'<User {self.email} ({self.role})>'
