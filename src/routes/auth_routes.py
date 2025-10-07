from flask import Blueprint, request, jsonify
from src.services.auth_service import AuthService, token_required
from src.models.agent import Agent
from src.database import db

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

@auth_bp.route('/register', methods=['POST'])
def register():
    """Register a new user"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['email', 'password', 'first_name', 'last_name', 'phone']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Register user
        result = AuthService.register_user(
            email=data['email'],
            password=data['password'],
            first_name=data['first_name'],
            last_name=data['last_name'],
            phone=data['phone'],
            role=data.get('role', 'customer')
        )
        
        # If registering as agent, create agent profile
        if data.get('role') == 'agent':
            agent = Agent(
                user_id=result['user']['id'],
                bio=data.get('bio', ''),
                is_available=False,
                background_check_status='pending'
            )
            db.session.add(agent)
            db.session.commit()
        
        return jsonify({
            'message': 'Registration successful',
            'user': result['user'],
            'token': result['token']
        }), 201
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': 'Registration failed'}), 500


@auth_bp.route('/login', methods=['POST'])
def login():
    """Login user"""
    try:
        data = request.get_json()
        
        if 'email' not in data or 'password' not in data:
            return jsonify({'error': 'Email and password required'}), 400
        
        result = AuthService.login_user(
            email=data['email'],
            password=data['password']
        )
        
        return jsonify({
            'message': 'Login successful',
            'user': result['user'],
            'token': result['token']
        }), 200
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 401
    except Exception as e:
        return jsonify({'error': 'Login failed'}), 500


@auth_bp.route('/me', methods=['GET'])
@token_required
def get_current_user(current_user):
    """Get current user profile"""
    return jsonify({
        'user': current_user.to_dict()
    }), 200


@auth_bp.route('/me', methods=['PUT'])
@token_required
def update_profile(current_user):
    """Update user profile"""
    try:
        data = request.get_json()
        
        # Update allowed fields
        if 'first_name' in data:
            current_user.first_name = data['first_name']
        if 'last_name' in data:
            current_user.last_name = data['last_name']
        if 'phone' in data:
            current_user.phone = data['phone']
        
        db.session.commit()
        
        return jsonify({
            'message': 'Profile updated successfully',
            'user': current_user.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Profile update failed'}), 500


@auth_bp.route('/change-password', methods=['POST'])
@token_required
def change_password(current_user):
    """Change user password"""
    try:
        data = request.get_json()
        
        if 'current_password' not in data or 'new_password' not in data:
            return jsonify({'error': 'Current and new password required'}), 400
        
        # Verify current password
        if not current_user.check_password(data['current_password']):
            return jsonify({'error': 'Current password is incorrect'}), 401
        
        # Set new password
        current_user.set_password(data['new_password'])
        db.session.commit()
        
        return jsonify({'message': 'Password changed successfully'}), 200
        
    except Exception as e:
        return jsonify({'error': 'Password change failed'}), 500
