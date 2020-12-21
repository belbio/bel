# Standard Library
import json
from typing import List, Tuple

# Third Party
import redis
from loguru import logger

# Local
import bel.core.settings as settings

redis_db = redis.Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT, db=0)

batch_cnt = 5  # TODO increase after initial testing


"""Notes

Queues:
    mq stands for message queue

    stores: [bel]

    mq:{store}
    mq:{store}:worker:{uuid}

    task should be formatted f"{url}:::{id}:::{action}"
        handles add/remove in a single queue

"""


def queue_lengths(stores: List[str] = [settings.REDIS_QUEUE]):
    """Collect message queue lengths"""

    qlens = {}
    for store in stores:
        key = f"mq:{store}"
        qlens[key] = redis_db.llen(key)

    return qlens


def reset_queues(stores: List[str] = [settings.REDIS_QUEUE]):
    """Reset all of the queues including the worker processing queues"""

    for store in stores:
        for key in redis_db.keys(f"mq:{store}:*"):
            redis_db.ltrim(key, 1, 0)  # Clear all elements by setting start>end
