from datetime import datetime
from src.database import db

class Service(db.Model):
    """Service types model"""
    __tablename__ = 'services'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    slug = db.Column(db.String(100), nullable=False, unique=True, index=True)
    description = db.Column(db.Text)
    tagline = db.Column(db.String(255))
    
    # Pricing
    base_price = db.Column(db.Numeric(10, 2), nullable=False)
    price_display = db.Column(db.String(50))  # e.g., "$10 + costs"
    
    # Service details
    icon = db.Column(db.String(10))  # Emoji icon
    estimated_time = db.Column(db.Integer)  # in minutes
    is_active = db.Column(db.Boolean, default=True)
    is_beta = db.Column(db.Boolean, default=False)
    
    # Display order
    sort_order = db.Column(db.Integer, default=0)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    orders = db.relationship('Order', back_populates='service', lazy='dynamic')
    
    def to_dict(self):
        """Convert service to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'slug': self.slug,
            'description': self.description,
            'tagline': self.tagline,
            'base_price': float(self.base_price) if self.base_price else 0,
            'price_display': self.price_display,
            'icon': self.icon,
            'estimated_time': self.estimated_time,
            'is_active': self.is_active,
            'is_beta': self.is_beta,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
    
    def __repr__(self):
        return f'<Service {self.name}>'
