"""Various utilities used throughout the BEL package"""

# Standard Library
import collections
import datetime
import functools
import json
import re
import tempfile
from timeit import default_timer
from typing import Any, Mapping

# Third Party Imports
import ulid

# Local Imports
import dateutil
import httpx
from cityhash import CityHash64
from loguru import logger

# Namespace Argument Regex pattern
# first section looks for NS:ID!LABEL in function - (([\w\.]+)\s*:\s*(".*?"|\w+)\s*!?\s*(".*?"|\w+)?)[\,\)]
# second section looks for a bare NS:ID!LABEL - (([\w\.]+)\s*:\s*(".*?"|\w+)\s*!?\s*(".*?"|\w+)?)
# order is important
# nsarg_pattern = re.compile(
#     r'((?P<ns>[\w\.]+)\s*:?\s*(?P<id>".*?"|\w+)\s*!?\s*(?P<label>".*?"|\w+)?)[\,\)]|((?P<ns2>[\w\.]+)\s*:\s*(?P<id2>".*?"|\w+)\s*!?\s*(?P<label2>".*?"|\w+)?)'
# )

nsarg_pattern = re.compile(
    r"""
    (?P<ns_arg>
        (?P<ns>[\w\.]+)        # namespace
        \s*:\s*                # ns:id separator
        (?P<id>".*?"|\w+)      # id
        (\s*!\s*)?             # id!label separator
        (?P<label>".*?"|\w+)?  # optional label
    )
    [\,\)]?                    # stop match
    
""",
    re.VERBOSE,
)

# Quotes pattern
escaped_quotes_pattern = re.compile(r'\\(")')
quotes_pattern = re.compile(r'(")')


def get_http_client():
    """Client for http requests"""

    return httpx.Client()


http_client = get_http_client()


def namespace_quoting(string: str) -> str:
    """Normalize NSArg ID and Label

    If needs quotes (only if it contains whitespace, comma or ')' ), make sure
    it is quoted, else remove quotes

    Also escape any internal double quotes
    """

    # Remove quotes if exist
    match = re.match(r'\s*"(.*)"\s*$', string)
    if match:
        string = match.group(1)

    string = string.strip()  # remove external whitespace

    string = string.replace('"', '"')  # quote internal double quotes

    # quote only if it contains whitespace, comma, ! or ')'
    if re.search(r"[),\!\s]", string):
        return f'"{string}"'

    return string


def split_key_label(key_label: str) -> dict:
    """Split key label into components ns:id!label"""

    match = nsarg_pattern.match(key_label)

    namespace, id_, label = "", "", ""

    if not match:
        return (namespace, id_, label)

    namespace = (match.group("ns"),)
    id_ = (match.group("id"),)
    if match.group("label"):
        label = (match.group("label"),)

    if isinstance(namespace, tuple):
        namespace = namespace[0]
    if isinstance(id_, tuple):
        id_ = id_[0]
    if isinstance(label, tuple):
        label = label[0]

    return (namespace, id_, label)


def timespan(start_time):
    """Return time in milliseconds from start_time"""

    timespan = datetime.datetime.now() - start_time
    timespan_ms = timespan.total_seconds() * 1000
    return timespan_ms


def download_file(url):
    """Download file"""

    with http_client.stream("GET", url) as response:

        fp = tempfile.NamedTemporaryFile()
        for chunk in response.iter_bytes():
            if chunk:  # filter out keep-alive new chunks
                fp.write(chunk)

        # logger.info(f'Download file - tmp file: {fp.name}  size: {fp.tell()}')
        return fp


def url_path_param_quoting(param):
    """Quote URL path parameters

    Convert '/' to _FORWARDSLASH_ - otherwise is interpreted as additional path parameter
        gunicorn processes the path prior to Falcon and interprets the
        correct quoting of %2F into a slash
    """
    return param.replace("/", "_FORWARDSLASH_")


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

    return ulid.new()


def dt_utc_formatted():
    """Create UTC ISODate formatted datetime string

    Format: YYYY-MM-DDThh:mm:ss.sssZ
    """
    return f"{datetime.datetime.utcnow().isoformat(timespec='milliseconds')}Z"


def parse_dt(dt: str):
    """Get datetime object from datetime strings"""

    return dateutil.parse(dt)


