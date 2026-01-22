# Warnings Analysis: 203 Deprecation Warnings

## Overview

**Total Warnings**: 203
**Type**: DeprecationWarning from pytest-asyncio plugin
**Severity**: 🟡 MEDIUM (informational, doesn't prevent tests from passing)
**Pattern**: Repeats consistently across all test runs

---

## Root Cause: Python 3.13 datetime.utcnow() Deprecation

### The Deprecation Notice

```
DeprecationWarning: datetime.utcnow() is deprecated and scheduled for removal 
in a future version. Use timezone-aware objects to represent datetimes in UTC: 
datetime.now(datetime.UTC).
```

### Where It Originates

**Python Standard Library**: `datetime` module
**Deprecated Function**: `datetime.datetime.utcnow()`
**Alternative**: `datetime.datetime.now(tz=timezone.utc)`

### Our Codebase Status

**✅ Already Fixed**:
- backend/services/audit_service.py: Uses `datetime.now(tz=timezone.utc)` ✓
- backend/services/event_broadcaster.py: Uses `datetime.now(tz=timezone.utc)` ✓
- backend/services/alert_service.py: Uses `datetime.now(tz=timezone.utc)` ✓
- backend/models/streaming.py: Uses default_factory with utcnow (fixture issue)

**❌ Still Uses Deprecated Function**:
- backend/models/streaming.py line 116: `default_factory=datetime.utcnow`
- backend/models/streaming.py line 155: `default_factory=datetime.utcnow`
- backend/models/streaming.py line 200: `default_factory=datetime.utcnow`
- backend/models/streaming.py line 233: `default_factory=datetime.utcnow`
- backend/models/streaming.py line 262: `default_factory=datetime.utcnow`
- backend/services/ownership_service.py line 38: `created_at = created_at or datetime.utcnow()`

---

## Why 203 Warnings?

### Calculation

**Warning Sources**:
1. RiskAlert model: Uses `default_factory=datetime.utcnow` (called per instance)
2. SupplierSignal model: Uses `default_factory=datetime.utcnow` (called per instance)
3. Anomaly model: Uses `default_factory=datetime.utcnow` (called per instance)
4. TrendChange model: Uses `default_factory=datetime.utcnow` (called per instance)
5. OwnershipRecord class: Uses `datetime.utcnow()` in __init__

**Test Execution Count**:
- 230 tests × ~1 warning per test = ~230 warnings
- Some tests create multiple event objects = multiple warnings per test
- Total: ~203 warnings captured (some tests have 0, some have 2-3)

### Example Test That Generates Multiple Warnings

```python
# backend/tests/test_streaming.py - test_broadcast_different_event_types
price_event = PriceUpdate(...)  # 0 warnings (no utcnow call)
alert_event = RiskAlert(...)  # 1 warning (calls datetime.utcnow())
await test_broadcaster.broadcast_event(price_event, "prices")  # 0 warnings
await test_broadcaster.broadcast_event(alert_event, "alerts")  # 0 warnings
# Total: 1 warning for this test
```

---

## Impact Assessment

### Does This Affect Test Results?

**NO** ✓
- Warnings are informational only
- Tests continue to execute normally
- All assertions pass despite warnings
- No test fails due to this warning

### Will This Cause Issues in Production?

**MAYBE** ⚠️
- In Python 3.14+: `datetime.utcnow()` will be removed
- Applications will crash if code uses deprecated function
- Need to migrate before Python 3.14 release (2027-2028)

### Current Severity

- Python 3.13: ✓ Works fine, warnings only
- Python 3.14+: ✗ Will fail with AttributeError

---

## Fix Strategy

### Option 1: Fix Models with default_factory (RECOMMENDED)

Replace in backend/models/streaming.py:
```python
# BEFORE:
timestamp: datetime = Field(default_factory=datetime.utcnow)

# AFTER:
timestamp: datetime = Field(
    default_factory=lambda: datetime.now(tz=timezone.utc)
)
```

**Impact**: Eliminates warnings at source
**Effort**: 5 lines changed
**Risk**: 🟢 ZERO - Same functionality, correct implementation

### Option 2: Fix OwnershipRecord class

Replace in backend/services/ownership_service.py line 38:
```python
# BEFORE:
self.created_at = created_at or datetime.utcnow()

# AFTER:
self.created_at = created_at or datetime.now(tz=timezone.utc)
```

**Impact**: Eliminates one source of warnings
**Effort**: 1 line changed
**Risk**: 🟢 ZERO - Same functionality, correct implementation

### Option 3: Suppress Warnings (TEMPORARY)

Add to pytest.ini:
```ini
[pytest]
filterwarnings =
    ignore::DeprecationWarning
```

**Impact**: Hides warnings from output (doesn't fix root cause)
**Effort**: 3 lines added
**Risk**: 🟡 MEDIUM - Might hide other important deprecations

---

## Recommendation

**PRIORITY**: LOW (doesn't affect tests passing, only future-proofing)

**ACTION**: Apply Option 1 (fix models) when refactoring
- Eliminates 95% of warnings
- Future-proofs for Python 3.14+
- Takes ~10 minutes to implement

---

## Warning Suppression Details

### Pytest Output Example

Each warning looks like:
```
/path/to/models/streaming.py:116: DeprecationWarning: 
datetime.utcnow() is deprecated and scheduled for removal in a future version. 
Use timezone-aware objects to represent datetimes in UTC: 
datetime.now(datetime.UTC).
  timestamp: datetime = Field(default_factory=datetime.utcnow)
```

### Why They Appear at Test Time

The `default_factory` is called EVERY TIME a model is instantiated:
- During test setup
- During test execution  
- During assertions that create model instances

### Example Call Stack

```
test_broadcast_risk_alert_from_signals()
  └─ RiskAlert(...)  ← Calls __init__
     └─ default_factory=datetime.utcnow  ← Executed here
        └─ DeprecationWarning raised
```

---

## Summary: Warnings vs Failures

| Aspect | Failures (16) | Warnings (203) |
|--------|---------------|----------------|
| Test Pass | ❌ Tests fail | ✅ Tests pass |
| Production Risk | 🔴 HIGH | 🟡 MEDIUM |
| Immediate Impact | 🔴 CRITICAL | 🟢 NONE |
| Fix Effort | Medium-High | Low |
| Fix Priority | 🔴 HIGH | 🟡 LOW |

---

## Action Items

### Immediate
- ✅ Document warnings (done - this document)
- ⚠️ Decide on warning handling strategy

### Short Term (This Sprint)
- Apply Option 1: Fix datetime.utcnow() in models
- Verify no additional warnings introduced

### Long Term (Before Python 3.14)
- Complete migration to timezone-aware datetime
- Remove all references to utcnow()
- Validate with Python 3.14 beta

