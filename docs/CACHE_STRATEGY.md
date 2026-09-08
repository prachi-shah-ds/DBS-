# Jodo Caching Strategy — Phase 10

## Overview

This document outlines the cache key structure, invalidation policy, and TTL (Time-To-Live) configuration for Jodo's Redis caching layer.

**Goal:** Reduce database load, improve response times, and maintain data consistency across the system.

---

## 1. Architecture

```
┌─────────────┐
│   Browser   │
└──────┬──────┘
       │ HTTP Request
       ▼
┌─────────────────────┐
│   Flask Route       │
└──────┬──────────────┘
       │ Check Cache?
       ▼
┌──────────────────────────┐
│  Redis Cache Layer       │  ◄─── Cache Hit: return instantly
│  (Key-Value Store)       │       Cache Miss: fetch & store
└──────┬───────────────────┘
       │
       ▼
┌──────────────────────────┐
│  Data Layer              │
│  (Mock or Odoo)          │
└──────────────────────────┘
```

---

## 2. Cache Keys Structure

All cache keys follow the pattern: `jodo:<category>:<resource>:<identifier>`

### Key Prefixes

| Category | Prefix | Example | TTL |
|----------|--------|---------|-----|
| Session | `jodo:session:` | `jodo:session:user_123` | 24 hours |
| Stock Data | `jodo:stock:` | `jodo:stock:SKU-1042` | 5 min |
| Transfers | `jodo:transfer:` | `jodo:transfer:WH/OUT/001` | 10 min |
| Alerts | `jodo:alert:` | `jodo:alert:user_123:all` | 5 min |
| User Profile | `jodo:user:` | `jodo:user:profile:user_123` | 1 hour |
| AI History | `jodo:ai_history:` | `jodo:ai_history:user_123:session_1` | 24 hours |
| Rate Limit | `jodo:rate_limit:` | `jodo:rate_limit:api:user_123` | 1 min |

---

## 3. TTL (Time-To-Live) Configuration

### Rationale

**Volatile Data (Short TTL):**
- Stock levels, transfers, alerts change frequently → cache for 5–10 minutes
- User sees data that's at most 5–10 minutes old (acceptable for ops)

**Semi-Static Data (Medium TTL):**
- User profiles, customer data change occasionally → cache for 1 hour
- User sees data that's at most 1 hour old (acceptable for profiles)

**Persistent Data (Long TTL):**
- Session tokens, AI conversation history → cache for 24 hours
- Explicit logout or conversation close triggers invalidation

| Data Type | TTL | Reason |
|-----------|-----|--------|
| Stock Levels | 5 min | Stock changes as transfers happen; 5-min staleness acceptable |
| Transfers | 10 min | Transfers are less frequent than stock changes |
| Alerts | 5 min | Alerts tie to stock data; refresh together |
| User Sessions | 24 hours | Sessions are long-lived; explicit logout clears cache |
| User Profiles | 1 hour | Profiles change rarely; hourly refresh sufficient |
| AI History | 24 hours | Conversations are session-scoped; cleared on logout |
| Rate Limiting | 1 min | Rate limit window is 1 minute |

---

## 4. Invalidation Policy

### Event-Driven Invalidation

Cache is invalidated in response to these events:

#### Stock Update
**When:** A product's stock level changes (via reorder, transfer, receipt)
**Action:** Invalidate `jodo:stock:*` pattern
**Effect:** Next dashboard load fetches fresh stock data

```python
# Example: After a transfer completes
def complete_transfer(transfer_id):
    # ... update database ...
    cache.invalidate_pattern("jodo:stock:*")       # Flush stock cache
    cache.invalidate_pattern("jodo:alert:*")       # Flush alerts (depends on stock)
```

#### Transfer Created/Updated
**When:** New transfer is raised or an existing transfer is modified
**Action:** Invalidate `jodo:transfer:*` pattern
**Effect:** Next dashboard load shows updated transfer list

#### Alert Triggered
**When:** A product's stock drops below minimum threshold
**Action:** Invalidate `jodo:alert:*` pattern
**Effect:** Dashboard immediately shows new alert

