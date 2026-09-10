import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration

def init_sentry(app):
    sentry_dsn = app.config.get("SENTRY_DSN")
    if sentry_dsn:
        sentry_sdk.init(dsn=sentry_dsn, integrations=[FlaskIntegration()], traces_sample_rate=0.1)
