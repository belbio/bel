"""Various utilities used throughout the BEL package

NOTE: reqsess allows caching external (including ElasticSearch and ArangoDB) REST
      requests for 1 day. This can cause stale results to show up. The cache
      lives for the life of the application using *bel* so you'll need to restart
      the BEL.bio API server if you update the terminologies, you expect major
      changes in the Pubtator results, etc.
"""

import collections
import datetime
import functools
import json
import logging
import tempfile
from timeit import default_timer
from typing import Any, Mapping

import dateutil
import requests
import requests_cache
import ulid
from cityhash import CityHash64
from structlog import get_logger

log = get_logger()

requests_cache.install_cache("requests_cache", backend="sqlite", expire_after=600)


def get_url(url: str, params: dict = {}, timeout: float = 5.0, cache: bool = True):
    """Wrapper for requests.get(url)

    Args:
        url: url to retrieve
        params: query string parameters
        timeout: allow this much time for the request and time it out if over
        cache: Cache for up to a day unless this is false

    Returns:
        Requests Result obj or None if timed out
    """

    try:

        if not cache:
            with requests_cache.disabled():
                r = requests.get(url, params=params, timeout=timeout)
        else:
            r = requests.get(url, params=params, timeout=timeout)

        log.debug(f"Response headers {r.headers}  From cache {r.from_cache}")
        return r

    except requests.exceptions.Timeout:
        log.warn(f"Timed out getting url in get_url: {url}")
        return None
    except Exception as e:
        log.warn(f"Error getting url: {url}  error: {e}")
        return None


def timespan(start_time):
    """Return time in milliseconds from start_time"""

    timespan = datetime.datetime.now() - start_time
    timespan_ms = timespan.total_seconds() * 1000
    return timespan_ms


def download_file(url):
    """Download file"""

    response = requests.get(url, stream=True)
    fp = tempfile.NamedTemporaryFile()
    for chunk in response.iter_content(chunk_size=1024):
        if chunk:  # filter out keep-alive new chunks
            fp.write(chunk)

    # log.info(f'Download file - tmp file: {fp.name}  size: {fp.tell()}')
    return fp


def url_path_param_quoting(param):
    """Quote URL path parameters

    Convert '/' to _FORWARDSLASH_ - otherwise is interpreted as additional path parameter
        gunicorn processes the path prior to Falcon and interprets the
        correct quoting of %2F into a slash
    """
    return param.replace("/", "_FORWARDSLASH_")


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
    """Create CityHash64 bit hash of string

    Args:
        string (str): string to create CityHash64 from

    Returns:
        str: CityHash64
    """

    return str(CityHash64(string))


def _generate_id() -> str:
    """Create ULID

    See: https://github.com/ahawker/ulid

    Returns:
        str: ULID random, unique identifier
    """

    # return str(uuid1())
    return ulid.new()


def dt_utc_formatted():
    """Create UTC ISODate formatted datetime string

    Format: YYYY-MM-DDThh:mm:ss.sssZ
    """
    return f"{datetime.datetime.utcnow().isoformat(timespec='milliseconds')}Z"


def parse_dt(dt: str):
    """Get datetime object from datetime strings"""

    return dateutil.parse(dt)


"""
https://github.com/brouberol/contexttimer/blob/master/contexttimer/__init__.py

Ctimer - A timer context manager measuring the
clock wall time of the code block it contains.
Copyright (C) 2013 Balthazar Rouberol - <brouberol@imap.cc>
This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.
This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.
You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

__version__ = "0.3.3"


class Timer(object):

    """ A timer as a context manager
    Wraps around a timer. A custom timer can be passed
    to the constructor. The default timer is timeit.default_timer.
    Note that the latter measures wall clock time, not CPU time!
    On Unix systems, it corresponds to time.time.
    On Windows systems, it corresponds to time.clock.
    Keyword arguments:
        output -- if True, print output after exiting context.
                  if callable, pass output to callable.
        factor -- 1000 for milliseconds, 1 for seconds
        format -- str.format string to be used for output; default "took {} ms"
        prefix -- string to prepend (plus a space) to output
                  For convenience, if you only specify this, output defaults to True.
    """

    def __init__(
        self, timer=default_timer, factor=1000, output=None, fmt="took {:.1f} ms", prefix=""
    ):
        self.timer = timer
        self.factor = factor
        self.output = output
        self.fmt = fmt
        self.prefix = prefix
        self.end = None

    def __call__(self):
        """ Return the current time """
        return self.timer()

    def __enter__(self):
        """ Set the start time """
        self.start = self()
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        """ Set the end time """
        self.end = self()

        if self.prefix and self.output is None:
            self.output = True

        if self.output:
            output = " ".join([self.prefix, self.fmt.format(self.elapsed)])
            if callable(self.output):
                self.output(output)
            else:
                print(output)

    def __str__(self):
        return "%.3f" % (self.elapsed)

    @property
    def elapsed(self):
        """ Return the current elapsed time since start
        If the `elapsed` property is called in the context manager scope,
        the elapsed time bewteen start and property access is returned.
        However, if it is accessed outside of the context manager scope,
        it returns the elapsed time bewteen entering and exiting the scope.
        The `elapsed` property can thus be accessed at different points within
        the context manager scope, to time different parts of the block.
        """
        if self.end is None:
            # if elapsed is called in the context manager scope
            return (self() - self.start) * self.factor
        else:
            # if elapsed is called out of the context manager scope
            return (self.end - self.start) * self.factor


def timer(
    logger=None,
    level=logging.INFO,
    fmt="function %(function_name)s execution time: %(execution_time).3f",
    *func_or_func_args,
    **timer_kwargs,
):
    """ Function decorator displaying the function execution time
    All kwargs are the arguments taken by the Timer class constructor.
    """
    # store Timer kwargs in local variable so the namespace isn't polluted
    # by different level args and kwargs

    def wrapped_f(f):
        @functools.wraps(f)
        def wrapped(*args, **kwargs):
            with Timer(**timer_kwargs) as t:
                out = f(*args, **kwargs)
            context = {"function_name": f.__name__, "execution_time": t.elapsed}
            if logger:
                logger.log(level, fmt % context, extra=context)
            else:
                print(fmt % context)
            return out

        return wrapped

    if len(func_or_func_args) == 1 and isinstance(func_or_func_args[0], collections.Callable):
        return wrapped_f(func_or_func_args[0])
    else:
        return wrapped_f
