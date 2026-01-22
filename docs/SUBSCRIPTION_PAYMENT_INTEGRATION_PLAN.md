# Subscription & Payment Integration Plan for KRAFTD

**Status:** Pre-Implementation Plan  
**Priority:** High (Revenue Model Enablement)  
**Estimated Effort:** 2-3 weeks  
**Dependencies:** Stripe account, Cosmos DB schemas  

---

## 1. Architecture Overview

```
User Registration
      ↓
Select Plan (Free/Pro/Enterprise)
      ↓
Payment Processing (Stripe) ← Payment Gateway
      ↓
Subscription Created (Cosmos DB)
      ↓
User Activated with Tier Limits
      ↓
Usage Tracking
      ↓
Invoice/Receipt → Email
```

### Technology Stack Recommendation

| Component | Technology | Why |
|-----------|-----------|-----|
| **Payment Gateway** | Stripe | Industry standard, webhooks, multi-currency, renewals |
| **Database** | Cosmos DB | Already in use, fast lookups for usage limits |
| **Billing** | Stripe Billing | Recurring subscriptions, invoices, automatic renewal |
| **Email** | Existing EmailService | Send receipts and invoices |
| **Webhooks** | Stripe Events | Handle payment failures, subscription changes |

---

## 2. Data Models Required

### 2.1 Subscription Plan Model
```python
# backend/models/subscription.py

class PlanTier(str, Enum):
    FREE = "free"           # Development/SME evaluation
    PRO = "pro"             # Growing SMEs ($99/month)
    ENTERPRISE = "enterprise"  # Large enterprises (custom)

class SubscriptionPlan(BaseModel):
    """Pricing tiers available on KRAFTD"""
    id: str  # "free", "pro", "enterprise"
    name: str  # "Free", "Professional", "Enterprise"
    tier: PlanTier
    monthly_price: float  # USD
    annual_price: Optional[float]  # USD (if available)
    stripe_product_id: str  # Stripe product ID
    stripe_price_id_monthly: str  # Stripe recurring price
    stripe_price_id_annual: Optional[str]  # For annual billing
    features: List[str]
    limits: Dict[str, int]  # {"api_calls": 10000, "documents": 1000}
    description: str
    is_active: bool = True
    created_at: datetime
    updated_at: datetime

# Example Limits:
FREE_LIMITS = {
    "documents_per_month": 50,
    "api_calls_per_day": 1000,
    "team_members": 1,
    "storage_gb": 5,
    "export_formats": ["pdf"],
    "ai_features": False,
    "priority_support": False
}

PRO_LIMITS = {
    "documents_per_month": 1000,
    "api_calls_per_day": 50000,
    "team_members": 10,
    "storage_gb": 100,
    "export_formats": ["pdf", "excel", "json", "csv"],
    "ai_features": True,
    "priority_support": True
}

ENTERPRISE_LIMITS = {
    "documents_per_month": None,  # Unlimited
    "api_calls_per_day": None,
    "team_members": None,
    "storage_gb": None,
    "export_formats": ["pdf", "excel", "json", "csv", "xml"],
    "ai_features": True,
    "priority_support": True,
    "sso": True,
    "custom_integrations": True
}
```

### 2.2 User Subscription Model (Extends existing User model)
```python
# Update backend/models/user.py

class SubscriptionStatus(str, Enum):
    ACTIVE = "active"
    CANCELED = "canceled"
    PAST_DUE = "past_due"
    INCOMPLETE = "incomplete"
    INCOMPLETE_EXPIRED = "incomplete_expired"
    PAUSED = "paused"
    UNPAID = "unpaid"

class User(BaseModel):
    # ... existing fields ...
    
    # Subscription fields (ADD TO EXISTING USER MODEL)
    subscription_tier: PlanTier = PlanTier.FREE
    subscription_status: SubscriptionStatus = SubscriptionStatus.ACTIVE
    stripe_customer_id: Optional[str] = None
    stripe_subscription_id: Optional[str] = None
    current_plan_id: str = "free"  # Links to SubscriptionPlan.id
    subscription_start_date: Optional[datetime] = None
    subscription_end_date: Optional[datetime] = None
    renewal_date: Optional[datetime] = None
    auto_renew: bool = True
    billing_email: Optional[str] = None  # May differ from login email
    billing_interval: str = "monthly"  # "monthly" or "annual"
    last_payment_status: Optional[str] = None
    payment_method_id: Optional[str] = None
```

