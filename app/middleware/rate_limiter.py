from flask import abort, request
from time import time
from collections import defaultdict

BUCKETS = defaultdict(lambda: {"tokens": 60, "last": time()})

def rate_limit(max_tokens=60, refill_seconds=60):
    def decorator(f):
        def wrapped(*args, **kwargs):
            key = request.remote_addr or "anonymous"
            bucket = BUCKETS[key]
            now = time()
            elapsed = now - bucket["last"]
            refill = (elapsed / refill_seconds) * max_tokens
            bucket["tokens"] = min(max_tokens, bucket["tokens"] + refill)
            bucket["last"] = now
            if bucket["tokens"] < 1:
                abort(429, "Too many requests")
            bucket["tokens"] -= 1
            return f(*args, **kwargs)
        wrapped.__name__ = f.__name__
        return wrapped
    return decorator
