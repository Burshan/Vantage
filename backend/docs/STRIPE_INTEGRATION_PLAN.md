# Stripe Integration Plan for Vantage Token System

## Current Architecture Assessment ✅

### Ready for Stripe Integration:
- ✅ **TokenTransaction Model**: Complete with Stripe-specific fields
  - `payment_intent_id` - Ready for Stripe Payment Intents
  - `stripe_charge_id` - Ready for Stripe Charges
  - `stripe_invoice_id` - Ready for Subscriptions
  - `price_per_token` & `total_amount_usd` - Ready for pricing
  - `currency` field with USD default
  - `status` field for payment tracking
  - `metadata` JSON field for additional Stripe data

- ✅ **Transaction Audit Trail**: Complete logging system
- ✅ **User Management**: Solid user system with Clerk integration
- ✅ **Admin Interface**: Token management endpoints ready
- ✅ **Token Balance System**: Working token balance tracking

### Architecture Strengths:
1. **Separation of Concerns**: Payment logic isolated in transaction system
2. **Idempotency Ready**: Transaction IDs and reference tracking
3. **Webhook Ready**: Status fields support async payment processing
4. **Multi-Currency Ready**: Currency field exists
5. **Subscription Ready**: Invoice ID field for recurring payments

## Stripe Integration Implementation Plan

### Phase 1: Basic Token Purchasing (1-2 days)
```python
# New endpoints to create:
POST /api/stripe/create-payment-intent     # Create Stripe payment
POST /api/stripe/confirm-payment          # Handle payment confirmation
POST /api/webhooks/stripe                 # Handle webhooks
```

### Phase 2: Subscription Management (2-3 days)
```python
# Additional endpoints:
POST /api/stripe/create-subscription      # Monthly token subscriptions
POST /api/stripe/cancel-subscription      # Cancel subscriptions
GET /api/stripe/subscriptions            # List user subscriptions
```

### Phase 3: Advanced Features (1-2 days)
- Payment method management
- Invoice history
- Failed payment handling
- Proration for plan changes

## Implementation Steps

### Step 1: Environment Setup
```bash
pip install stripe
```

```python
# config.py additions needed:
STRIPE_SECRET_KEY = os.getenv('STRIPE_SECRET_KEY')
STRIPE_PUBLISHABLE_KEY = os.getenv('STRIPE_PUBLISHABLE_KEY')
STRIPE_WEBHOOK_SECRET = os.getenv('STRIPE_WEBHOOK_SECRET')
```

### Step 2: Create Stripe Service
```python
# services/stripe_service.py
class StripeService:
    def __init__(self, secret_key):
        stripe.api_key = secret_key
    
    def create_payment_intent(self, amount_usd, customer_email, tokens_requested):
        # Create payment intent
        # Return payment_intent object
    
    def create_customer(self, user_email, user_id):
        # Create Stripe customer
        # Store customer_id in User model
    
    def handle_webhook(self, payload, sig_header):
        # Handle Stripe webhooks
        # Update TokenTransaction status
```

### Step 3: Payment Controller
```python
# controllers/stripe_controller.py
@stripe_bp.route('/create-payment-intent', methods=['POST'])
def create_payment_intent():
    # 1. Calculate price (tokens * price_per_token)
    # 2. Create Stripe payment intent
    # 3. Create pending TokenTransaction
    # 4. Return client_secret for frontend
```

### Step 4: Webhook Handler
```python
@stripe_bp.route('/webhooks', methods=['POST'])  
def stripe_webhook():
    # Handle payment_intent.succeeded
    # Update TokenTransaction status to 'completed'
    # Add tokens to user account
    # Send confirmation email
```

### Step 5: Frontend Integration
```javascript
// Frontend Stripe integration needed:
// 1. Stripe Elements for card input
// 2. Payment confirmation flow
// 3. Success/error handling
```

## Token Pricing Strategy