### 2.3 Payment/Invoice Model
```python
class Payment(BaseModel):
    """Record of successful payments"""
    id: str  # UUID
    user_id: str
    stripe_payment_intent_id: str
    stripe_invoice_id: Optional[str]
    amount_cents: int  # Store as cents to avoid float precision issues
    currency: str = "USD"
    status: str  # "succeeded", "processing", "failed"
    payment_method: str  # "card", "ach", etc.
    created_at: datetime
    processed_at: Optional[datetime]
    receipt_url: Optional[str]  # Stripe receipt URL
    description: str  # "Pro Plan - Monthly subscription"

class Invoice(BaseModel):
    """Billing invoice"""
    id: str  # UUID
    user_id: str
    stripe_invoice_id: str
    amount_cents: int
    status: str  # "draft", "open", "paid", "void", "uncollectible"
    due_date: Optional[datetime]
    paid_date: Optional[datetime]
    invoice_url: str  # Stripe hosted invoice URL
    pdf_url: str  # Downloadable PDF
    created_at: datetime
    sent_at: Optional[datetime]
```

### 2.4 Usage Tracking Model
```python
class UsageRecord(BaseModel):
    """Daily usage tracking for quota enforcement"""
    id: str
    user_id: str
    date: str  # "2026-01-22"
    documents_processed: int = 0
    api_calls: int = 0
    storage_used_mb: float = 0
    export_count: int = 0
    created_at: datetime
    updated_at: datetime
```

---

## 3. Database Schema (Cosmos DB Containers)

### Create New Containers:

```bash
# In Cosmos DB, create 4 new containers:

1. "subscription_plans" (Partition Key: /tier)
   - Stores fixed pricing tiers
   - Low write frequency, read on every registration
   - TTL: Never expires

2. "user_subscriptions" (Partition Key: /user_id)
   - Extends existing user collection
   - High write frequency (on every payment/upgrade)
   - TTL: None (permanent)

3. "payments" (Partition Key: /user_id)
   - Immutable payment records
   - High write frequency
   - TTL: 2555 days (7 years for accounting)

4. "usage_records" (Partition Key: /user_id)
   - Daily usage snapshots
   - Very high write frequency (maybe 1000s/day)
   - TTL: 90 days (auto-expire old records)
```

**OR** (Simpler Approach):
- Add subscription fields directly to existing `users` container
- Add `payments` container for transaction history
- Add `usage_records` container for quota tracking

---

## 4. Stripe Integration Flow

### 4.1 Registration → Subscription Selection

```python
# Updated: backend/routes/auth.py

@router.post("/register/with-plan")
async def register_with_subscription(
    registration: UserRegister,
    plan_id: str,  # "free", "pro"
    billing_interval: str = "monthly",  # "monthly" or "annual"
    request: Request
):
    """
    1. Create user (existing logic)
    2. Create Stripe customer
    3. For paid plans: Create checkout session
    4. Store subscription intent in DB
    """
    # Create user
    user = AuthService.create_user(...)
    users_db[user.email] = user
    
    # Get selected plan
    plan = SubscriptionService.get_plan(plan_id)
    
    # Create Stripe customer
    stripe_customer = StripeService.create_customer(
        email=user.email,
        name=user.name,
        metadata={"user_id": user.id}
    )
    
    # Update user with Stripe customer ID
    user.stripe_customer_id = stripe_customer.id
    user.current_plan_id = plan_id
    
    if plan_id == "free":
        # Free tier: Activate immediately
        user.subscription_tier = PlanTier.FREE
        user.subscription_status = SubscriptionStatus.ACTIVE
        user.subscription_start_date = datetime.utcnow()
        users_db[user.email] = user
        
        # Generate tokens
        access_token = TokenService.create_access_token(user.email)
        return TokenResponse(access_token=access_token, ...)
    
    else:
        # Paid tier: Create checkout session
        checkout_session = StripeService.create_checkout_session(
            customer_id=stripe_customer.id,
            price_id=plan.stripe_price_id_monthly if billing_interval == "monthly" else plan.stripe_price_id_annual,
            success_url="https://kraftd.io/dashboard?payment=success",
            cancel_url="https://kraftd.io/register?plan=pro",
            metadata={"user_id": user.id, "plan_id": plan_id}
        )
        
        # Store incomplete subscription in DB
        user.subscription_status = SubscriptionStatus.INCOMPLETE
        users_db[user.email] = user
        
        # Return checkout URL instead of token
        return {
            "checkout_url": checkout_session.url,
            "session_id": checkout_session.id,
            "message": "Please complete payment to activate your subscription"
        }
```