#### User Login
**When:** User logs in
**Action:** Create new session cache entry; old entry expires naturally
**Effect:** Session persists for 24 hours or until logout

#### User Logout
**When:** User clicks logout
**Action:** Delete `jodo:session:user_<id>` immediately
**Effect:** User must log in again on next visit

#### Full Flush (Emergency)
**When:** Database is reset, major data migration, or debugging
**Action:** Invalidate `jodo:*` (all keys)
**Effect:** All caches cleared; system fetches fresh data on next request

---

## 5. Cache Hit/Miss Strategy

### Pseudo-Code

```python
def get_stock_with_cache(sku):
    cache_key = f"jodo:stock:{sku}"
    
    # Check cache first
    cached_data = cache.get(cache_key)
    if cached_data:
        return cached_data  # Cache hit ✓
    
    # Cache miss: fetch from data layer
    fresh_data = fetch_from_odoo(sku)
    
    # Store in cache with 5-minute TTL
    cache.set(cache_key, fresh_data, ttl=300)
    
    return fresh_data
```

### Flow

```
Request for Stock Level
   ↓
[Check Redis Cache]
   ├─ HIT: Return cached value immediately ✓ (fast)
   └─ MISS:
       ↓
       [Fetch from Odoo/Mock Data]
           ↓
       [Store in Redis with TTL]
           ↓
       [Return to client]
       (slower, but updates cache)
```

---

## 6. Rate Limiting (Bonus)

Use Redis to track API request counts per user/IP:

```python
def check_rate_limit(user_id, max_requests=100, window_seconds=60):
    key = f"jodo:rate_limit:api:{user_id}"
    current_count = cache.increment(key)  # Atomic increment
    
    if current_count == 1:
        # First request in this window; set expiry
        cache.set_with_expiry(key, current_count, window_seconds)
    
    if current_count > max_requests:
        return False  # Rate limit exceeded
    
    return True  # Within limit
```

---

## 7. Monitoring & Debugging

### Cache Metrics to Track
- **Cache Hit Ratio:** (hits) / (hits + misses)
- **Average Response Time:** with cache vs without cache
- **Memory Usage:** Redis memory consumption

### Debugging Commands

```bash
# View all Jodo keys
REDIS_CLI> KEYS jodo:*

# Check a specific key's TTL
REDIS_CLI> TTL jodo:stock:SKU-1042

# View key value
REDIS_CLI> GET jodo:stock:SKU-1042

# Flush all Jodo cache
REDIS_CLI> DEL jodo:*

# Monitor cache operations in real-time
REDIS_CLI> MONITOR
```

---

## 8. Edge Cases & Fallback

### Redis Unavailable
**What happens:**
- `redis_client` is `None`
- `cache_manager` checks `if not self.redis` and returns None/False
- Flask route detects cache miss and fetches directly from data layer
- **Result:** App continues to work (slower, but functional)

### Stale Cache During Data Update
**Problem:** User A updates stock; cache isn't invalidated yet; User B sees stale stock.
**Solution:** Explicit invalidation on write operation (above)

### Cache Key Collision
**Problem:** Two different resources have same key
**Prevention:** Use hierarchical keys: `jodo:<category>:<resource>:<id>`

---

## 9. Future Enhancements

- **Cache Warming:** Pre-load frequently accessed data on app startup
- **L2 Cache:** Local in-memory cache (e.g., `functools.lru_cache`) before Redis
- **Cache Versioning:** Add version numbers to keys to invalidate old versions
- **Predictive Invalidation:** Invalidate cache based on time of day (e.g., end of shift)

---

## Summary

| Key Concept | Value |
|-------------|-------|
| **Cache Tool** | Redis (in-memory key-value store) |
| **Key Pattern** | `jodo:<category>:<resource>:<id>` |
| **Default TTLs** | 5 min (stock) → 24 hours (sessions) |
| **Invalidation** | Event-driven (stock/transfer/alert changes) |
| **Fallback** | If Redis down, app fetches directly from data layer |
| **Goal** | Reduce load on Odoo/mock data; improve response time |

---

*Last updated: [date] · Maintained by P1*
