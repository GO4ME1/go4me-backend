from flask import Blueprint, request, jsonify
from src.services.auth_service import token_required, role_required
from src.models.agent import Agent
from src.database import db

agent_bp = Blueprint('agents', __name__, url_prefix='/api/agents')

@agent_bp.route('/profile', methods=['GET'])
@token_required
@role_required('agent')
def get_agent_profile(current_user):
    """Get agent profile"""
    try:
        if not current_user.agent_profile:
            return jsonify({'error': 'Agent profile not found'}), 404
        
        return jsonify({
            'agent': current_user.agent_profile.to_dict(include_stats=True)
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to retrieve agent profile'}), 500


@agent_bp.route('/profile', methods=['PUT'])
@token_required
@role_required('agent')
def update_agent_profile(current_user):
    """Update agent profile"""
    try:
        if not current_user.agent_profile:
            return jsonify({'error': 'Agent profile not found'}), 404
        
        data = request.get_json()
        agent = current_user.agent_profile
        
        # Update allowed fields
        if 'bio' in data:
            agent.bio = data['bio']
        if 'profile_photo' in data:
            agent.profile_photo = data['profile_photo']
        
        db.session.commit()
        
        return jsonify({
            'message': 'Agent profile updated successfully',
            'agent': agent.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to update agent profile'}), 500


@agent_bp.route('/availability', methods=['PUT'])
@token_required
@role_required('agent')
def update_availability(current_user):
    """Toggle agent availability"""
    try:
        if not current_user.agent_profile:
            return jsonify({'error': 'Agent profile not found'}), 404
        
        data = request.get_json()
        agent = current_user.agent_profile
        
        if 'is_available' not in data:
            return jsonify({'error': 'is_available field required'}), 400
        
        agent.is_available = data['is_available']
        
        # Update location if provided
        if 'latitude' in data and 'longitude' in data:
            agent.current_location_lat = data['latitude']
            agent.current_location_lng = data['longitude']
        
        db.session.commit()
        
        return jsonify({
            'message': 'Availability updated successfully',
            'agent': agent.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to update availability'}), 500


@agent_bp.route('/stats', methods=['GET'])
@token_required
@role_required('agent')
def get_agent_stats(current_user):
    """Get agent statistics"""
    try:
        if not current_user.agent_profile:
            return jsonify({'error': 'Agent profile not found'}), 404
        
        agent = current_user.agent_profile
        
        return jsonify({
            'stats': {
                'total_jobs': agent.total_jobs,
                'completed_jobs': agent.completed_jobs,
                'cancelled_jobs': agent.cancelled_jobs,
                'completion_rate': agent.completion_rate,
                'average_rating': float(agent.average_rating) if agent.average_rating else 0,
                'total_earnings': float(agent.total_earnings) if agent.total_earnings else 0,
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to retrieve agent stats'}), 500


# Admin routes for managing agents
@agent_bp.route('/', methods=['GET'])
@token_required
@role_required('admin')
def get_all_agents(current_user):
    """Get all agents (admin only)"""
    try:
        agents = Agent.query.all()
        
        return jsonify({
            'agents': [agent.to_dict(include_stats=True) for agent in agents]
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to retrieve agents'}), 500


@agent_bp.route('/<int:agent_id>/background-check', methods=['PUT'])
@token_required
@role_required('admin')
def update_background_check(current_user, agent_id):
    """Update agent background check status (admin only)"""
    try:
        agent = Agent.query.get(agent_id)
        
        if not agent:
            return jsonify({'error': 'Agent not found'}), 404
        
        data = request.get_json()
        
        if 'status' not in data:
            return jsonify({'error': 'status field required'}), 400
        
        if data['status'] not in ['pending', 'approved', 'rejected']:
            return jsonify({'error': 'Invalid status'}), 400
        
        agent.background_check_status = data['status']
        
        if data['status'] == 'approved':
            from datetime import datetime
            agent.background_check_date = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'message': 'Background check status updated',
            'agent': agent.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to update background check'}), 500