### 4.2 Payment Webhook Handler

```python
# New: backend/routes/webhooks.py

from stripe.error import SignatureVerificationError

@router.post("/webhooks/stripe")
async def stripe_webhook(request: Request):
    """
    Handle Stripe webhook events:
    - charge.succeeded
    - invoice.payment_succeeded
    - customer.subscription.updated
    - customer.subscription.deleted
    """
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    
    try:
        event = StripeService.construct_event(payload, sig_header)
    except SignatureVerificationError as e:
        raise HTTPException(status_code=400, detail="Invalid signature")
    
    # Handle event types
    if event['type'] == 'checkout.session.completed':
        await handle_checkout_completed(event['data']['object'])
    
    elif event['type'] == 'invoice.payment_succeeded':
        await handle_payment_succeeded(event['data']['object'])
    
    elif event['type'] == 'invoice.payment_failed':
        await handle_payment_failed(event['data']['object'])
    
    elif event['type'] == 'customer.subscription.updated':
        await handle_subscription_updated(event['data']['object'])
    
    elif event['type'] == 'customer.subscription.deleted':
        await handle_subscription_deleted(event['data']['object'])
    
    return {"received": True}

async def handle_checkout_completed(session):
    """User completed checkout → Activate subscription"""
    user_id = session.metadata.get('user_id')
    plan_id = session.metadata.get('plan_id')
    
    user = get_user_by_id(user_id)
    plan = SubscriptionService.get_plan(plan_id)
    
    # Create subscription in Stripe
    stripe_subscription = StripeService.create_subscription(
        customer_id=session.customer,
        price_id=session.line_items[0].price_id,
        metadata={"user_id": user_id, "plan_id": plan_id}
    )
    
    # Update user in DB
    user.subscription_status = SubscriptionStatus.ACTIVE
    user.subscription_tier = plan.tier
    user.stripe_subscription_id = stripe_subscription.id
    user.subscription_start_date = datetime.utcnow()
    user.renewal_date = datetime.utcnow() + timedelta(days=30)
    user.auto_renew = True
    users_db[user.email] = user
    
    # Send confirmation email
    await EmailService.send_subscription_confirmed(user.email, plan.name)
    
    logger.info(f"Subscription activated for {user.email}: {plan_id}")

async def handle_payment_failed(invoice):
    """Payment failed → Update status and notify user"""
    stripe_customer_id = invoice.customer
    user = get_user_by_stripe_customer(stripe_customer_id)
    
    user.subscription_status = SubscriptionStatus.PAST_DUE
    user.last_payment_status = "failed"
    users_db[user.email] = user
    
    # Send payment failed email with retry link
    await EmailService.send_payment_failed(user.email)
    
    logger.warning(f"Payment failed for {user.email}")
```

---

## 5. Usage Quota Enforcement

### 5.1 Middleware for Rate Limiting

```python
# New: backend/middleware/quota.py

from fastapi import Request
from datetime import datetime

async def enforce_quota(request: Request, call_next):
    """
    Check user subscription tier against:
    - API calls per day
    - Documents processed per month
    - Export formats allowed
    """
    user_email = get_current_user(request)
    user = users_db.get(user_email)
    
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    
    plan = SubscriptionService.get_plan(user.current_plan_id)
    limits = plan.limits
    
    # Get today's usage
    today = datetime.utcnow().strftime("%Y-%m-%d")
    usage = get_usage_record(user.id, today)
    
    # Check rate limits
    if limits.get("api_calls_per_day") and usage.api_calls >= limits["api_calls_per_day"]:
        raise HTTPException(
            status_code=429,
            detail=f"Daily API limit reached. Upgrade to {next_tier(user.subscription_tier)}"
        )
    
    # Continue processing
    response = await call_next(request)
    
    # Track this API call
    usage.api_calls += 1
    save_usage_record(usage)
    
    return response
```

### 5.2 Document Upload Quota Check

