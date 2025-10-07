import os
import jwt
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify
from src.models.user import User
from src.database import db

JWT_SECRET = os.getenv('JWT_SECRET_KEY', 'your-secret-key-change-in-production')
JWT_ALGORITHM = 'HS256'
JWT_EXP_DELTA_SECONDS = 86400 * 7  # 7 days

class AuthService:
    """Service for authentication and authorization"""
    
    @staticmethod
    def generate_token(user):
        """Generate JWT token for user"""
        payload = {
            'user_id': user.id,
            'email': user.email,
            'role': user.role,
            'exp': datetime.utcnow() + timedelta(seconds=JWT_EXP_DELTA_SECONDS),
            'iat': datetime.utcnow()
        }
        
        token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
        return token
    
    @staticmethod
    def decode_token(token):
        """Decode and verify JWT token"""
        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            return payload
        except jwt.ExpiredSignatureError:
            raise ValueError("Token has expired")
        except jwt.InvalidTokenError:
            raise ValueError("Invalid token")
    
    @staticmethod
    def register_user(email, password, first_name, last_name, phone, role='customer'):
        """Register a new user"""
        # Check if user already exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            raise ValueError("Email already registered")
        
        # Create new user
        user = User(
            email=email,
            first_name=first_name,
            last_name=last_name,
            phone=phone,
            role=role
        )
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        # Generate token
        token = AuthService.generate_token(user)
        
        return {
            'user': user.to_dict(),
            'token': token
        }
    
    @staticmethod
    def login_user(email, password):
        """Authenticate user and generate token"""
        user = User.query.filter_by(email=email).first()
        
        if not user or not user.check_password(password):
            raise ValueError("Invalid email or password")
        
        if not user.is_active:
            raise ValueError("Account is inactive")
        
        # Update last login
        user.last_login = datetime.utcnow()
        db.session.commit()
        
        # Generate token
        token = AuthService.generate_token(user)
        
        return {
            'user': user.to_dict(),
            'token': token
        }
    
    @staticmethod
    def get_current_user(token):
        """Get user from token"""
        payload = AuthService.decode_token(token)
        user = User.query.get(payload['user_id'])
        
        if not user or not user.is_active:
            raise ValueError("User not found or inactive")
        
        return user


def token_required(f):
    """Decorator to require authentication"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        # Get token from header
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            try:
                token = auth_header.split(" ")[1]  # Bearer <token>
            except IndexError:
                return jsonify({'error': 'Invalid authorization header'}), 401
        
        if not token:
            return jsonify({'error': 'Authentication token is missing'}), 401
        
        try:
            current_user = AuthService.get_current_user(token)
            return f(current_user=current_user, *args, **kwargs)
        except ValueError as e:
            return jsonify({'error': str(e)}), 401
    
    return decorated


def role_required(*roles):
    """Decorator to require specific role(s)"""
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            current_user = kwargs.get('current_user')
            
            if not current_user:
                return jsonify({'error': 'User not found'}), 401
            
            if current_user.role not in roles:
                return jsonify({'error': 'Insufficient permissions'}), 403
            
            return f(*args, **kwargs)
        
        return decorated
    return decorator
