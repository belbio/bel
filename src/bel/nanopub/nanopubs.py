# Standard Library
import gzip
from typing import Any, Iterable, List, Mapping, Optional, Tuple

# Third Party Imports
from loguru import logger

# Local Imports
import bel.core.settings as settings
import bel.lang.belobj
from bel.core.utils import http_client
from bel.schemas.nanopubs import Nanopub
from cityhash import CityHash64


# Following is used in nanopub-tools codebase
def hash_nanopub(nanopub: Mapping[str, Any]) -> str:
    """Create CityHash64 from nanopub for duplicate check

    TODO - check that this hash value is consistent between C# and Python running on
    laptop and server

    Build string to hash

    Collect flat array of (all values.strip()):
        nanopub.type.name
        nanopub.type.version

        One of:
            nanopub.citation.database.name
            nanopub.citation.database.id

            OR

            nanopub.citation.database.uri

            OR

            nanopub.citation.database.reference

        Extend with sorted list of assertions (SRO as single string with space between S, R and O)

        Extend with sorted list of annotations (nanopub.annotations.type + ' ' + nanopub.annotations.id)

    Convert array to string by joining array elements separated by a space

    Create CityHash64(str) and return

    """

    hash_list = []

    # Type
    hash_list.append(nanopub["nanopub"]["type"].get("name", "").strip())
    hash_list.append(nanopub["nanopub"]["type"].get("version", "").strip())

    # Citation
    if nanopub["nanopub"]["citation"].get("database", False):
        hash_list.append(nanopub["nanopub"]["citation"]["database"].get("name", "").strip())
        hash_list.append(nanopub["nanopub"]["citation"]["database"].get("id", "").strip())
    elif nanopub["nanopub"]["citation"].get("uri", False):
        hash_list.append(nanopub["nanopub"]["citation"].get("uri", "").strip())
    elif nanopub["nanopub"]["citation"].get("reference", False):
        hash_list.append(nanopub["nanopub"]["citation"].get("reference", "").strip())

    # Assertions
    assertions = []
    for assertion in nanopub["nanopub"]["assertions"]:
        if assertion.get("relation") is None:
            assertion["relation"] = ""
        if assertion.get("object") is None:
            assertion["object"] = ""
        assertions.append(
            " ".join(
                (
                    assertion["subject"].strip(),
                    assertion.get("relation", "").strip(),
                    assertion.get("object", "").strip(),
                )
            ).strip()
        )
    assertions = sorted(assertions)
    hash_list.extend(assertions)

    # Annotations
    annotations = []

    for anno in nanopub["nanopub"]["annotations"]:
        annotations.append(
            " ".join((anno.get("type", "").strip(), anno.get("id", "").strip())).strip()
        )

    annotations = sorted(annotations)
    hash_list.extend(annotations)

    np_string = " ".join([l.lower() for l in hash_list])

    return "{:x}".format(CityHash64(np_string))
