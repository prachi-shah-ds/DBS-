import uuid
from flask import g, request

def request_id_middleware(app):
    @app.before_request
    def assign_request_id():
        rid = request.headers.get("X-Request-Id") or str(uuid.uuid4())
        g.request_id = rid
    @app.after_request
    def add_request_id(response):
        response.headers["X-Request-Id"] = g.get("request_id")
        return response
