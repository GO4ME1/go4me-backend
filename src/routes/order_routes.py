from flask import Blueprint, request, jsonify
from src.services.auth_service import token_required, role_required
from src.services.order_service import OrderService
from src.services.stripe_service import StripeService
from src.services.twilio_service import TwilioService
from src.models.order import Order
from src.models.service import Service

order_bp = Blueprint('orders', __name__, url_prefix='/api/orders')

@order_bp.route('/', methods=['POST'])
@token_required
def create_order(current_user):
    """Create a new order"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['service_id', 'description']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Create order
        order = OrderService.create_order(
            customer=current_user,
            service_id=data['service_id'],
            description=data['description'],
            pickup_address=data.get('pickup_address'),
            delivery_address=data.get('delivery_address'),
            special_instructions=data.get('special_instructions')
        )
        
        # Create payment intent
        payment_intent = StripeService.create_payment_intent(order, current_user)
        
        # Send confirmation SMS
        try:
            TwilioService.send_order_confirmation(order)
        except Exception as e:
            print(f"Failed to send SMS: {str(e)}")
        
        return jsonify({
            'message': 'Order created successfully',
            'order': order.to_dict(),
            'payment': payment_intent
        }), 201
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        print(f"Error creating order: {str(e)}")
        return jsonify({'error': 'Order creation failed'}), 500


@order_bp.route('/', methods=['GET'])
@token_required
def get_orders(current_user):
    """Get orders for current user"""
    try:
        status = request.args.get('status')
        
        if current_user.role == 'customer':
            orders = OrderService.get_customer_orders(current_user.id, status)
        elif current_user.role == 'agent':
            if not current_user.agent_profile:
                return jsonify({'error': 'Agent profile not found'}), 404
            orders = OrderService.get_agent_orders(current_user.agent_profile.id, status)
        elif current_user.role == 'admin':
            query = Order.query
            if status:
                query = query.filter_by(status=status)
            orders = query.order_by(Order.created_at.desc()).all()
        else:
            return jsonify({'error': 'Invalid user role'}), 403
        
        return jsonify({
            'orders': [order.to_dict() for order in orders]
        }), 200
        
    except Exception as e:
        print(f"Error getting orders: {str(e)}")
        return jsonify({'error': 'Failed to retrieve orders'}), 500


@order_bp.route('/<int:order_id>', methods=['GET'])
@token_required
def get_order(current_user, order_id):
    """Get specific order details"""
    try:
        order = Order.query.get(order_id)
        
        if not order:
            return jsonify({'error': 'Order not found'}), 404
        
        # Check permissions
        if current_user.role == 'customer' and order.customer_id != current_user.id:
            return jsonify({'error': 'Unauthorized'}), 403
        elif current_user.role == 'agent':
            if not current_user.agent_profile or order.agent_id != current_user.agent_profile.id:
                return jsonify({'error': 'Unauthorized'}), 403
        
        return jsonify({
            'order': order.to_dict(include_details=True)
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to retrieve order'}), 500


@order_bp.route('/available', methods=['GET'])
@token_required
@role_required('agent')
def get_available_orders(current_user):
    """Get orders available for agents to accept"""
    try:
        orders = OrderService.get_available_orders()
        
        return jsonify({
            'orders': [order.to_dict() for order in orders]
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to retrieve available orders'}), 500


@order_bp.route('/<int:order_id>/accept', methods=['POST'])
@token_required
@role_required('agent')
def accept_order(current_user, order_id):
    """Accept an order as an agent"""
    try:
        if not current_user.agent_profile:
            return jsonify({'error': 'Agent profile not found'}), 404
        
        order = OrderService.assign_agent(order_id, current_user.agent_profile.id)
        
        return jsonify({
            'message': 'Order accepted successfully',
            'order': order.to_dict()
        }), 200
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        print(f"Error accepting order: {str(e)}")
        return jsonify({'error': 'Failed to accept order'}), 500


@order_bp.route('/<int:order_id>/start', methods=['POST'])
@token_required
@role_required('agent')
def start_order(current_user, order_id):
    """Start working on an order"""
    try:
        order = OrderService.start_order(order_id)
        
        return jsonify({
            'message': 'Order started successfully',
            'order': order.to_dict()
        }), 200
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': 'Failed to start order'}), 500


@order_bp.route('/<int:order_id>/complete', methods=['POST'])
@token_required
@role_required('agent')
def complete_order(current_user, order_id):
    """Complete an order"""
    try:
        data = request.get_json()
        
        order = OrderService.complete_order(
            order_id=order_id,
            completion_notes=data.get('completion_notes'),
            completion_photos=data.get('completion_photos', []),
            receipt_photos=data.get('receipt_photos', []),
            additional_costs=data.get('additional_costs', 0)
        )
        
        return jsonify({
            'message': 'Order completed successfully',
            'order': order.to_dict()
        }), 200
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        print(f"Error completing order: {str(e)}")
        return jsonify({'error': 'Failed to complete order'}), 500


@order_bp.route('/<int:order_id>/cancel', methods=['POST'])
@token_required
def cancel_order(current_user, order_id):
    """Cancel an order"""
    try:
        data = request.get_json()
        
        order = OrderService.cancel_order(
            order_id=order_id,
            reason=data.get('reason')
        )
        
        return jsonify({
            'message': 'Order cancelled successfully',
            'order': order.to_dict()
        }), 200
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': 'Failed to cancel order'}), 500
