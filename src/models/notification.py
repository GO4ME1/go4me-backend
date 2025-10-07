from datetime import datetime
from src.database import db

class Notification(db.Model):
    """Notification log for SMS/Email"""
    __tablename__ = 'notifications'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Relationships
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=True)
    
    # Notification details
    type = db.Column(db.String(20), nullable=False)  # 'sms', 'email'
    subject = db.Column(db.String(255))
    message = db.Column(db.Text, nullable=False)
    
    # Delivery details
    recipient = db.Column(db.String(255), nullable=False)  # phone or email
    status = db.Column(db.String(20), default='pending')  # pending, sent, failed
    
    # External IDs
    twilio_sid = db.Column(db.String(100))  # Twilio message SID
    sendgrid_id = db.Column(db.String(100))  # SendGrid message ID
    
    # Error tracking
    error_message = db.Column(db.Text)
    retry_count = db.Column(db.Integer, default=0)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    sent_at = db.Column(db.DateTime)
    failed_at = db.Column(db.DateTime)
    
    # Relationships
    user = db.relationship('User', backref='notifications')
    order = db.relationship('Order', back_populates='notifications')
    
    def to_dict(self):
        """Convert notification to dictionary"""
        return {
            'id': self.id,
            'type': self.type,
            'subject': self.subject,
            'message': self.message,
            'recipient': self.recipient,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'sent_at': self.sent_at.isoformat() if self.sent_at else None,
            'failed_at': self.failed_at.isoformat() if self.failed_at else None,
        }
    
    def __repr__(self):
        return f'<Notification {self.type} to {self.recipient} - {self.status}>'
