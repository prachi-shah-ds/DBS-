from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from flask import request
import time

REQUEST_COUNT = Counter("app_requests_total", "Total HTTP requests", ["method", "endpoint", "http_status"])
REQUEST_LATENCY = Histogram("app_request_latency_seconds", "Request latency", ["endpoint"])

def init_metrics(app):
    @app.before_request
    def start_timer():
        request._start_time = time.time()

    @app.after_request
    def record(response):
        elapsed = time.time() - getattr(request, "_start_time", time.time())
        REQUEST_COUNT.labels(request.method, request.path, response.status_code).inc()
        REQUEST_LATENCY.labels(request.path).observe(elapsed)
        return response

    @app.route("/metrics")
    def metrics():
        return generate_latest(), 200, {"Content-Type": CONTENT_TYPE_LATEST}
