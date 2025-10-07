from flask import Blueprint, request, jsonify
from src.services.auth_service import token_required, role_required
from src.services.stripe_service import StripeService
from src.models.payment import Payment
from src.models.service import Service

payment_bp = Blueprint('payments', __name__, url_prefix='/api/payments')

@payment_bp.route('/webhook', methods=['POST'])
def stripe_webhook():
    """Handle Stripe webhooks"""
    try:
        payload = request.data
        sig_header = request.headers.get('Stripe-Signature')
        
        result = StripeService.webhook_handler(payload, sig_header)
        
        return jsonify(result), 200
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        print(f"Webhook error: {str(e)}")
        return jsonify({'error': 'Webhook processing failed'}), 500


@payment_bp.route('/<int:payment_id>', methods=['GET'])
@token_required
def get_payment(current_user, payment_id):
    """Get payment details"""
    try:
        payment = Payment.query.get(payment_id)
        
        if not payment:
            return jsonify({'error': 'Payment not found'}), 404
        
        # Check permissions
        if current_user.role != 'admin' and payment.user_id != current_user.id:
            return jsonify({'error': 'Unauthorized'}), 403
        
        return jsonify({
            'payment': payment.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to retrieve payment'}), 500


@payment_bp.route('/<int:payment_id>/refund', methods=['POST'])
@token_required
@role_required('admin')
def refund_payment(current_user, payment_id):
    """Refund a payment"""
    try:
        data = request.get_json()
        
        refund = StripeService.create_refund(
            payment_id=payment_id,
            amount=data.get('amount'),
            reason=data.get('reason')
        )
        
        return jsonify({
            'message': 'Refund processed successfully',
            'refund': {
                'id': refund.id,
                'amount': refund.amount / 100,
                'status': refund.status
            }
        }), 200
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        print(f"Refund error: {str(e)}")
        return jsonify({'error': 'Refund processing failed'}), 500


# Service routes
service_bp = Blueprint('services', __name__, url_prefix='/api/services')

@service_bp.route('/', methods=['GET'])
def get_services():
    """Get all active services"""
    try:
        services = Service.query.filter_by(is_active=True).order_by(Service.sort_order).all()
        
        return jsonify({
            'services': [service.to_dict() for service in services]
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to retrieve services'}), 500


@service_bp.route('/<slug>', methods=['GET'])
def get_service(slug):
    """Get specific service by slug"""
    try:
        service = Service.query.filter_by(slug=slug, is_active=True).first()
        
        if not service:
            return jsonify({'error': 'Service not found'}), 404
        
        return jsonify({
            'service': service.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to retrieve service'}), 500
