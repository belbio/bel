# Standard Library
import time

# Local Imports
import bel.core.settings as settings
import dramatiq
from dramatiq.brokers.redis import RedisBroker
from loguru import logger

redis_broker = RedisBroker(
    url=f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}", namespace="belapi", port=6379
)

dramatiq.set_broker(redis_broker)

LOW = 100
MED = 50
HI = 0


# NOTE - time_limit is in milliseconds


@dramatiq.actor(priority=LOW, time_limit=864000000)
def update_pipeline():
    """ Push all nanopubs into the BEL Pipeline

    time_limit = 864000000ms = 10 days
    """

    pass

    # services.nanopubs.flush_all_to_edgestore()


# NOTE - Structlog doesn't work with dramatiq - have to use logging module directly
#           also doesn't appear to respect log_level