```python
# In document upload endpoint

@router.post("/documents/upload")
async def upload_document(
    file: UploadFile,
    current_user: User = Depends(get_current_user)
):
    """Check monthly document limit before processing"""
    plan = SubscriptionService.get_plan(current_user.current_plan_id)
    
    # Get this month's usage
    current_month = datetime.utcnow().strftime("%Y-%m")
    month_usage = get_monthly_usage(current_user.id, current_month)
    
    if month_usage.documents_processed >= plan.limits["documents_per_month"]:
        raise HTTPException(
            status_code=403,
            detail=f"Monthly document limit ({plan.limits['documents_per_month']}) reached. Please upgrade.",
            headers={"X-Upgrade-Url": "https://kraftd.io/pricing"}
        )
    
    # Check AI features
    if not plan.limits["ai_features"]:
        raise HTTPException(
            status_code=403,
            detail="AI extraction requires Pro plan or higher",
            headers={"X-Upgrade-Url": "https://kraftd.io/pricing"}
        )
    
    # Process document...
    result = await process_document(file)
    month_usage.documents_processed += 1
    save_usage_record(month_usage)
    
    return result
```

---

## 6. Billing Portal & Customer Management

### 6.1 Customer Portal Endpoints

```python
# New: backend/routes/billing.py

@router.get("/billing/invoices")
async def get_invoices(current_user: User = Depends(get_current_user)):
    """List user's invoices"""
    invoices = db.query_invoices(user_id=current_user.id)
    return [
        {
            "id": inv.id,
            "amount": inv.amount_cents / 100,
            "date": inv.created_at,
            "status": inv.status,
            "pdf_url": inv.pdf_url
        }
        for inv in invoices
    ]

@router.get("/billing/subscription")
async def get_subscription(current_user: User = Depends(get_current_user)):
    """Get current subscription status"""
    plan = SubscriptionService.get_plan(current_user.current_plan_id)
    return {
        "plan": {
            "id": plan.id,
            "name": plan.name,
            "price": plan.monthly_price,
            "features": plan.features,
            "limits": plan.limits
        },
        "status": current_user.subscription_status,
        "renewal_date": current_user.renewal_date,
        "auto_renew": current_user.auto_renew,
        "billing_interval": current_user.billing_interval
    }

@router.post("/billing/upgrade")
async def upgrade_plan(
    new_plan_id: str,
    current_user: User = Depends(get_current_user)
):
    """Upgrade to higher tier"""
    new_plan = SubscriptionService.get_plan(new_plan_id)
    current_plan = SubscriptionService.get_plan(current_user.current_plan_id)
    
    if PLAN_HIERARCHY[new_plan_id] <= PLAN_HIERARCHY[current_user.current_plan_id]:
        raise HTTPException(status_code=400, detail="Can only upgrade to higher tiers")
    
    # Create new checkout session for upgrade
    # Stripe handles pro-rata credit automatically
    checkout_session = StripeService.create_checkout_session(
        customer_id=current_user.stripe_customer_id,
        price_id=new_plan.stripe_price_id_monthly,
        success_url=f"https://kraftd.io/dashboard?upgraded={new_plan_id}",
        cancel_url="https://kraftd.io/pricing",
        subscription_update=current_user.stripe_subscription_id
    )
    
    return {"checkout_url": checkout_session.url}

@router.post("/billing/cancel-subscription")
async def cancel_subscription(current_user: User = Depends(get_current_user)):
    """Cancel subscription (downgrade to free)"""
    if current_user.subscription_tier == PlanTier.FREE:
        raise HTTPException(status_code=400, detail="Already on free plan")
    
    # Cancel in Stripe
    StripeService.cancel_subscription(current_user.stripe_subscription_id)
    
    # Update user
    current_user.subscription_tier = PlanTier.FREE
    current_user.current_plan_id = "free"
    current_user.subscription_status = SubscriptionStatus.CANCELED
    current_user.subscription_end_date = datetime.utcnow()
    users_db[current_user.email] = current_user
    
    # Send confirmation
    await EmailService.send_subscription_canceled(current_user.email)
    
    return {"message": "Subscription canceled. You'll remain on the Free plan."}

@router.get("/billing/customer-portal")
async def get_customer_portal_url(current_user: User = Depends(get_current_user)):
    """Get Stripe-hosted billing portal link"""
    if not current_user.stripe_customer_id:
        raise HTTPException(status_code=400, detail="No billing account")
    
    session = StripeService.create_billing_portal_session(
        customer_id=current_user.stripe_customer_id,
        return_url="https://kraftd.io/dashboard"
    )
    
    return {"url": session.url}
```

---

