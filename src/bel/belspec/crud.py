# Standard Library
from typing import Mapping

# Third Party
# Local Imports
import bel.core.settings as settings
import bel.db.arangodb as arangodb
import cachetools
import semver
from bel.belspec.enhance import create_ebnf_parser, create_enhanced_specification
from bel.schemas.belspec import BelSpec, BelSpecVersions

# Third Party Imports
from loguru import logger

# ArangoDB handles
bel_db = arangodb.bel_db
bel_config_name = arangodb.bel_config_name
bel_config_coll = arangodb.bel_config_coll


""" Notes

belspec_versions = {doc_type: belspec_versions, versions: List[], latest: str}

belspec_{version} = {doc_type: belspec, belspec: <belspec>, enhanced_belspec: <enhanced_belspec>}

belhelp_{version} = {doc_type: belhelp, belhelp: <belhelp>}

"""


def get_latest_version() -> str:
    """Get latest version of BEL installed"""

    doc = bel_config_coll.get("belspec_versions")

    return doc["latest"]


def get_default_version() -> str:
    """Get default BEL version"""

    return settings.BEL_DEFAULT_VERSION


def max_semantic_version(version_strings) -> str:
    """Return max semantic version from list"""

    versions = []
    for version_str in version_strings:
        if version_str == "latest":
            continue

        try:
            versions.append(semver.VersionInfo.parse(version_str))
        except Exception:
            pass  # Skip non-semantic versioned belspecs for latest version

    max_version = str(max(versions))

    return max_version


def update_belspec_versions():
    """Update BEL Spec versions record

    And adding the latest version
    """

    query = f"""
    FOR doc IN {bel_config_name}
        FILTER doc.doc_type == "belspec"
        RETURN doc.orig_belspec.version
    """

    version_strings = sorted(list(bel_db.aql.execute(query)), reverse=True)
    latest = max_semantic_version(version_strings)

    doc = {
        "_key": "belspec_versions",
        "doc_type": "belspec_versions",
        "latest": latest,
        "default": settings.BEL_DEFAULT_VERSION,
        "versions": version_strings,
    }

    bel_config_coll.insert(doc, overwrite=True)


@cachetools.cached(cachetools.TTLCache(maxsize=1, ttl=600))
def get_belspec_versions() -> dict:

    doc = bel_config_coll.get(f"belspec_versions")

    doc["versions"].insert(0, "latest")

    if "latest" in doc:
        return BelSpecVersions(**doc).dict()

    else:
        return {}


def get_best_match(query_str, belspec_versions: BelSpecVersions):
    """Get best match to query version in versions or return latest"""

    try:
        query = semver.VersionInfo.parse(query_str)
    except Exception as e:
        logger.warning(
            f"Could not parse belspec version {query_str} - returning latest version instead"
        )
        return belspec_versions["latest"]

    versions = []
    for version_str in sorted(belspec_versions["versions"], reverse=True):
        if version_str == "latest":
            continue
        try:
            versions.append(semver.VersionInfo.parse(version_str))
        except Exception:
            pass  # Skip non-semantic versioned belspecs for latest version

    match = None
    matches = 0
    for version in versions:
        if (
            query.major == version.major
            and query.minor == version.minor
            and query.patch == version.patch
        ):
            if matches < 3:
                match = version
            matches = 3

        elif query.major == version.major and query.minor == version.minor:
            if matches < 2:
                match = version
            matches = 2

        elif query.major == version.major:
            if matches < 1:
                match = version
            matches = 1

    if not match:
        return belspec_versions["latest"]

    return str(match)


def check_version(version: str = "latest", versions: BelSpecVersions = None) -> str:
    """ Check if version is valid and if not return default or latest """

    if not version:
        version = settings.BEL_DEFAULT_VERSION

    if versions is None:
        versions = get_belspec_versions()

    if version == "latest":
        version = versions["latest"]

    elif version not in versions["versions"]:
        original_version = version
        version = get_best_match(version, versions)
        # logger.debug(f"BEL version {original_version} out of date using {version}")

    return version


def get_belspec(version: str = "latest") -> dict:
    """Get original/unenhanced belspec"""

    if version == "latest":
        version = get_latest_version()

    doc = bel_config_coll.get(f"belspec_{version}")

    if "orig_belspec" in doc:
        return doc["orig_belspec"]
    else:
        return {}


@cachetools.cached(cachetools.TTLCache(maxsize=10, ttl=600))
def get_enhanced_belspec(version: str = "latest") -> dict:
    """Get enhanced belspec"""

    if version == "latest":
        version = get_latest_version()

    doc = bel_config_coll.get(f"belspec_{version}")

    if doc is not None and "enhanced_belspec" in doc:
        return doc["enhanced_belspec"]
    else:
        return {}


def get_ebnf(version) -> str:
    """Generate EBNF from BEL Specification"""

    if version == "latest":
        version = get_latest_version()

    doc = bel_config_coll.get(f"belspec_{version}")

    if "orig_belspec" in doc:
        ebnf = create_ebnf_parser(doc["orig_belspec"])
        return ebnf
    else:
        return f"No Specification found for {version}"


def update_belspec(belspec: BelSpec):
    """Create or update belspec"""

    belspec = belspec.dict()

    version = belspec["version"]
    enhanced_belspec = create_enhanced_specification(belspec)

    doc = {
        "_key": f"belspec_{version}",
        "doc_type": "belspec",
        "orig_belspec": belspec,
        "enhanced_belspec": enhanced_belspec,
    }

    result = bel_config_coll.insert(doc, overwrite=True)

    logger.info("Result of loading belspec", version=version, result=result)

    update_belspec_versions()


def delete_belspec(version: str):
    """Delete BEL specification"""

    if version == "latest":
        raise ValueError("Cannot delete `latest` version")

    bel_config_coll.delete(f"belspec_{version}")

    update_belspec_versions()


def get_belhelp(version: str = "latest") -> dict:
    """Get BELspec Help

    This document contains supporting documentation for functions and relations
    for the BELSpec
    """

    if version == "latest":
        version = get_latest_version()

    doc = bel_config_coll.get(f"belhelp_{version}")

    return doc["belhelp"]


def update_belhelp(belhelp: dict):
    """Create or update belhelp"""

    version = belhelp["version"]

    doc = {"_key": f"belspec_{version}", "doc_type": "belhelp", "belhelp": belhelp}

    bel_config_coll.insert(doc, overwrite=True)


def delete_belhelp(version: str):
    """Delete BEL specification help"""

    if version == "latest":
        raise ValueError("Cannot delete `latest` version")

    r = bel_config_coll.delete(f"belhelp_{version}")