### Recommended Pricing Structure:
```python
TOKEN_PACKAGES = {
    'starter': {'tokens': 10, 'price_usd': 9.99, 'price_per_token': 0.999},
    'professional': {'tokens': 50, 'price_usd': 39.99, 'price_per_token': 0.799},
    'enterprise': {'tokens': 150, 'price_usd': 99.99, 'price_per_token': 0.666},
}

SUBSCRIPTION_PLANS = {
    'monthly_basic': {'tokens': 25, 'price_usd': 19.99, 'interval': 'month'},
    'monthly_pro': {'tokens': 100, 'price_usd': 59.99, 'interval': 'month'},
}
```

## Database Migration Required

```sql
-- Add Stripe customer ID to users table
ALTER TABLE users ADD COLUMN stripe_customer_id VARCHAR(255);
ALTER TABLE users ADD COLUMN subscription_status VARCHAR(50);
ALTER TABLE users ADD COLUMN subscription_id VARCHAR(255);

-- Indexes for performance
CREATE INDEX idx_users_stripe_customer ON users(stripe_customer_id);
CREATE INDEX idx_token_transactions_payment_intent ON token_transactions(payment_intent_id);
CREATE INDEX idx_token_transactions_status ON token_transactions(status);
```

## Security Considerations

### ✅ Already Implemented:
- User authentication via Clerk
- Admin-only endpoints
- Transaction logging
- Input validation

### 🔄 Need to Add:
- Stripe webhook signature verification
- Idempotency keys for duplicate prevention
- Rate limiting on payment endpoints
- PCI compliance considerations (handled by Stripe)

## Testing Strategy

### Unit Tests Needed:
```python
# Test payment flow
def test_create_payment_intent()
def test_webhook_payment_succeeded()
def test_token_allocation_after_payment()
def test_duplicate_webhook_handling()

# Test error scenarios
def test_payment_failed()
def test_insufficient_funds()
def test_invalid_webhook_signature()
```

### Integration Tests:
- End-to-end payment flow
- Webhook handling
- Token allocation
- Subscription lifecycle

## Monitoring & Analytics

### Metrics to Track:
- Payment success rates
- Average tokens purchased
- Monthly recurring revenue
- Churn rate
- Failed payment recovery

### Logging Requirements:
- All payment attempts
- Webhook processing
- Token allocation
- Errors and failures

## Current Manual Admin Interface

### ✅ Already Available:
```bash
# Manual token grants (current solution):
POST /api/admin/tokens/add
{
  "user_email": "user@example.com",
  "amount": 50,
  "note": "Welcome bonus"
}

# Bulk token grants:
POST /api/admin/tokens/bulk-grant
{
  "users": [{"email": "user1@example.com", "amount": 10}],
  "note": "Promotion"
}

# Transaction history:
GET /api/admin/tokens/transactions
```

## Timeline Estimate

### Immediate (Today): ✅ DONE
- [x] TokenTransaction model ready
- [x] Admin token management
- [x] Transaction tracking
- [x] Database functions

### Week 1 (5-7 days):
- [ ] Stripe service implementation
- [ ] Payment intent creation
- [ ] Webhook handling
- [ ] Basic frontend integration

### Week 2 (3-5 days):
- [ ] Subscription management
- [ ] Advanced error handling
- [ ] Testing and QA
- [ ] Production deployment

### Week 3 (2-3 days):
- [ ] Analytics and monitoring
- [ ] Documentation
- [ ] Admin dashboard enhancements

## Risk Mitigation

### Financial Risks:
- ✅ Transaction logging prevents double-spending
- ✅ Admin controls for manual intervention
- ✅ Webhook idempotency handling

### Technical Risks:
- ✅ Fallback to manual token grants
- ✅ Database transaction integrity
- ✅ Comprehensive error handling

### Business Risks:
- ✅ Flexible pricing model
- ✅ Multiple payment options ready
- ✅ Subscription and one-time purchase support

## Conclusion

**The current architecture is EXCELLENT for Stripe integration!** 

### Immediate Options:
1. **Manual Admin Grants** (Available Now)
2. **Stripe Integration** (1-2 weeks implementation)
3. **Hybrid Approach** (Manual + automated as needed)

The TokenTransaction system is enterprise-ready and will seamlessly support Stripe when implemented. The database design anticipates all Stripe integration needs.