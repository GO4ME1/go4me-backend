const express = require('express');
const router = express.Router();
const { stripe } = require('../server');

/**
 * POST /api/create-checkout-session
 * Creates a Stripe Checkout session for the booking
 */
router.post('/create-checkout-session', async (req, res) => {
  try {
    const {
      service,
      customerName,
      customerEmail,
      customerPhone,
      address,
      deliveryPreference,
      urgency,
      innoutLocation,
      innoutOrder,
      groceryOrder,
      taskDetails,
      specialInstructions,
      pricing,
      agreedToTerms,
      agreedToSms,
      agreedToMarketing
    } = req.body;

    // Validation
    if (!service || !customerName || !customerPhone || !address || !pricing) {
      return res.status(400).json({ error: 'Missing required fields' });
    }

    if (!agreedToTerms || !agreedToSms) {
      return res.status(400).json({ error: 'Must agree to terms and SMS consent' });
    }

    // Generate order number
    const orderNumber = `GO4ME-${Date.now().toString().slice(-8)}`;

    // Create line items for Stripe
    const lineItems = [];

    // Service fee
    const serviceInfo = getServiceInfo(service);
    lineItems.push({
      price_data: {
        currency: 'usd',
        product_data: {
          name: serviceInfo.name,
          description: serviceInfo.description,
        },
        unit_amount: Math.round(pricing.subtotal * 100), // Convert to cents
      },
      quantity: 1,
    });

    // Prepare metadata for webhook
    const metadata = {
      orderNumber,
      service,
      customerName,
      customerEmail: customerEmail || '',
      customerPhone,
      addressStreet: address.street,
      addressCity: address.city,
      addressState: address.state,
      addressZip: address.zip,
      addressGateCode: address.gateCode || '',
      deliveryPreference,
      urgency,
      innoutLocation: innoutLocation || '',
      innoutOrder: innoutOrder ? JSON.stringify(innoutOrder) : '',
      groceryOrder: groceryOrder ? JSON.stringify(groceryOrder) : '',
      taskDetails: taskDetails || '',
      specialInstructions: specialInstructions || '',
      subtotal: pricing.subtotal.toString(),
      tax: pricing.tax.toString(),
      total: pricing.total.toString(),
      agreedToTerms: agreedToTerms.toString(),
      agreedToSms: agreedToSms.toString(),
      agreedToMarketing: agreedToMarketing.toString(),
    };

    // Create Stripe Checkout session
    const session = await stripe.checkout.sessions.create({
      payment_method_types: ['card'],
      line_items: lineItems,
      mode: 'payment',
      success_url: `${process.env.FRONTEND_URL}/success?session_id={CHECKOUT_SESSION_ID}`,
      cancel_url: `${process.env.FRONTEND_URL}/`,
      customer_email: customerEmail || undefined,
      metadata,
      phone_number_collection: {
        enabled: false, // We already collect phone
      },
    });

    res.json({ sessionId: session.id, orderNumber });
  } catch (error) {
    console.error('Error creating checkout session:', error);
    res.status(500).json({ error: 'Failed to create checkout session', message: error.message });
  }
});

/**
 * Helper function to get service information
 */
function getServiceInfo(serviceId) {
  const services = {
    innout: {
      name: '🍔 In-N-Out Delivery',
      description: 'We pick up and deliver your In-N-Out order',
    },
    grocery: {
      name: '🛒 Grocery Runs',
      description: 'We shop and deliver your Trader Joe\'s groceries',
    },
    feels: {
      name: '💭 Feels on Wheels',
      description: 'Emotional support and companionship service',
    },
    dmv: {
      name: '🚗 DMV Proxy',
      description: 'We handle DMV errands so you don\'t have to wait in line',
    },
    eyes: {
      name: '👁️ Eyes On',
      description: 'Property check-in service',
    },
    lost: {
      name: '🔍 Lost & Found',
      description: 'We help locate and retrieve lost items',
    },
    cleaning: {
      name: '👔 Dry Cleaning Pickup',
      description: 'Dry cleaning pickup and delivery',
    },
    custom: {
      name: '✨ Custom Errand',
      description: 'Custom errand service',
    },
  };

  return services[serviceId] || { name: 'Go4me.ai Service', description: 'Errand service' };
}

module.exports = router;

