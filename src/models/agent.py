from datetime import datetime
from src.database import db

class Agent(db.Model):
    """Agent/Gopher model"""
    __tablename__ = 'agents'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    
    # Agent details
    bio = db.Column(db.Text)
    profile_photo = db.Column(db.String(255))
    
    # Availability
    is_available = db.Column(db.Boolean, default=False)
    current_location_lat = db.Column(db.Float)
    current_location_lng = db.Column(db.Float)
    
    # Background check
    background_check_status = db.Column(db.String(20), default='pending')  # pending, approved, rejected
    background_check_date = db.Column(db.DateTime)
    
    # Statistics
    total_jobs = db.Column(db.Integer, default=0)
    completed_jobs = db.Column(db.Integer, default=0)
    cancelled_jobs = db.Column(db.Integer, default=0)
    average_rating = db.Column(db.Float, default=0.0)
    total_earnings = db.Column(db.Numeric(10, 2), default=0)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_active = db.Column(db.DateTime)
    
    # Relationships
    user = db.relationship('User', back_populates='agent_profile')
    orders = db.relationship('Order', back_populates='agent', lazy='dynamic')
    
    @property
    def completion_rate(self):
        """Calculate completion rate"""
        if self.total_jobs == 0:
            return 0
        return (self.completed_jobs / self.total_jobs) * 100
    
    def to_dict(self, include_stats=True):
        """Convert agent to dictionary"""
        data = {
            'id': self.id,
            'user_id': self.user_id,
            'bio': self.bio,
            'profile_photo': self.profile_photo,
            'is_available': self.is_available,
            'background_check_status': self.background_check_status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_active': self.last_active.isoformat() if self.last_active else None,
        }
        
        if include_stats:
            data.update({
                'total_jobs': self.total_jobs,
                'completed_jobs': self.completed_jobs,
                'average_rating': float(self.average_rating) if self.average_rating else 0,
                'completion_rate': self.completion_rate,
                'total_earnings': float(self.total_earnings) if self.total_earnings else 0,
            })
            
        if self.user:
            data['name'] = self.user.full_name
            data['phone'] = self.user.phone
            
        return data
    
    def __repr__(self):
        return f'<Agent {self.id} - {self.user.full_name if self.user else "Unknown"}>'
