import os
import stripe
from datetime import datetime
from flask import Blueprint, request, jsonify
from twilio.rest import Client

simple_order_bp = Blueprint('simple_orders', __name__, url_prefix='/api/orders')

# Initialize Stripe
stripe.api_key = os.getenv('STRIPE_SECRET_KEY')
FRONTEND_URL = os.getenv('FRONTEND_URL', 'https://go4me-ar7jjn.manus.space')

# Initialize Twilio
twilio_client = Client(
    os.getenv('TWILIO_ACCOUNT_SID'),
    os.getenv('TWILIO_AUTH_TOKEN')
)
TWILIO_PHONE = os.getenv('TWILIO_PHONE_NUMBER')

def send_sms(to_phone, message):
    """Send SMS via Twilio"""
    try:
        # Format phone number
        if not to_phone.startswith('+'):
            to_phone = '+1' + to_phone.replace('-', '').replace('(', '').replace(')', '').replace(' ', '')
        
        message = twilio_client.messages.create(
            body=message,
            from_=TWILIO_PHONE,
            to=to_phone
        )
        print(f"SMS sent successfully to {to_phone}: {message.sid}")
        return True
    except Exception as e:
        print(f"Failed to send SMS to {to_phone}: {str(e)}")
        return False

@simple_order_bp.route('/create', methods=['POST'])
def create_order():
    """Create a new order and return Stripe checkout URL"""
    try:
        data = request.get_json()
        
        # Calculate total price
        if data.get('service') == 'innout':
            # Calculate food total
            food_total = 0
            for item in data.get('innoutOrder', []):
                food_total += item['price'] * item['quantity']
            
            total = food_total + 10  # $10 delivery fee
            service_name = "In-N-Out Delivery"
            
        else:
            # Other services - fixed pricing
            service_prices = {
                'dmv': 95,
                'eyes-on': 60,
                'lost-found': 40,
                'dry-cleaning': 15,
                'custom': 50  # Default for custom
            }
            total = service_prices.get(data.get('service'), 50)
            service_name = data.get('service', 'Service').replace('-', ' ').title()
        
        # Create Stripe Checkout Session
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'usd',
                    'product_data': {
                        'name': f"Go4me.ai - {service_name}",
                        'description': f"Order for {data.get('name', 'Customer')}",
                    },
                    'unit_amount': int(total * 100),  # Convert to cents
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url=f"{FRONTEND_URL}/success?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{FRONTEND_URL}/new-task",
            metadata={
                'customer_name': data.get('name', ''),
                'customer_phone': data.get('phone', ''),
                'service': data.get('service', ''),
                'delivery_address': f"{data.get('street', '')} {data.get('city', '')} {data.get('state', '')} {data.get('zip', '')}",
                'order_data': str(data)  # Store full order data
            }
        )
        
        # TODO: Save order to database here
        # For now, just return the checkout URL
        
        return jsonify({
            'success': True,
            'checkout_url': checkout_session.url,
            'session_id': checkout_session.id,
            'total': total
        }), 200
        
    except Exception as e:
        print(f"Error creating order: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@simple_order_bp.route('/success', methods=['GET'])
def order_success():
    """Handle successful payment"""
    session_id = request.args.get('session_id')
    
    if not session_id:
        return jsonify({'error': 'No session ID provided'}), 400
    
    try:
        # Retrieve the session from Stripe
        session = stripe.checkout.Session.retrieve(session_id)
        
        # Send confirmation SMS to customer
        if session.payment_status == 'paid':
            customer_phone = session.metadata.get('customer_phone')
            customer_name = session.metadata.get('customer_name', 'Customer')
            service = session.metadata.get('service', 'service')
            
            if customer_phone:
                message = f"🎉 Order confirmed! Hi {customer_name}, your {service} order has been received and a gopher will be assigned shortly. Track your order at: {FRONTEND_URL}/tracking"
                send_sms(customer_phone, message)
                
                # TODO: Notify available gophers about new order
                # For now, we'll just log it
                print(f"New order ready for gopher assignment: {session_id}")
        
        return jsonify({
            'success': True,
            'payment_status': session.payment_status,
            'customer_email': session.customer_details.email if session.customer_details else None
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@simple_order_bp.route('/notify-gopher', methods=['POST'])
def notify_gopher():
    """Send SMS to notify gopher about new order"""
    try:
        data = request.get_json()
        gopher_phone = data.get('gopher_phone')
        order_details = data.get('order_details', 'New order available')
        
        if not gopher_phone:
            return jsonify({'error': 'Gopher phone number required'}), 400
        
        message = f"🚀 New Go4me.ai run available! {order_details}. Accept in the app to start earning!"
        
        if send_sms(gopher_phone, message):
            return jsonify({'success': True, 'message': 'Gopher notified'}), 200
        else:
            return jsonify({'success': False, 'error': 'Failed to send SMS'}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500
