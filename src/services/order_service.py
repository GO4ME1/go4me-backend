import random
import string
from datetime import datetime
from src.models.order import Order
from src.models.service import Service
from src.models.agent import Agent
from src.services.twilio_service import TwilioService
from src.database import db

class OrderService:
    """Service for managing orders"""
    
    @staticmethod
    def generate_order_number():
        """Generate unique order number"""
        while True:
            # Format: GO-XXXXXX (e.g., GO-A1B2C3)
            code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
            order_number = f"GO-{code}"
            
            # Check if unique
            existing = Order.query.filter_by(order_number=order_number).first()
            if not existing:
                return order_number
    
    @staticmethod
    def create_order(customer, service_id, description, pickup_address=None, 
                    delivery_address=None, special_instructions=None):
        """Create a new order"""
        # Get service
        service = Service.query.get(service_id)
        if not service or not service.is_active:
            raise ValueError("Service not available")
        
        # Generate order number
        order_number = OrderService.generate_order_number()
        
        # Create order
        order = Order(
            order_number=order_number,
            customer_id=customer.id,
            service_id=service_id,
            description=description,
            pickup_address=pickup_address,
            delivery_address=delivery_address,
            special_instructions=special_instructions,
            service_fee=service.base_price,
            total_amount=service.base_price,  # Will be updated with additional costs
            status='pending'
        )
        
        db.session.add(order)
        db.session.commit()
        
        return order
    
    @staticmethod
    def assign_agent(order_id, agent_id):
        """Assign an agent to an order"""
        order = Order.query.get(order_id)
        if not order:
            raise ValueError("Order not found")
        
        agent = Agent.query.get(agent_id)
        if not agent:
            raise ValueError("Agent not found")
        
        if not agent.is_available:
            raise ValueError("Agent is not available")
        
        # Assign agent
        order.agent_id = agent_id
        order.status = 'accepted'
        order.accepted_at = datetime.utcnow()
        
        # Update agent stats
        agent.total_jobs += 1
        agent.is_available = False  # Mark as busy
        
        db.session.commit()
        
        # Send notifications
        try:
            TwilioService.send_agent_assigned(order)
        except Exception as e:
            print(f"Failed to send SMS: {str(e)}")
        
        return order
    
    @staticmethod
    def start_order(order_id):
        """Mark order as started"""
        order = Order.query.get(order_id)
        if not order:
            raise ValueError("Order not found")
        
        if order.status != 'accepted':
            raise ValueError("Order must be accepted before starting")
        
        order.status = 'in_progress'
        order.started_at = datetime.utcnow()
        
        db.session.commit()
        
        # Send notification
        try:
            TwilioService.send_order_started(order)
        except Exception as e:
            print(f"Failed to send SMS: {str(e)}")
        
        return order
    
    @staticmethod
    def complete_order(order_id, completion_notes=None, completion_photos=None, 
                      receipt_photos=None, additional_costs=0):
        """Complete an order"""
        order = Order.query.get(order_id)
        if not order:
            raise ValueError("Order not found")
        
        if order.status != 'in_progress':
            raise ValueError("Order must be in progress to complete")
        
        # Update order
        order.status = 'completed'
        order.completed_at = datetime.utcnow()
        order.completion_notes = completion_notes
        order.completion_photos = completion_photos or []
        order.receipt_photos = receipt_photos or []
        order.additional_costs = additional_costs
        order.total_amount = float(order.service_fee) + float(additional_costs)
        
        # Update agent stats
        if order.agent:
            order.agent.completed_jobs += 1
            order.agent.total_earnings = float(order.agent.total_earnings or 0) + float(order.service_fee)
            order.agent.is_available = True  # Mark as available again
        
        db.session.commit()
        
        # Send notification
        try:
            TwilioService.send_order_completed(order)
        except Exception as e:
            print(f"Failed to send SMS: {str(e)}")
        
        return order
    
    @staticmethod
    def cancel_order(order_id, reason=None):
        """Cancel an order"""
        order = Order.query.get(order_id)
        if not order:
            raise ValueError("Order not found")
        
        if order.status in ['completed', 'cancelled']:
            raise ValueError("Cannot cancel completed or already cancelled order")
        
        order.status = 'cancelled'
        order.cancelled_at = datetime.utcnow()
        
        # If agent was assigned, update their stats and availability
        if order.agent:
            order.agent.cancelled_jobs += 1
            order.agent.is_available = True
        
        db.session.commit()
        
        return order
    
    @staticmethod
    def get_available_orders():
        """Get orders available for agents to accept"""
        return Order.query.filter_by(
            status='pending',
            agent_id=None
        ).order_by(Order.created_at.desc()).all()
    
    @staticmethod
    def get_customer_orders(customer_id, status=None):
        """Get orders for a customer"""
        query = Order.query.filter_by(customer_id=customer_id)
        
        if status:
            query = query.filter_by(status=status)
        
        return query.order_by(Order.created_at.desc()).all()
    
    @staticmethod
    def get_agent_orders(agent_id, status=None):
        """Get orders for an agent"""
        query = Order.query.filter_by(agent_id=agent_id)
        
        if status:
            query = query.filter_by(status=status)
        
        return query.order_by(Order.created_at.desc()).all()
