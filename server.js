require('dotenv').config();
const express = require('express');
const cors = require('cors');
const stripe = require('stripe')(process.env.STRIPE_SECRET_KEY);
const twilio = require('twilio');
const { Pool } = require('pg');

const app = express();
const PORT = process.env.PORT || 3000;

// Middleware
app.use(cors());

// Database connection
const pool = new Pool({
  connectionString: process.env.DATABASE_URL,
  ssl: process.env.NODE_ENV === 'production' ? { rejectUnauthorized: false } : false
});

// Twilio client
const twilioClient = process.env.TWILIO_ACCOUNT_SID && process.env.TWILIO_AUTH_TOKEN
  ? twilio(process.env.TWILIO_ACCOUNT_SID, process.env.TWILIO_AUTH_TOKEN)
  : null;

// Export dependencies for routes
module.exports = { app, pool, twilioClient, stripe };

// Health check endpoint
app.get('/health', (req, res) => {
  res.json({ 
    status: 'ok', 
    timestamp: new Date().toISOString(),
    stripe: !!process.env.STRIPE_SECRET_KEY,
    twilio: !!twilioClient,
    database: !!process.env.DATABASE_URL
  });
});

// Import routes after exports to avoid circular dependency
const checkoutRoutes = require('./routes/checkout');
const webhookRoutes = require('./routes/webhook');

// Apply JSON middleware for most routes
app.use('/api/create-checkout-session', express.json());
app.use('/api', checkoutRoutes);
app.use('/api', webhookRoutes);

// Error handling middleware
app.use((err, req, res, next) => {
  console.error('Error:', err);
  res.status(500).json({ 
    error: 'Internal server error',
    message: process.env.NODE_ENV === 'development' ? err.message : undefined
  });
});

// Start server
app.listen(PORT, () => {
  console.log(`🚀 Go4me.ai Backend API running on port ${PORT}`);
  console.log(`📝 Health check: http://localhost:${PORT}/health`);
  console.log(`💳 Stripe: ${process.env.STRIPE_SECRET_KEY ? '✅ Configured' : '❌ Not configured'}`);
  console.log(`📱 Twilio: ${twilioClient ? '✅ Configured' : '❌ Not configured'}`);
  console.log(`🗄️  Database: ${process.env.DATABASE_URL ? '✅ Configured' : '❌ Not configured'}`);
});

