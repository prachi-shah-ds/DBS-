import logging
from structlog import wrap_logger, configure, processors, stdlib

def configure_structlog():
    configure(
        processors=[processors.TimeStamper(fmt="iso"), processors.JSONRenderer()],
        logger_factory=stdlib.LoggerFactory()
    )

def get_logger(name=None):
    logger = logging.getLogger(name)
    return wrap_logger(logger)
