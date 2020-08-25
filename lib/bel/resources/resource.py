# Standard Library
import copy
import gzip
import json

# Third Party Imports
from loguru import logger

# Local Imports
import bel.core.utils
import bel.db.arangodb as arangodb
import bel.db.elasticsearch as elasticsearch
import bel.resources.namespace
import bel.resources.ortholog

()


def load_resource(resource_url: str = None, resource_fn: str = None, force: bool = False):
    """Load BEL Resource file

    Forceupdate will create a new index in Elasticsearch regardless of whether
    an index with the resource version already exists.

    Args:
        resource_url: URL from which to download the resource to load into the BEL API
        resource_fn: filename for resource file
        force: force full update - e.g. don't leave Elasticsearch indexes alone if their version ID matches
    """

    if resource_url:
        logger.info(f"Loading resource {resource_url}")
    elif resource_fn:
        logger.info(f"Loading resource {resource_fn}")

    # Download resource from url
    if resource_url:
        fp = bel.core.utils.download_file(resource_url)
        fp.seek(0)
        f = gzip.open(fp, "rt")
    elif resource_fn:
        f = gzip.open(resource_fn, "rt")

    if not f:
        logger.error(f"Could not open resource file: {resource_url} or {resource_fn}")
        return "Failed to read resource file"

    metadata = json.loads(f.__next__())

    if "metadata" not in metadata:
        logger.error(f"Missing metadata entry for {resource_url}")
        return "Cannot load resource file - missing metadata object in first line of file"

    metadata = metadata["metadata"]

    # Load resource files
    if metadata["resource_type"] == "namespace":
        bel.resources.namespace.load_terms(f, metadata, force)

    elif metadata["resource_type"] == "orthologs":
        bel.resources.ortholog.load_orthologs(f, metadata)
    else:
        logger.info(f"Unrecognized resource type: {metadata['metadata']['type']}")

    f.close
