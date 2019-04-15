import os
import yaml
from elasticsearch import Elasticsearch
import elasticsearch.helpers

from bel.Config import config

import logging

log = logging.getLogger(__name__)

cur_dir_name = os.path.dirname(os.path.realpath(__file__))
mappings_terms_fn = f"{cur_dir_name}/es_mappings_terms.yml"
terms_alias = "terms"


def get_all_index_names(es):
    """Get all index names"""

    indices = es.indices.get_alias()

    return indices


def add_index_alias(es, index_name, alias_name):
    """Add index alias to index_name"""

    es.indices.put_alias(index=index_name, name=terms_alias)


def index_exists(es, index_name: str):
    """Does index exist?

    Args:
        index_name:  index to check for existence
    """
    return es.indices.exists(index=index_name)


def delete_index(es, index_name: str):
    """Delete the terms index"""

    if not index_name:
        log.warn("No index name given to delete")
        return None

    result = es.indices.delete(index=index_name)
    return result


def create_terms_index(es, index_name: str):
    """Create terms index"""

    with open(mappings_terms_fn, "r") as f:
        mappings_terms = yaml.load(f, Loader=yaml.SafeLoader)

    try:
        es.indices.create(index=index_name, body=mappings_terms)

    except Exception as e:
        log.error(f"Could not create elasticsearch terms index: {e}")


def delete_terms_indexes(es, index_name: str = "terms_*"):
    """Delete all terms indexes"""

    try:
        es.indices.delete(index=index_name)
    except Exception as e:
        log.error(f"Could not delete all terms indices: {e}")


def get_client():
    """Get elasticsearch client

    Returns:
        es: Elasticsearch client handle
    """

    es = Elasticsearch([config["bel_api"]["servers"]["elasticsearch"]], send_get_body_as="POST")

    return es


def bulk_load_docs(es, docs):
    """Bulk load docs

    Args:
        es: elasticsearch handle
        docs: Iterator of doc objects - includes index_name
    """

    chunk_size = 200

    try:
        results = elasticsearch.helpers.bulk(es, docs, chunk_size=chunk_size)
        log.debug(f"Elasticsearch documents loaded: {results[0]}")

        # elasticsearch.helpers.parallel_bulk(es, terms, chunk_size=chunk_size, thread_count=4)
        if len(results[1]) > 0:
            log.error("Bulk load errors {}".format(results))
    except elasticsearch.ElasticsearchException as e:
        log.error("Indexing error: {}\n".format(e))
