const express = require('express');
const router = express.Router();
const { stripe, pool, twilioClient } = require('../server');
const { sendCustomerConfirmation, sendGopherNotification } = require('../utils/sms');

/**
 * POST /api/webhook/stripe
 * Handles Stripe webhook events
 * 
 * IMPORTANT: This endpoint needs raw body, not JSON parsed
 * In production, you'll need to use express.raw() for this specific route
 */
router.post('/webhook/stripe', express.raw({ type: 'application/json' }), async (req, res) => {
  const sig = req.headers['stripe-signature'];
  const webhookSecret = process.env.STRIPE_WEBHOOK_SECRET;

  let event;

  try {
    // Verify webhook signature
    event = stripe.webhooks.constructEvent(req.body, sig, webhookSecret);
  } catch (err) {
    console.error('⚠️  Webhook signature verification failed:', err.message);
    return res.status(400).send(`Webhook Error: ${err.message}`);
  }

  // Handle the event
  switch (event.type) {
    case 'checkout.session.completed':
      const session = event.data.object;
      await handleCheckoutComplete(session);
      break;

    case 'payment_intent.succeeded':
      console.log('💳 Payment succeeded:', event.data.object.id);
      break;

    case 'payment_intent.payment_failed':
      console.log('❌ Payment failed:', event.data.object.id);
      break;

    default:
      console.log(`Unhandled event type: ${event.type}`);
  }

  // Return a 200 response to acknowledge receipt of the event
  res.json({ received: true });
});

/**
 * Handle completed checkout session
 */
async function handleCheckoutComplete(session) {
  try {
    console.log('✅ Checkout completed:', session.id);

    const metadata = session.metadata;

    // Parse JSON fields
    const innoutOrder = metadata.innoutOrder ? JSON.parse(metadata.innoutOrder) : null;
    const groceryOrder = metadata.groceryOrder ? JSON.parse(metadata.groceryOrder) : null;

    // Save order to database
    const orderData = {
      orderNumber: metadata.orderNumber,
      service: metadata.service,
      customerName: metadata.customerName,
      customerEmail: metadata.customerEmail || session.customer_email || null,
      customerPhone: metadata.customerPhone,
      address: {
        street: metadata.addressStreet,
        city: metadata.addressCity,
        state: metadata.addressState,
        zip: metadata.addressZip,
        gateCode: metadata.addressGateCode || null,
      },
      deliveryPreference: metadata.deliveryPreference,
      urgency: metadata.urgency,
      innoutLocation: metadata.innoutLocation || null,
      innoutOrder,
      groceryOrder,
      taskDetails: metadata.taskDetails || null,
      specialInstructions: metadata.specialInstructions || null,
      subtotal: parseFloat(metadata.subtotal),
      tax: parseFloat(metadata.tax),
      total: parseFloat(metadata.total),
      stripeSessionId: session.id,
      stripePaymentIntent: session.payment_intent,
      status: 'pending',
      agreedToTerms: metadata.agreedToTerms === 'true',
      agreedToSms: metadata.agreedToSms === 'true',
      agreedToMarketing: metadata.agreedToMarketing === 'true',
    };

    // Insert into database
    if (pool) {
      try {
        const query = `
          INSERT INTO orders (
            order_number, service_type, customer_name, customer_email, customer_phone,
            delivery_address, delivery_preference, urgency,
            innout_location, innout_order, grocery_order,
            task_details, special_instructions,
            subtotal, tax, total,
            stripe_session_id, stripe_payment_intent, status,
            agreed_to_terms, agreed_to_sms, agreed_to_marketing
          ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18, $19, $20, $21, $22)
          RETURNING id
        `;

        const values = [
          orderData.orderNumber,
          orderData.service,
          orderData.customerName,
          orderData.customerEmail,
          orderData.customerPhone,
          JSON.stringify(orderData.address),
          orderData.deliveryPreference,
          orderData.urgency,
          orderData.innoutLocation,
          orderData.innoutOrder ? JSON.stringify(orderData.innoutOrder) : null,
          orderData.groceryOrder ? JSON.stringify(orderData.groceryOrder) : null,
          orderData.taskDetails,
          orderData.specialInstructions,
          orderData.subtotal,
          orderData.tax,
          orderData.total,
          orderData.stripeSessionId,
          orderData.stripePaymentIntent,
          orderData.status,
          orderData.agreedToTerms,
          orderData.agreedToSms,
          orderData.agreedToMarketing,
        ];

        const result = await pool.query(query, values);
        console.log('💾 Order saved to database:', result.rows[0].id);
      } catch (dbError) {
        console.error('❌ Database error:', dbError);
        // Continue even if database fails - we still want to send SMS
      }
    }

    // Send SMS confirmation to customer
    if (twilioClient && orderData.agreedToSms) {
      try {
        await sendCustomerConfirmation(orderData);
        console.log('📱 SMS sent to customer:', orderData.customerPhone);
      } catch (smsError) {
        console.error('❌ SMS error:', smsError);
      }
    }

    // Send notification to gophers (if you have a gopher phone number)
    if (twilioClient && process.env.GOPHER_PHONE_NUMBER) {
      try {
        await sendGopherNotification(orderData);
        console.log('📱 SMS sent to gopher');
      } catch (smsError) {
        console.error('❌ Gopher SMS error:', smsError);
      }
    }

  } catch (error) {
    console.error('❌ Error handling checkout complete:', error);
    throw error;
  }
}

module.exports = router;

