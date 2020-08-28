# Standard Library
import os

# Third Party Imports
import elasticsearch.helpers
import yaml
from elasticsearch import Elasticsearch

# Local Imports
import bel.core.settings as settings
from loguru import logger


cur_dir_name = os.path.dirname(os.path.realpath(__file__))
mappings_terms_fn = f"{cur_dir_name}/es_mappings_terms.yml"

es = Elasticsearch([settings.ELASTICSEARCH_URL], send_get_body_as="POST")
logger.info(f"Elasticsearch URL: {settings.ELASTICSEARCH_URL}")

def get_all_index_names():
    """Get all index names"""

    indices = es.indices.get_alias()

    return indices


def add_index_alias(index_name, alias_name):
    """Add index alias to index_name"""

    es.indices.put_alias(index=index_name, name=alias_name)


def index_exists(index_name: str):
    """Does index exist?

    Args:
        index_name:  index to check for existence
    """
    return es.indices.exists(index=index_name)


def delete_index(index_name: str):
    """Delete the terms index"""

    if not index_name:
        logger.warn("No index name given to delete")
        return None

    result = es.indices.delete(index=index_name)
    return result


def create_terms_index(index_name: str):
    """Create terms index"""

    with open(mappings_terms_fn, "r") as f:
        mappings_terms = yaml.load(f, Loader=yaml.SafeLoader)

    try:
        es.indices.create(index=index_name, body=mappings_terms)

    except Exception as e:
        logger.error(f"Could not create elasticsearch terms index: {e}")


def delete_terms_indexes(index_name: str = f"{settings.TERMS_INDEX}_*"):
    """Delete all terms indexes"""

    try:
        es.indices.delete(index=index_name)
    except Exception as e:
        logger.error(f"Could not delete all terms indices: {e}")


def bulk_load_docs(docs):
    """Bulk load docs

    Args:
        es: elasticsearch handle
        docs: Iterator of doc objects - includes index_name
    """

    chunk_size = 200

    try:
        results = elasticsearch.helpers.bulk(es, docs, chunk_size=chunk_size)
        logger.debug(f"Elasticsearch documents loaded: {results[0]}")

        # elasticsearch.helpers.parallel_bulk(terms, chunk_size=chunk_size, thread_count=4)
        if len(results[1]) > 0:
            logger.error("Bulk load errors {}".format(results))
    except elasticsearch.ElasticsearchException as e:
        logger.error("Indexing error: {}\n".format(e))
