import os
import yaml
from elasticsearch import Elasticsearch
import elasticsearch.helpers

from bel.Config import config

import logging
log = logging.getLogger(__name__)

cur_dir_name = os.path.dirname(os.path.realpath(__file__))
mapping_terms_fn = f'{cur_dir_name}/es_mapping_terms.yml'

terms_idx_name = 'terms_blue'
terms_alias = 'terms'


# TODO - start using index aliases for managing updating Elasticsearch
# today_str = datetime.date.today().strftime("%Y-%m-%d")
# index_name = 'terms_' + today_str


def set_terms_alias(es):
    """Add terms alias for the terms_blue index"""
    if es.indices.exists_alias(terms_idx_name, terms_alias):
        es.indices.delete_alias(terms_idx_name, terms_alias)
    es.indices.put_alias(terms_idx_name, terms_alias)


def index_exists(es, index):
    """
    Input: index -- index to check for existence

    """
    return es.indices.exists(index=index)


def delete_index(es, index_name):
    """Delete the terms index"""

    if not index_name:
        log.warn('No index name given to delete')
        return None

    result = es.indices.delete(index=index_name)
    return result


def create_terms_index(es, index_name):
    """Create terms index"""

    with open(mapping_terms_fn, 'r') as f:
        mapping_terms = yaml.load(f)

    try:
        es.indices.create(index=index_name, body=mapping_terms)

    except Exception as e:
        log.error(f'Could not create elasticsearch terms index: {e}')

    set_terms_alias(es)


def get_client(delete: bool = False, index_name: str = terms_idx_name):
    """Get elasticsearch client

    Will create terms index if not available using mapping in
    es_mapping_terms.yml file

    Args:
        delete (bool): delete index if exists
        index_name (str): index to be created or defaults to terms_idx_name
    Returns:
        es: Elasticsearch client handle
    """

    es = Elasticsearch([config['bel_api']['servers']['elasticsearch']], send_get_body_as='POST')
    if delete:
        if index_exists(es, index_name):
            delete_index(es, index_name)

    if not index_exists(es, index_name):
        create_terms_index(es, index_name)

    return es


def bulk_load_terms(es, terms):
    """Bulk load terms

    Args:
        es: elasticsearch handle
        terms: Iterator of term objects - includes index_name
    """

    chunk_size = 200

    try:
        results = elasticsearch.helpers.bulk(es, terms, chunk_size=chunk_size)
        log.info(f'Elasticsearch documents loaded: {results[0]}')

        # elasticsearch.helpers.parallel_bulk(es, terms, chunk_size=chunk_size, thread_count=4)
        if len(results[1]) > 0:
            log.error('Bulk load errors {}'.format(results))
    except elasticsearch.ElasticsearchException as e:
        log.error('Indexing error: {}\n'.format(e))

