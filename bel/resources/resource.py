import timy
import json
import gzip
import copy

import bel.utils
import bel.db.elasticsearch as elasticsearch
import bel.db.arangodb as arangodb

import bel.resources.namespace
import bel.resources.ortholog

from bel.Config import config

from structlog import get_logger
log = get_logger()

# Set timy to track in logging mode (INFO level)
timy.timy_config.tracking_mode = timy.TrackingMode.LOGGING


def load_resource(resource_url: str, forceupdate: bool = False):
    """Load BEL Resource file

    Forceupdate will create a new index in Elasticsearch regardless of whether
    an index with the resource version already exists.

    Args:
        resource_url: URL from which to download the resource to load into the BEL API
        forceupdate: force full update - e.g. don't leave Elasticsearch indexes alone if their version ID matches
    """

    log.info(f'Loading resource {resource_url}')

    try:
        # Download resource
        fo = bel.utils.download_file(resource_url)

        if not fo:
            log.error(f'Could not download and open file {resource_url}')
            return "Failed to download resource_url"

        # Get metadata
        fo.seek(0)
        with gzip.open(fo, 'rt') as f:
            metadata = json.loads(f.__next__())

        if 'metadata' not in metadata:
            log.error(f'Missing metadata entry for {resource_url}')
            return "Cannot load resource file - missing metadata object in first line of file"

        # Load resource files
        if metadata['metadata']['type'] == 'namespace':
            bel.resources.namespace.load_terms(fo, metadata, forceupdate)

        elif metadata['metadata']['type'] == 'ortholog':
            bel.resources.ortholog.load_orthologs(fo, metadata)

    finally:
        fo.close()
