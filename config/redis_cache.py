"""Redis cache configuration for Jodo — Phase 10 caching strategy.

This module sets up and manages the Redis caching layer for:
- Session store (user login sessions)
- Dashboard data cache (stock levels, transfers, alerts)
- AI agent conversation history
- Rate limiting and request throttling
"""

import os
import redis
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

# ============ REDIS CONNECTION ============
REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
REDIS_DB = int(os.getenv('REDIS_DB', 0))
REDIS_PASSWORD = os.getenv('REDIS_PASSWORD', None)

# Initialize Redis client
try:
    redis_client = redis.Redis(
        host=REDIS_HOST,
        port=REDIS_PORT,
        db=REDIS_DB,
        password=REDIS_PASSWORD,
        decode_responses=True,
        socket_connect_timeout=5,
        socket_keepalive=True,
        health_check_interval=30
    )
    # Test connection
    redis_client.ping()
    print(f"✓ Redis connected: {REDIS_HOST}:{REDIS_PORT}")
except redis.ConnectionError as e:
    print(f"✗ Redis connection failed: {e}")
    redis_client = None

# ============ CACHE KEY PREFIXES ============
CACHE_PREFIX = "jodo:"
KEY_PREFIXES = {
    'session': f"{CACHE_PREFIX}session:",
    'stock': f"{CACHE_PREFIX}stock:",
    'transfer': f"{CACHE_PREFIX}transfer:",
    'alert': f"{CACHE_PREFIX}alert:",
    'user': f"{CACHE_PREFIX}user:",
    'ai_history': f"{CACHE_PREFIX}ai_history:",
    'rate_limit': f"{CACHE_PREFIX}rate_limit:",
}

# ============ TTL (TIME-TO-LIVE) CONFIGURATION ============
TTL_CONFIG = {
    'session': timedelta(hours=24),              # User sessions expire in 24 hours
    'stock_data': timedelta(minutes=5),          # Stock cache expires in 5 min (volatile data)
    'transfer_data': timedelta(minutes=10),      # Transfer data cache expires in 10 min
    'alert_data': timedelta(minutes=5),          # Alerts refresh every 5 min
    'user_profile': timedelta(hours=1),          # User data expires in 1 hour
    'ai_history': timedelta(hours=24),           # AI conversation history expires in 24 hours
    'rate_limit': timedelta(minutes=1),          # Rate limit window is 1 minute
}

# ============ CACHE OPERATIONS ============
class CacheManager:
    """Manages all caching operations for Jodo."""

    def __init__(self, redis_conn):
        self.redis = redis_conn

    def get(self, key):
        """Retrieve a value from cache."""
        if not self.redis:
            return None
        try:
            return self.redis.get(key)
        except redis.RedisError as e:
            print(f"Cache GET error: {e}")
            return None

    def set(self, key, value, ttl=None):
        """Store a value in cache with optional TTL."""
        if not self.redis:
            return False
        try:
            if ttl:
                self.redis.setex(key, ttl, value)
            else:
                self.redis.set(key, value)
            return True
        except redis.RedisError as e:
            print(f"Cache SET error: {e}")
            return False

    def delete(self, key):
        """Remove a key from cache."""
        if not self.redis:
            return False
        try:
            self.redis.delete(key)
            return True
        except redis.RedisError as e:
            print(f"Cache DELETE error: {e}")
            return False

    def invalidate_pattern(self, pattern):
        """Invalidate all keys matching a pattern (e.g., 'stock:*')."""
        if not self.redis:
            return 0
        try:
            keys = self.redis.keys(pattern)
            if keys:
                return self.redis.delete(*keys)
            return 0
        except redis.RedisError as e:
            print(f"Cache INVALIDATE error: {e}")
            return 0

    def increment(self, key, amount=1):
        """Increment a counter (for rate limiting)."""
        if not self.redis:
            return 0
        try:
            return self.redis.incr(key, amount)
        except redis.RedisError as e:
            print(f"Cache INCR error: {e}")
            return 0

    def set_with_expiry(self, key, value, seconds):
        """Set a key with expiry in seconds."""
        if not self.redis:
            return False
        try:
            self.redis.setex(key, seconds, value)
            return True
        except redis.RedisError as e:
            print(f"Cache SETEX error: {e}")
            return False

# ============ CACHE INVALIDATION TRIGGERS ============
INVALIDATION_EVENTS = {
    'stock_updated': f"{KEY_PREFIXES['stock']}*",      # Invalidate all stock caches when stock changes
    'transfer_created': f"{KEY_PREFIXES['transfer']}*",  # Invalidate transfer cache on new transfer
    'alert_triggered': f"{KEY_PREFIXES['alert']}*",      # Invalidate alerts when new alert fires
    'user_login': f"{KEY_PREFIXES['session']}*",          # Invalidate session on login (replace with new)
    'full_flush': "jodo:*",                             # Nuclear option: flush all Jodo cache
}

# ============ INITIALIZATION ============
cache_manager = CacheManager(redis_client) if redis_client else None
