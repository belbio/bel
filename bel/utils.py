import ulid
import mmh3
import json
from typing import Mapping, Any

import logging
log = logging.getLogger(__name__)


def first_true(iterable, default=False, pred=None):
    """Returns the first true value in the iterable.

    If no true value is found, returns *default*

    If *pred* is not None, returns the first item
    for which pred(item) is true.

    """
    # first_true([a,b,c], x) --> a or b or c or x
    # first_true([a,b], x, f) --> a if f(a) else b if f(b) else x
    return next(filter(pred, iterable), default)


def _create_hash_from_doc(doc: Mapping[str, Any]) -> str:
    """Create hash Id from edge record

    Args:
        edge (Mapping[str, Any]): edge record to create hash from

    Returns:
        str: Murmur3 128 bit hash
    """

    doc_string = json.dumps(doc, sort_keys=True)
    return _create_hash(doc_string)


def _create_hash(string: str) -> str:
    """Create Murmur3 128 bit hash of string

    Args:
        string (str): string to create Murmur3 128bit hash from

    Returns:
        str: Murmur3 128 bit hash
    """

    return mmh3.hash128(string)


def _generate_id() -> str:
    """Create ULID

    See: https://github.com/ahawker/ulid

    Returns:
        str: ULID random, unique identifier
    """

    # return str(uuid1())
    return ulid.new()


# TODO - doesn't this replicate functionality of timy package?
class FuncTimer():
    """ Convenience class to time function calls

    Use via the "with" keyword ::

        with Functimer("Expensive Function call"):
            foo = expensiveFunction(bar)

    A timer will be displayed in the current logger as `"Starting expensive function call ..."`
    then when the code exits the with statement, the log will mention `"Finished expensive function call in 28.42s"`

    By default, all FuncTimer log messages are written at the `logging.DEBUG` level. For info-level messages, set the
    `FuncTimer.info`  argument to `True`::

        with Functimer("Expensive Function call",info=True):
            foo = expensiveFunction(bar)
    """
    import time

    def __init__(self, funcName, info=False):

        self.funcName = funcName
        self.infoLogLevel = True

    def __enter__(self):
        log.debug("Starting {} ...".format(self.funcName))
        self.start = time.clock()
        return self

    def __exit__(self, *args):
        self.end = time.clock()
        self.interval = self.end - self.start
        log.info("{} over in {}s".format(self.funcName, self.interval).capitalize())
