# Go4me.ai Backend API

Backend API for the Go4me.ai booking form with Stripe payment processing, Twilio SMS notifications, and PostgreSQL database.

## Features

- ✅ Stripe Checkout integration
- ✅ Stripe webhook handler for payment confirmation
- ✅ Twilio SMS notifications (customer + gopher)
- ✅ PostgreSQL database for order storage
- ✅ CORS enabled for frontend integration
- ✅ Environment-based configuration
- ✅ Error handling and logging

## Tech Stack

- **Runtime:** Node.js
- **Framework:** Express.js
- **Payment:** Stripe
- **SMS:** Twilio
- **Database:** PostgreSQL
- **Deployment:** Railway, Render, or Cloudflare Workers

## Prerequisites

- Node.js 18+ installed
- PostgreSQL database
- Stripe account (https://stripe.com)
- Twilio account (https://twilio.com)

## Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/GO4ME1/go4me-booking-form.git
   cd go4me-booking-form/backend
   ```

2. **Install dependencies:**
   ```bash
   npm install
   ```

3. **Set up environment variables:**
   ```bash
   cp .env.example .env
   ```

4. **Edit `.env` with your credentials:**
   - Stripe API keys from https://dashboard.stripe.com/apikeys
   - Twilio credentials from https://console.twilio.com
   - PostgreSQL connection string

5. **Set up the database:**
   ```bash
   psql -U postgres -d go4me -f schema.sql
   ```

6. **Start the development server:**
   ```bash
   npm run dev
   ```

The API will be running at `http://localhost:3000`

## API Endpoints

### Health Check
```
GET /health
```

Returns server status and configuration check.

**Response:**
```json
{
  "status": "ok",
  "timestamp": "2025-10-18T...",
  "stripe": true,
  "twilio": true,
  "database": true
}
```

### Create Checkout Session
```
POST /api/create-checkout-session
Content-Type: application/json
```

Creates a Stripe Checkout session for a booking.

**Request Body:**
```json
{
  "service": "innout",
  "customerName": "John Doe",
  "customerEmail": "john@example.com",
  "customerPhone": "+15551234567",
  "address": {
    "street": "123 Main St",
    "city": "San Diego",
    "state": "CA",
    "zip": "92101",
    "gateCode": "1234"
  },
  "deliveryPreference": "meet",
  "urgency": "standard",
  "innoutLocation": "Balboa Ave",
  "innoutOrder": [...],
  "groceryOrder": [...],
  "taskDetails": "...",
  "specialInstructions": "...",
  "pricing": {
    "subtotal": 10.00,
    "tax": 0.78,
    "total": 10.78
  },
  "agreedToTerms": true,
  "agreedToSms": true,
  "agreedToMarketing": false
}
```

**Response:**
```json
{
  "sessionId": "cs_test_...",
  "orderNumber": "GO4ME-12345678"
}
```

### Stripe Webhook
```
POST /api/webhook/stripe
Content-Type: application/json
Stripe-Signature: ...
```

Handles Stripe webhook events (checkout.session.completed).

**Events Handled:**
- `checkout.session.completed` - Save order, send SMS
- `payment_intent.succeeded` - Log success
- `payment_intent.payment_failed` - Log failure

## Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `NODE_ENV` | Environment | `development` or `production` |
| `PORT` | Server port | `3000` |
| `FRONTEND_URL` | Frontend URL for redirects | `https://book.go4me.ai` |
| `STRIPE_SECRET_KEY` | Stripe secret key | `sk_test_...` |
| `STRIPE_WEBHOOK_SECRET` | Stripe webhook secret | `whsec_...` |
| `TWILIO_ACCOUNT_SID` | Twilio account SID | `AC...` |
| `TWILIO_AUTH_TOKEN` | Twilio auth token | `...` |
| `TWILIO_PHONE_NUMBER` | Twilio phone number | `+15551234567` |
| `GOPHER_PHONE_NUMBER` | Gopher notification number | `+15551234567` |
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://...` |

## Database Schema

The database includes three main tables:

1. **orders** - Main orders table with customer info, service details, pricing
2. **gophers** - Service providers (for future use)
3. **order_updates** - Status change history

See `schema.sql` for the complete schema.

## SMS Notifications

### Customer Confirmation
Sent immediately after payment:
- Order number
- Service type
- Total amount
- Delivery address
- Estimated time
- Next steps

### Gopher Notification
Sent to gopher phone number:
- New order alert
- Customer details
- Service type
- Urgency level
- Delivery address
- Special instructions

### Status Updates
Can be sent for:
- Gopher assigned
- En route
- Completed

## Deployment

### Railway (Recommended)

1. **Install Railway CLI:**
   ```bash
   npm install -g @railway/cli
   ```

2. **Login and initialize:**
   ```bash
   railway login
   railway init
   ```

3. **Add PostgreSQL:**
   ```bash
   railway add postgresql
   ```

4. **Set environment variables:**
   ```bash
   railway variables set STRIPE_SECRET_KEY=sk_test_...
   railway variables set TWILIO_ACCOUNT_SID=AC...
   # ... etc
   ```

5. **Deploy:**
   ```bash
   railway up
   ```

6. **Run database migrations:**
   ```bash
   railway run psql -f schema.sql
   ```

Your API will be live at: `https://your-app.railway.app`

### Render

1. Go to https://render.com
2. Click "New" → "Web Service"
3. Connect GitHub repository
4. Configure:
   - Build Command: `npm install`
   - Start Command: `npm start`
   - Add PostgreSQL database
   - Add environment variables
5. Deploy

### Cloudflare Workers

1. **Install Wrangler:**
   ```bash
   npm install -g wrangler
   ```

2. **Configure wrangler.toml:**
   ```toml
   name = "go4me-backend"
   main = "server.js"
   compatibility_date = "2025-10-18"
   ```

3. **Deploy:**
   ```bash
   wrangler deploy
   ```

## Stripe Webhook Setup

1. Go to https://dashboard.stripe.com/webhooks
2. Click "Add endpoint"
3. Enter your webhook URL: `https://your-api.com/api/webhook/stripe`
4. Select events:
   - `checkout.session.completed`
   - `payment_intent.succeeded`
   - `payment_intent.payment_failed`
5. Copy the webhook secret to `.env` as `STRIPE_WEBHOOK_SECRET`

## Testing

### Test Checkout Locally

```bash
# Start the server
npm run dev

# In another terminal, test the health endpoint
curl http://localhost:3000/health

# Test checkout (replace with your test data)
curl -X POST http://localhost:3000/api/create-checkout-session \
  -H "Content-Type: application/json" \
  -d '{"service":"innout","customerName":"Test","customerPhone":"+15551234567","address":{"street":"123 Main","city":"San Diego","state":"CA","zip":"92101"},"deliveryPreference":"meet","urgency":"standard","pricing":{"subtotal":10,"tax":0.78,"total":10.78},"agreedToTerms":true,"agreedToSms":true}'
```

### Test Webhook Locally

Use Stripe CLI to forward webhooks:

```bash
stripe listen --forward-to localhost:3000/api/webhook/stripe
```

Then trigger a test event:

```bash
stripe trigger checkout.session.completed
```

## Troubleshooting

### Database Connection Issues

```bash
# Check PostgreSQL is running
psql -U postgres -c "SELECT version();"

# Test connection string
psql "postgresql://user:pass@host:port/database"
```

### Stripe Webhook Errors

- Verify `STRIPE_WEBHOOK_SECRET` is set correctly
- Check webhook signature in Stripe dashboard
- Ensure endpoint is publicly accessible

### SMS Not Sending

- Verify Twilio credentials are correct
- Check phone number format (E.164: +1XXXXXXXXXX)
- Ensure customer agreed to SMS consent

## Security

- ✅ Environment variables for secrets
- ✅ Stripe webhook signature verification
- ✅ CORS configured for frontend domain
- ✅ SQL injection prevention (parameterized queries)
- ✅ HTTPS required in production

## License

MIT

## Support

- **GitHub Issues:** https://github.com/GO4ME1/go4me-booking-form/issues
- **Email:** support@go4me.ai
- **Website:** https://go4me.ai