## 7. Service Layer (StripeService & SubscriptionService)

### 7.1 StripeService

```python
# New: backend/services/stripe_service.py

import stripe
from typing import Dict, Optional

class StripeService:
    """Wrapper around Stripe API"""
    
    def __init__(self):
        stripe.api_key = get_secrets_manager().get_stripe_secret_key()
    
    @staticmethod
    def create_customer(email: str, name: str, metadata: Dict) -> stripe.Customer:
        """Create Stripe customer"""
        return stripe.Customer.create(
            email=email,
            name=name,
            metadata=metadata
        )
    
    @staticmethod
    def create_checkout_session(
        customer_id: str,
        price_id: str,
        success_url: str,
        cancel_url: str,
        metadata: Dict = None,
        subscription_update: Optional[str] = None
    ) -> stripe.checkout.Session:
        """Create checkout session for payment"""
        params = {
            "customer": customer_id,
            "line_items": [{"price": price_id, "quantity": 1}],
            "mode": "subscription",
            "success_url": success_url,
            "cancel_url": cancel_url,
        }
        
        if metadata:
            params["metadata"] = metadata
        
        if subscription_update:
            params["subscription_data"] = {"billing_cycle_anchor": "automatic"}
        
        return stripe.checkout.Session.create(**params)
    
    @staticmethod
    def create_subscription(
        customer_id: str,
        price_id: str,
        metadata: Dict = None
    ) -> stripe.Subscription:
        """Create subscription directly"""
        return stripe.Subscription.create(
            customer=customer_id,
            items=[{"price": price_id}],
            metadata=metadata
        )
    
    @staticmethod
    def cancel_subscription(subscription_id: str) -> stripe.Subscription:
        """Cancel subscription at end of billing period"""
        return stripe.Subscription.modify(
            subscription_id,
            cancel_at_period_end=True
        )
    
    @staticmethod
    def construct_event(payload: bytes, sig_header: str) -> Dict:
        """Verify and construct webhook event"""
        endpoint_secret = get_secrets_manager().get_stripe_webhook_secret()
        return stripe.Webhook.construct_event(
            payload,
            sig_header,
            endpoint_secret
        )
    
    @staticmethod
    def create_billing_portal_session(
        customer_id: str,
        return_url: str
    ) -> stripe.billing_portal.Session:
        """Create link to Stripe-hosted billing portal"""
        return stripe.billing_portal.Session.create(
            customer=customer_id,
            return_url=return_url
        )
```

### 7.2 SubscriptionService

```python
# New: backend/services/subscription_service.py

from models.subscription import SubscriptionPlan, PlanTier

class SubscriptionService:
    """Business logic for subscription management"""
    
    PLANS = {
        "free": SubscriptionPlan(
            id="free",
            name="Free",
            tier=PlanTier.FREE,
            monthly_price=0,
            stripe_product_id="prod_free",
            stripe_price_id_monthly="price_free",
            features=[
                "Up to 50 documents/month",
                "Basic document extraction",
                "PDF export only",
                "Email support"
            ],
            limits={
                "documents_per_month": 50,
                "api_calls_per_day": 1000,
                "team_members": 1,
                "storage_gb": 5,
                "export_formats": ["pdf"],
                "ai_features": False,
                "priority_support": False
            }
        ),
        "pro": SubscriptionPlan(
            id="pro",
            name="Professional",
            tier=PlanTier.PRO,
            monthly_price=99,
            annual_price=990,
            stripe_product_id="prod_pro",
            stripe_price_id_monthly="price_pro_monthly",
            stripe_price_id_annual="price_pro_annual",
            features=[
                "Up to 1,000 documents/month",
                "Advanced AI extraction",
                "Multiple export formats (PDF, Excel, JSON, CSV)",
                "10 team members",
                "100GB storage",
                "Priority support",
                "API access"
            ],
            limits={
                "documents_per_month": 1000,
                "api_calls_per_day": 50000,
                "team_members": 10,
                "storage_gb": 100,
                "export_formats": ["pdf", "excel", "json", "csv"],
                "ai_features": True,
                "priority_support": True
            }
        ),
        "enterprise": SubscriptionPlan(
            id="enterprise",
            name="Enterprise",
            tier=PlanTier.ENTERPRISE,
            monthly_price=None,
            stripe_product_id="prod_enterprise",
            stripe_price_id_monthly="price_enterprise_custom",
            features=[
                "Unlimited documents",
                "Advanced AI & custom models",
                "All export formats + custom",
                "Unlimited team members",
                "Custom integrations",
                "SSO & SAML",
                "Dedicated support & SLA",
                "On-premises deployment option"
            ],
            limits={
                "documents_per_month": None,
                "api_calls_per_day": None,
                "team_members": None,
                "storage_gb": None,
                "export_formats": None,  # All
                "ai_features": True,
                "priority_support": True,
                "sso": True,
                "custom_integrations": True
            }
        )
    }
    
    @staticmethod
    def get_plan(plan_id: str) -> SubscriptionPlan:
        """Get pricing plan by ID"""
        if plan_id not in SubscriptionService.PLANS:
            raise ValueError(f"Plan {plan_id} not found")
        return SubscriptionService.PLANS[plan_id]
    
    @staticmethod
    def get_all_plans() -> List[SubscriptionPlan]:
        """Get all active plans"""
        return list(SubscriptionService.PLANS.values())
    
    @staticmethod
    def check_quota(user: User, limit_type: str) -> bool:
        """Check if user has exceeded limit"""
        plan = SubscriptionService.get_plan(user.current_plan_id)
        limit = plan.limits.get(limit_type)
        
        if limit is None:  # Unlimited
            return True
        
        # Get current usage
        usage = get_usage(user.id, limit_type)
        return usage < limit
```

