from datetime import datetime
from src.database import db

class Payment(db.Model):
    """Payment transactions model"""
    __tablename__ = 'payments'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Relationships
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    
    # Stripe details
    stripe_payment_intent_id = db.Column(db.String(100), unique=True)
    stripe_charge_id = db.Column(db.String(100))
    
    # Payment details
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    currency = db.Column(db.String(3), default='usd')
    
    # Status: 'pending', 'processing', 'succeeded', 'failed', 'refunded'
    status = db.Column(db.String(20), default='pending', nullable=False, index=True)
    
    # Payment method
    payment_method_type = db.Column(db.String(50))  # card, etc.
    last4 = db.Column(db.String(4))  # Last 4 digits of card
    
    # Refund details
    refund_amount = db.Column(db.Numeric(10, 2), default=0)
    refund_reason = db.Column(db.String(255))
    refunded_at = db.Column(db.DateTime)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    succeeded_at = db.Column(db.DateTime)
    failed_at = db.Column(db.DateTime)
    
    # Relationships
    user = db.relationship('User', back_populates='payments')
    order = db.relationship('Order', back_populates='payment')
    
    def to_dict(self):
        """Convert payment to dictionary"""
        return {
            'id': self.id,
            'order_id': self.order_id,
            'amount': float(self.amount) if self.amount else 0,
            'currency': self.currency,
            'status': self.status,
            'payment_method_type': self.payment_method_type,
            'last4': self.last4,
            'refund_amount': float(self.refund_amount) if self.refund_amount else 0,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'succeeded_at': self.succeeded_at.isoformat() if self.succeeded_at else None,
            'failed_at': self.failed_at.isoformat() if self.failed_at else None,
            'refunded_at': self.refunded_at.isoformat() if self.refunded_at else None,
        }
    
    def __repr__(self):
        return f'<Payment {self.id} - ${self.amount} ({self.status})>'
