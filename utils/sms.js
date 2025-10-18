const { twilioClient } = require('../server');

/**
 * Send order confirmation SMS to customer
 */
async function sendCustomerConfirmation(orderData) {
  if (!twilioClient) {
    console.log('⚠️  Twilio not configured, skipping SMS');
    return;
  }

  const message = formatCustomerMessage(orderData);

  return await twilioClient.messages.create({
    body: message,
    from: process.env.TWILIO_PHONE_NUMBER,
    to: orderData.customerPhone,
  });
}

/**
 * Send new order notification to gopher
 */
async function sendGopherNotification(orderData) {
  if (!twilioClient) {
    console.log('⚠️  Twilio not configured, skipping SMS');
    return;
  }

  const message = formatGopherMessage(orderData);

  return await twilioClient.messages.create({
    body: message,
    from: process.env.TWILIO_PHONE_NUMBER,
    to: process.env.GOPHER_PHONE_NUMBER,
  });
}

/**
 * Format customer confirmation message
 */
function formatCustomerMessage(orderData) {
  const serviceNames = {
    innout: 'In-N-Out Delivery',
    grocery: 'Grocery Runs',
    feels: 'Feels on Wheels',
    dmv: 'DMV Proxy',
    eyes: 'Eyes On',
    lost: 'Lost & Found',
    cleaning: 'Dry Cleaning',
    custom: 'Custom Errand',
  };

  const serviceName = serviceNames[orderData.service] || 'Service';

  let message = `🎉 Go4me.ai Order Confirmed!\n\n`;
  message += `Order #${orderData.orderNumber}\n`;
  message += `Service: ${serviceName}\n`;
  message += `Total: $${orderData.total.toFixed(2)}\n\n`;

  // Add service-specific details
  if (orderData.service === 'innout' && orderData.innoutLocation) {
    message += `📍 Location: ${orderData.innoutLocation}\n`;
  }

  if (orderData.urgency === 'urgent') {
    message += `⚡ Urgency: Within 2 hours\n`;
  } else if (orderData.urgency === 'asap') {
    message += `🚨 Urgency: ASAP (within 1 hour)\n`;
  } else {
    message += `📅 Delivery: Within 4 hours\n`;
  }

  message += `\n📍 Delivery: ${orderData.address.street}, ${orderData.address.city}\n`;
  
  if (orderData.deliveryPreference === 'meet') {
    message += `🤝 Meet at door\n`;
  } else {
    message += `📦 Leave at door\n`;
  }

  message += `\nYou'll receive updates when:\n`;
  message += `• A gopher is assigned\n`;
  message += `• They're on the way\n`;
  message += `• Your order is delivered\n\n`;
  message += `Questions? Reply HELP or visit go4me.ai/support`;

  return message;
}

/**
 * Format gopher notification message
 */
function formatGopherMessage(orderData) {
  const serviceNames = {
    innout: 'In-N-Out Delivery',
    grocery: 'Grocery Runs',
    feels: 'Feels on Wheels',
    dmv: 'DMV Proxy',
    eyes: 'Eyes On',
    lost: 'Lost & Found',
    cleaning: 'Dry Cleaning',
    custom: 'Custom Errand',
  };

  const serviceName = serviceNames[orderData.service] || 'Service';

  let message = `🚨 NEW ORDER - ${orderData.orderNumber}\n\n`;
  message += `Service: ${serviceName}\n`;
  message += `Customer: ${orderData.customerName}\n`;
  message += `Phone: ${orderData.customerPhone}\n`;
  message += `Total: $${orderData.total.toFixed(2)}\n\n`;

  // Urgency
  if (orderData.urgency === 'asap') {
    message += `🚨 ASAP - Within 1 hour!\n`;
  } else if (orderData.urgency === 'urgent') {
    message += `⚡ URGENT - Within 2 hours\n`;
  } else {
    message += `📅 Standard - Within 4 hours\n`;
  }

  // Address
  message += `\n📍 Delivery Address:\n`;
  message += `${orderData.address.street}\n`;
  message += `${orderData.address.city}, ${orderData.address.state} ${orderData.address.zip}\n`;
  
  if (orderData.address.gateCode) {
    message += `🔑 Gate Code: ${orderData.address.gateCode}\n`;
  }

  // Service-specific details
  if (orderData.service === 'innout') {
    message += `\n🍔 In-N-Out Location: ${orderData.innoutLocation}\n`;
    if (orderData.innoutOrder && orderData.innoutOrder.length > 0) {
      message += `Order Items: ${orderData.innoutOrder.length} items\n`;
    }
  }

  if (orderData.service === 'grocery') {
    if (orderData.groceryOrder && orderData.groceryOrder.length > 0) {
      message += `\n🛒 Grocery Items: ${orderData.groceryOrder.length} items\n`;
    }
  }

  if (orderData.taskDetails) {
    message += `\n📝 Details: ${orderData.taskDetails.substring(0, 100)}${orderData.taskDetails.length > 100 ? '...' : ''}\n`;
  }

  if (orderData.specialInstructions) {
    message += `\n⚠️ Special Instructions: ${orderData.specialInstructions}\n`;
  }

  message += `\n🔗 View full details in admin dashboard`;

  return message;
}

/**
 * Send status update SMS to customer
 */
async function sendStatusUpdate(customerPhone, orderNumber, status, gopherName = null) {
  if (!twilioClient) {
    console.log('⚠️  Twilio not configured, skipping SMS');
    return;
  }

  let message = '';

  switch (status) {
    case 'assigned':
      message = `👋 Your gopher ${gopherName} has been assigned to order #${orderNumber}! They'll be in touch soon.`;
      break;
    case 'en_route':
      message = `🚗 ${gopherName} is on the way with your order #${orderNumber}!`;
      break;
    case 'completed':
      message = `✅ Order #${orderNumber} delivered! Thanks for using Go4me.ai. Rate your experience: go4me.ai/rate/${orderNumber}`;
      break;
    default:
      message = `📦 Update on order #${orderNumber}: ${status}`;
  }

  return await twilioClient.messages.create({
    body: message,
    from: process.env.TWILIO_PHONE_NUMBER,
    to: customerPhone,
  });
}

module.exports = {
  sendCustomerConfirmation,
  sendGopherNotification,
  sendStatusUpdate,
};

