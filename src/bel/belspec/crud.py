# Standard Library
from typing import Mapping

# Third Party Imports
from loguru import logger

# Local Imports
import bel.core.settings as settings
import bel.db.arangodb as arangodb
import cachetools
import semver
from bel.belspec.enhance import create_ebnf_parser, create_enhanced_specification
from bel.schemas.belspec import BelSpec, BelSpecVersions


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
        try:
            versions.append(semver.VersionInfo.parse(version_str))
        except:
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

    version_strings = list(bel_db.aql.execute(query))
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


def check_version(version: str = "latest") -> str:
    """ Check if version is valid and if not return default or latest """

    if not version:
        version = settings.BEL_DEFAULT_VERSION

    bel_versions = get_belspec_versions()

    if version == "latest":
        version = bel_versions["latest"]
    elif version not in bel_versions["versions"]:
        logger.warning(
            f"Cannot validate with invalid version: {version} which is not in BEL Versions: {bel_versions} - using latest version instead"
        )
        version = bel_versions["latest"]

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

    doc = {
        "_key": f"belspec_{version}",
        "doc_type": "belhelp",
        "belhelp": belhelp,
    }

    bel_config_coll.insert(doc, overwrite=True)


def delete_belhelp(version: str):
    """Delete BEL specification help"""

    if version == "latest":
        raise ValueError("Cannot delete `latest` version")

    r = bel_config_coll.delete(f"belhelp_{version}")
