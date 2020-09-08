# Standard Library
import copy
import gzip
import json

# Third Party Imports
from loguru import logger

# Local Imports
import bel.core.settings as settings
import bel.core.utils
import bel.core.mail
import bel.db.arangodb as arangodb
import bel.db.elasticsearch as elasticsearch
import bel.resources.namespace
import bel.resources.ortholog

from bel.schemas.config import Configuration


def create_msg_body(results):
    """Create email message body for update_resources"""

    body = ""
    for url in results:
        body += f"Resource: {url}\n"
        result = results[url]
        if result["success"]:
            body += f"   Successful\n"
        else:
            body += f"   FAILED\n"
        
        for message in result["messages"]:
            body += f"   {message}\n"
        
        body += "\n\n"
    
    return body


def update_resources(url: str = None, force: bool = False, email: str = None):
    """Update bel resources

    Reads the arangodb bel.bel_config.configuration.update_bel_resources object
    to figure out what bel resource urls to process

    Args:
        url: url to bel resource file as *.jsonl.gz
    """
    
    results = {}

    bel_config_collection = arangodb.bel_config_collection

    configuration = bel_config_collection.get("configuration")

    for key in configuration["update_bel_resources"]:
        for url in configuration["update_bel_resources"]:
            result = load_resource(resource_url=url, force=force)
            results[url] = result

    if email is not None:
        subject = f"BEL Resources Update for {settings.HOST_NAME}"
        body = create_msg_body(results)
        bel.core.mail.send_simple_email(email, subject, body)


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
    first_item = json.loads(f.__next__())

    first_item_key = list(first_item.keys())[0]
    if first_item_key in ['term', 'ortholog'] and "metadata" not in metadata:
        logger.error(f"Missing metadata entry for {resource_url}")
        return "Cannot load resource file - missing metadata object in first line of file"

    metadata = metadata["metadata"]

    result = {}
    # Load resource files
    if metadata["resource_type"] == "namespace":
        result = bel.resources.namespace.load_terms(f, metadata, force)

    elif metadata["resource_type"] == "orthologs":
        result = bel.resources.ortholog.load_orthologs(f, metadata)

    else:
        logger.info(f"Unrecognized resource type: {metadata['metadata']['type']}")

    f.close
    return result
