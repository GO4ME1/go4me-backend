import os
import stripe
from datetime import datetime
from src.models.payment import Payment
from src.database import db

# Initialize Stripe
stripe.api_key = os.getenv('STRIPE_SECRET_KEY')

class StripeService:
    """Service for handling Stripe payments"""
    
    @staticmethod
    def create_customer(user):
        """Create a Stripe customer for a user"""
        try:
            customer = stripe.Customer.create(
                email=user.email,
                name=user.full_name,
                phone=user.phone,
                metadata={
                    'user_id': user.id,
                    'role': user.role
                }
            )
            
            # Save Stripe customer ID to user
            user.stripe_customer_id = customer.id
            db.session.commit()
            
            return customer
        except stripe.error.StripeError as e:
            print(f"Stripe error creating customer: {str(e)}")
            raise
    
    @staticmethod
    def create_payment_intent(order, user):
        """Create a payment intent for an order"""
        try:
            # Ensure user has a Stripe customer ID
            if not user.stripe_customer_id:
                StripeService.create_customer(user)
            
            # Calculate amount in cents
            amount_cents = int(float(order.total_amount) * 100)
            
            # Create payment intent
            intent = stripe.PaymentIntent.create(
                amount=amount_cents,
                currency='usd',
                customer=user.stripe_customer_id,
                metadata={
                    'order_id': order.id,
                    'order_number': order.order_number,
                    'user_id': user.id
                },
                description=f"Go4me.ai Order #{order.order_number}",
                automatic_payment_methods={'enabled': True},
            )
            
            # Create payment record
            payment = Payment(
                user_id=user.id,
                order_id=order.id,
                stripe_payment_intent_id=intent.id,
                amount=order.total_amount,
                currency='usd',
                status='pending'
            )
            db.session.add(payment)
            db.session.commit()
            
            return {
                'client_secret': intent.client_secret,
                'payment_intent_id': intent.id,
                'amount': float(order.total_amount)
            }
            
        except stripe.error.StripeError as e:
            print(f"Stripe error creating payment intent: {str(e)}")
            raise
    
    @staticmethod
    def confirm_payment(payment_intent_id):
        """Confirm a payment was successful"""
        try:
            intent = stripe.PaymentIntent.retrieve(payment_intent_id)
            
            # Find payment record
            payment = Payment.query.filter_by(
                stripe_payment_intent_id=payment_intent_id
            ).first()
            
            if not payment:
                raise ValueError("Payment record not found")
            
            # Update payment status
            if intent.status == 'succeeded':
                payment.status = 'succeeded'
                payment.succeeded_at = datetime.utcnow()
                payment.stripe_charge_id = intent.charges.data[0].id if intent.charges.data else None
                
                # Get payment method details
                if intent.charges.data:
                    charge = intent.charges.data[0]
                    payment.payment_method_type = charge.payment_method_details.type
                    if charge.payment_method_details.card:
                        payment.last4 = charge.payment_method_details.card.last4
                
                # Update order status
                payment.order.status = 'pending'  # Ready for agent assignment
                
            elif intent.status == 'requires_payment_method':
                payment.status = 'failed'
                payment.failed_at = datetime.utcnow()
            
            db.session.commit()
            
            return payment.to_dict()
            
        except stripe.error.StripeError as e:
            print(f"Stripe error confirming payment: {str(e)}")
            raise
    
    @staticmethod
    def create_refund(payment_id, amount=None, reason=None):
        """Create a refund for a payment"""
        try:
            payment = Payment.query.get(payment_id)
            if not payment:
                raise ValueError("Payment not found")
            
            if not payment.stripe_charge_id:
                raise ValueError("No charge ID found for this payment")
            
            # Calculate refund amount (full refund if not specified)
            refund_amount_cents = int(float(amount or payment.amount) * 100)
            
            # Create refund in Stripe
            refund = stripe.Refund.create(
                charge=payment.stripe_charge_id,
                amount=refund_amount_cents,
                reason=reason or 'requested_by_customer',
                metadata={
                    'payment_id': payment.id,
                    'order_id': payment.order_id
                }
            )
            
            # Update payment record
            payment.status = 'refunded'
            payment.refund_amount = amount or payment.amount
            payment.refund_reason = reason
            payment.refunded_at = datetime.utcnow()
            
            db.session.commit()
            
            return refund
            
        except stripe.error.StripeError as e:
            print(f"Stripe error creating refund: {str(e)}")
            raise
    
    @staticmethod
    def webhook_handler(payload, sig_header):
        """Handle Stripe webhooks"""
        webhook_secret = os.getenv('STRIPE_WEBHOOK_SECRET')
        
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, webhook_secret
            )
            
            # Handle different event types
            if event.type == 'payment_intent.succeeded':
                payment_intent = event.data.object
                StripeService.confirm_payment(payment_intent.id)
                
            elif event.type == 'payment_intent.payment_failed':
                payment_intent = event.data.object
                payment = Payment.query.filter_by(
                    stripe_payment_intent_id=payment_intent.id
                ).first()
                if payment:
                    payment.status = 'failed'
                    payment.failed_at = datetime.utcnow()
                    db.session.commit()
            
            return {'status': 'success'}
            
        except ValueError as e:
            print(f"Webhook signature verification failed: {str(e)}")
            raise
        except stripe.error.SignatureVerificationError as e:
            print(f"Webhook signature verification failed: {str(e)}")
            raise
