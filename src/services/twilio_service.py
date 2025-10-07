import os
from datetime import datetime
from twilio.rest import Client
from src.models.notification import Notification
from src.database import db

# Initialize Twilio
account_sid = os.getenv('TWILIO_ACCOUNT_SID')
auth_token = os.getenv('TWILIO_AUTH_TOKEN')
twilio_phone = os.getenv('TWILIO_PHONE_NUMBER')

twilio_client = Client(account_sid, auth_token) if account_sid and auth_token else None

class TwilioService:
    """Service for sending SMS notifications via Twilio"""
    
    @staticmethod
    def send_sms(to_phone, message, user_id=None, order_id=None):
        """Send an SMS message"""
        if not twilio_client:
            print("Twilio not configured - SMS not sent")
            return None
        
        try:
            # Create notification record
            notification = Notification(
                user_id=user_id,
                order_id=order_id,
                type='sms',
                message=message,
                recipient=to_phone,
                status='pending'
            )
            db.session.add(notification)
            db.session.flush()
            
            # Send SMS via Twilio
            twilio_message = twilio_client.messages.create(
                body=message,
                from_=twilio_phone,
                to=to_phone
            )
            
            # Update notification with Twilio SID
            notification.twilio_sid = twilio_message.sid
            notification.status = 'sent'
            notification.sent_at = datetime.utcnow()
            
            db.session.commit()
            
            return notification.to_dict()
            
        except Exception as e:
            print(f"Error sending SMS: {str(e)}")
            if notification:
                notification.status = 'failed'
                notification.failed_at = datetime.utcnow()
                notification.error_message = str(e)
                db.session.commit()
            raise
    
    @staticmethod
    def send_order_confirmation(order):
        """Send order confirmation SMS to customer"""
        message = f"""Go4me.ai Order Confirmed! 🎉

Order #{order.order_number}
Service: {order.service.name}
Total: ${float(order.total_amount):.2f}

We'll notify you when an agent accepts your order.

Track: https://go4me.ai/order/{order.order_number}"""
        
        return TwilioService.send_sms(
            to_phone=order.customer.phone,
            message=message,
            user_id=order.customer_id,
            order_id=order.id
        )
    
    @staticmethod
    def send_agent_assigned(order):
        """Notify customer that an agent has been assigned"""
        agent_name = order.agent.user.first_name
        
        message = f"""Your Go4me.ai order has been accepted! 🚀

Order #{order.order_number}
Agent: {agent_name}
Phone: {order.agent.user.phone}

{agent_name} will contact you shortly.

Track: https://go4me.ai/order/{order.order_number}"""
        
        return TwilioService.send_sms(
            to_phone=order.customer.phone,
            message=message,
            user_id=order.customer_id,
            order_id=order.id
        )
    
    @staticmethod
    def send_order_started(order):
        """Notify customer that order has started"""
        message = f"""Your gopher is on the way! 🏃

Order #{order.order_number}
Agent: {order.agent.user.first_name}

You'll receive updates as your task progresses.

Track: https://go4me.ai/order/{order.order_number}"""
        
        return TwilioService.send_sms(
            to_phone=order.customer.phone,
            message=message,
            user_id=order.customer_id,
            order_id=order.id
        )
    
    @staticmethod
    def send_order_completed(order):
        """Notify customer that order is complete"""
        message = f"""Your order is complete! ✅

Order #{order.order_number}
Total: ${float(order.total_amount):.2f}

Photos and receipts are available in your dashboard.

View: https://go4me.ai/order/{order.order_number}

Thank you for using Go4me.ai!"""
        
        return TwilioService.send_sms(
            to_phone=order.customer.phone,
            message=message,
            user_id=order.customer_id,
            order_id=order.id
        )
    
    @staticmethod
    def send_new_job_alert(agent, order):
        """Alert agent about a new available job"""
        message = f"""New Go4me.ai Job Available! 💼

Service: {order.service.name}
Pay: ${float(order.service_fee):.2f}
Location: {order.pickup_address or 'See app'}

Accept now: https://go4me.ai/agent/job/{order.id}"""
        
        return TwilioService.send_sms(
            to_phone=agent.user.phone,
            message=message,
            user_id=agent.user_id,
            order_id=order.id
        )
    
    @staticmethod
    def send_verification_code(phone, code):
        """Send verification code for phone verification"""
        message = f"""Your Go4me.ai verification code is: {code}

This code expires in 10 minutes.

Never share this code with anyone."""
        
        return TwilioService.send_sms(
            to_phone=phone,
            message=message
        )
