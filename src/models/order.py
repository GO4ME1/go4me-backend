from datetime import datetime
from src.database import db

class Order(db.Model):
    """Order model for service requests"""
    __tablename__ = 'orders'
    
    id = db.Column(db.Integer, primary_key=True)
    order_number = db.Column(db.String(20), unique=True, nullable=False, index=True)
    
    # Relationships
    customer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    agent_id = db.Column(db.Integer, db.ForeignKey('agents.id'), nullable=True)
    service_id = db.Column(db.Integer, db.ForeignKey('services.id'), nullable=False)
    
    # Order details
    description = db.Column(db.Text, nullable=False)
    special_instructions = db.Column(db.Text)
    
    # Location
    pickup_address = db.Column(db.String(255))
    delivery_address = db.Column(db.String(255))
    
    # Status: 'pending', 'accepted', 'in_progress', 'completed', 'cancelled'
    status = db.Column(db.String(20), default='pending', nullable=False, index=True)
    
    # Pricing
    service_fee = db.Column(db.Numeric(10, 2), nullable=False)  # Base fee
    additional_costs = db.Column(db.Numeric(10, 2), default=0)  # Food, DMV fees, etc.
    total_amount = db.Column(db.Numeric(10, 2), nullable=False)
    
    # Proof & Documentation
    completion_photos = db.Column(db.JSON)  # Array of photo URLs
    receipt_photos = db.Column(db.JSON)  # Array of receipt URLs
    completion_notes = db.Column(db.Text)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    accepted_at = db.Column(db.DateTime)
    started_at = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)
    cancelled_at = db.Column(db.DateTime)
    
    # Relationships
    customer = db.relationship('User', back_populates='orders', foreign_keys=[customer_id])
    agent = db.relationship('Agent', back_populates='orders')
    service = db.relationship('Service', back_populates='orders')
    payment = db.relationship('Payment', back_populates='order', uselist=False)
    notifications = db.relationship('Notification', back_populates='order', lazy='dynamic')
    
    def to_dict(self, include_details=True):
        """Convert order to dictionary"""
        data = {
            'id': self.id,
            'order_number': self.order_number,
            'status': self.status,
            'service_fee': float(self.service_fee) if self.service_fee else 0,
            'additional_costs': float(self.additional_costs) if self.additional_costs else 0,
            'total_amount': float(self.total_amount) if self.total_amount else 0,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
        }
        
        if include_details:
            data.update({
                'description': self.description,
                'special_instructions': self.special_instructions,
                'pickup_address': self.pickup_address,
                'delivery_address': self.delivery_address,
                'completion_photos': self.completion_photos or [],
                'receipt_photos': self.receipt_photos or [],
                'completion_notes': self.completion_notes,
                'accepted_at': self.accepted_at.isoformat() if self.accepted_at else None,
                'started_at': self.started_at.isoformat() if self.started_at else None,
                'cancelled_at': self.cancelled_at.isoformat() if self.cancelled_at else None,
            })
            
            if self.customer:
                data['customer'] = self.customer.to_dict()
            if self.agent:
                data['agent'] = self.agent.to_dict()
            if self.service:
                data['service'] = self.service.to_dict()
                
        return data
    
    def __repr__(self):
        return f'<Order {self.order_number} - {self.status}>'
