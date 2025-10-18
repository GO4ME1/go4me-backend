-- Go4me.ai Database Schema
-- PostgreSQL

-- Create orders table
CREATE TABLE IF NOT EXISTS orders (
  id SERIAL PRIMARY KEY,
  order_number VARCHAR(20) UNIQUE NOT NULL,
  service_type VARCHAR(50) NOT NULL,
  
  -- Customer information
  customer_name VARCHAR(100) NOT NULL,
  customer_email VARCHAR(100),
  customer_phone VARCHAR(20) NOT NULL,
  
  -- Delivery information
  delivery_address JSONB NOT NULL,
  delivery_preference VARCHAR(20) NOT NULL, -- 'meet' or 'leave'
  urgency VARCHAR(20) NOT NULL, -- 'standard', 'urgent', 'asap'
  
  -- Service-specific data
  innout_location VARCHAR(50),
  innout_order JSONB,
  grocery_order JSONB,
  task_details TEXT,
  special_instructions TEXT,
  
  -- Pricing
  subtotal DECIMAL(10,2) NOT NULL,
  tax DECIMAL(10,2) NOT NULL,
  total DECIMAL(10,2) NOT NULL,
  
  -- Payment information
  stripe_session_id VARCHAR(100),
  stripe_payment_intent VARCHAR(100),
  
  -- Status tracking
  status VARCHAR(20) DEFAULT 'pending', -- 'pending', 'assigned', 'in_progress', 'completed', 'cancelled'
  assigned_gopher_id INTEGER,
  
  -- Legal agreements
  agreed_to_terms BOOLEAN DEFAULT false,
  agreed_to_sms BOOLEAN DEFAULT false,
  agreed_to_marketing BOOLEAN DEFAULT false,
  
  -- Timestamps
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),
  completed_at TIMESTAMP
);

-- Create indexes for common queries
CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);
CREATE INDEX IF NOT EXISTS idx_orders_created_at ON orders(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_orders_customer_phone ON orders(customer_phone);
CREATE INDEX IF NOT EXISTS idx_orders_order_number ON orders(order_number);
CREATE INDEX IF NOT EXISTS idx_orders_service_type ON orders(service_type);

-- Create gophers table (for future use)
CREATE TABLE IF NOT EXISTS gophers (
  id SERIAL PRIMARY KEY,
  name VARCHAR(100) NOT NULL,
  phone VARCHAR(20) NOT NULL,
  email VARCHAR(100),
  status VARCHAR(20) DEFAULT 'active', -- 'active', 'inactive', 'busy'
  rating DECIMAL(3,2) DEFAULT 5.00,
  total_orders INTEGER DEFAULT 0,
  created_at TIMESTAMP DEFAULT NOW()
);

-- Create order_updates table (for tracking status changes)
CREATE TABLE IF NOT EXISTS order_updates (
  id SERIAL PRIMARY KEY,
  order_id INTEGER REFERENCES orders(id) ON DELETE CASCADE,
  status VARCHAR(20) NOT NULL,
  message TEXT,
  created_by VARCHAR(50), -- 'system', 'gopher', 'admin'
  created_at TIMESTAMP DEFAULT NOW()
);

-- Create trigger to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_orders_updated_at BEFORE UPDATE ON orders
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Insert sample gopher (for testing)
INSERT INTO gophers (name, phone, email, status) 
VALUES ('Test Gopher', '+15551234567', 'gopher@go4me.ai', 'active')
ON CONFLICT DO NOTHING;

-- Create view for order statistics
CREATE OR REPLACE VIEW order_stats AS
SELECT
  service_type,
  COUNT(*) as total_orders,
  SUM(total) as total_revenue,
  AVG(total) as avg_order_value,
  COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed_orders,
  COUNT(CASE WHEN status = 'pending' THEN 1 END) as pending_orders
FROM orders
GROUP BY service_type;

-- Create view for recent orders
CREATE OR REPLACE VIEW recent_orders AS
SELECT
  order_number,
  service_type,
  customer_name,
  customer_phone,
  total,
  status,
  urgency,
  created_at
FROM orders
ORDER BY created_at DESC
LIMIT 50;

COMMENT ON TABLE orders IS 'Main orders table storing all Go4me.ai bookings';
COMMENT ON TABLE gophers IS 'Gophers (service providers) table';
COMMENT ON TABLE order_updates IS 'Order status update history';
COMMENT ON VIEW order_stats IS 'Aggregated statistics by service type';
COMMENT ON VIEW recent_orders IS 'Most recent 50 orders for dashboard';