---

## 8. Frontend Integration (React)

### 8.1 Pricing Page Component

```tsx
// frontend/src/pages/Pricing.tsx

export const PricingPage = () => {
  const plans = useFetchPlans(); // Calls GET /api/plans
  const [selectedPlan, setSelectedPlan] = useState<string>("pro");
  const [billingInterval, setBillingInterval] = useState<"monthly" | "annual">("monthly");

  const handleSelectPlan = async (planId: string) => {
    if (planId === "free") {
      // Free signup
      navigate("/register?plan=free");
    } else {
      // Redirect to register with plan
      navigate(`/register?plan=${planId}&interval=${billingInterval}`);
    }
  };

  return (
    <div className="pricing-container">
      <h1>Simple, Transparent Pricing</h1>
      
      {/* Billing Interval Toggle */}
      <div className="billing-toggle">
        <button 
          className={billingInterval === "monthly" ? "active" : ""}
          onClick={() => setBillingInterval("monthly")}
        >
          Monthly
        </button>
        <button 
          className={billingInterval === "annual" ? "active" : ""}
          onClick={() => setBillingInterval("annual")}
        >
          Annual (20% off)
        </button>
      </div>

      {/* Plan Cards */}
      <div className="plans-grid">
        {plans.map(plan => (
          <PlanCard key={plan.id} plan={plan} onSelect={() => handleSelectPlan(plan.id)} />
        ))}
      </div>
    </div>
  );
};
```

### 8.2 Subscription Management Component

```tsx
// frontend/src/pages/SubscriptionManager.tsx

export const SubscriptionManager = () => {
  const { data: subscription } = useQuery(["subscription"], () => 
    api.get("/billing/subscription")
  );
  
  const { data: invoices } = useQuery(["invoices"], () =>
    api.get("/billing/invoices")
  );

  const handleUpgrade = async (newPlanId: string) => {
    const response = await api.post("/billing/upgrade", { new_plan_id: newPlanId });
    window.location.href = response.checkout_url;
  };

  const handleCancel = async () => {
    if (window.confirm("Cancel subscription and downgrade to Free?")) {
      await api.post("/billing/cancel-subscription");
      window.location.reload();
    }
  };

  return (
    <div className="subscription-container">
      <h2>Subscription & Billing</h2>
      
      {/* Current Plan */}
      <div className="current-plan">
        <h3>Current Plan: {subscription.plan.name}</h3>
        <p>Renews on: {new Date(subscription.renewal_date).toLocaleDateString()}</p>
        {subscription.plan.id !== "enterprise" && (
          <>
            <button onClick={() => handleUpgrade("pro")}>Upgrade to Pro</button>
            <button onClick={handleCancel}>Cancel Subscription</button>
          </>
        )}
      </div>

      {/* Invoices */}
      <div className="invoices">
        <h3>Billing History</h3>
        <table>
          <thead>
            <tr>
              <th>Date</th>
              <th>Amount</th>
              <th>Status</th>
              <th>Invoice</th>
            </tr>
          </thead>
          <tbody>
            {invoices.map(inv => (
              <tr key={inv.id}>
                <td>{new Date(inv.date).toLocaleDateString()}</td>
                <td>${(inv.amount / 100).toFixed(2)}</td>
                <td>{inv.status}</td>
                <td><a href={inv.pdf_url} target="_blank">Download</a></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};
```

---

## 9. Environment Configuration

### 9.1 .env Variables

```bash
# Stripe
STRIPE_SECRET_KEY=sk_live_xxxxxxxxxxxxx
STRIPE_PUBLIC_KEY=pk_live_xxxxxxxxxxxxx
STRIPE_WEBHOOK_SECRET=whsec_xxxxxxxxxxxxx

# Pricing (can be overridden in code)
FREE_PLAN_DOCS_LIMIT=50
PRO_PLAN_DOCS_LIMIT=1000
FREE_PLAN_API_LIMIT=1000
PRO_PLAN_API_LIMIT=50000

# Payment URLs
CHECKOUT_SUCCESS_URL=https://kraftd.io/dashboard?payment=success
CHECKOUT_CANCEL_URL=https://kraftd.io/pricing
BILLING_PORTAL_RETURN_URL=https://kraftd.io/dashboard
```

### 9.2 Key Vault Secrets (Production)

```
stripe-secret-key
stripe-public-key
stripe-webhook-secret
```

---

## 10. Implementation Roadmap

### Phase 1: Foundation (Week 1)
- [ ] Create Stripe account
- [ ] Add subscription models to `backend/models/subscription.py`
- [ ] Create StripeService and SubscriptionService
- [ ] Add Cosmos DB containers for payments/usage
- [ ] Extend User model with subscription fields

### Phase 2: Backend Integration (Week 2)
- [ ] Add webhook endpoint at `/webhooks/stripe`
- [ ] Implement checkout session flow
- [ ] Add billing routes (`/billing/*`)
- [ ] Implement usage tracking middleware
- [ ] Add quota enforcement to document upload

### Phase 3: Frontend Integration (Week 2-3)
- [ ] Create Pricing page component
- [ ] Create Subscription management page
- [ ] Update registration flow to include plan selection
- [ ] Add plan limits display in UI
- [ ] Add quota warnings in dashboard

### Phase 4: Testing & Polish (Week 3)
- [ ] Test all payment flows (free → pro → enterprise)
- [ ] Test cancellation and downgrades
- [ ] Test invoice generation
- [ ] Load test payment processing
- [ ] Security audit of payment code

### Phase 5: Launch
- [ ] Enable Stripe live mode
- [ ] Update privacy policy & ToS with payment terms
- [ ] Set up accounting integration
- [ ] Monitor webhook failures
- [ ] Customer support guide for billing issues

---

## 11. Security Checklist

- [ ] Never log Stripe tokens or payment data
- [ ] Use HTTPS for all payment endpoints
- [ ] Validate webhook signatures (already in code above)
- [ ] Store Stripe keys in Key Vault, not .env
- [ ] Implement PCI compliance if storing payment methods
- [ ] Add rate limiting to payment endpoints
- [ ] Encrypt sensitive data at rest in Cosmos DB
- [ ] Test for timing attacks on subscription checks
- [ ] Regular security audit of payment code

---

## 12. Cost Estimates

| Item | Cost | Notes |
|------|------|-------|
| Stripe | 2.9% + $0.30 | Per transaction, included in monthly fee |
| Stripe Billing | 0.5% | Of subscription revenue |
| **Total Fee** | **~3.4%** | Example: $99 plan = ~$3.37 fee |
| **Free Plan** | $0 | No transaction fees |
| **10 Pro Users** | ~$33.60/month | 10 × $99 × 3.4% |

---

## 13. Recommended Next Steps

1. **Create Stripe Account** → https://stripe.com/register
2. **Generate API Keys** → Add to Key Vault
3. **Implement SubscriptionService** → Start with simple pricing tiers
4. **Add to User Model** → Extend existing `User` class
5. **Build Pricing Page** → React component with plan cards
6. **Test Webhook Flow** → Use Stripe CLI for local testing
7. **Deploy to Production** → Enable live mode, enable webhooks

---

**Timeline:** 2-3 weeks to full implementation  
**Team:** Backend (1 engineer) + Frontend (1 engineer)  
**Priority:** HIGH - Required for revenue generation before Series A fundraising
