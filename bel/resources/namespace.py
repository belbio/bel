import timy
import json
import gzip
import copy

from arango import ArangoError

from typing import IO

import bel.utils
import bel.db.elasticsearch as elasticsearch
import bel.db.arangodb as arangodb

from bel.Config import config

# import structlog
# import logging
# log = logging.getLogger(__name__)

from structlog import get_logger
log = get_logger()

terms_alias = 'terms'


def load_terms(fo: IO, metadata: dict):
    """Load terms into Elasticsearch and ArangoDB

    Args:
        fo: file obj - terminology file
        metadata: dict containing the metadata for terminology
    """

    version = metadata['metadata']['version']

    # LOAD TERMS INTO Elasticsearch
    with timy.Timer('Load Terms') as timer:
        es = bel.db.elasticsearch.get_client()

        es_version = version.replace('T', '').replace('-', '').replace(':', '')
        index_prefix = metadata['metadata']['namespace'].lower()
        index_name = f"terms_{index_prefix}_{es_version}"

        # Create index with mapping
        if not elasticsearch.index_exists(es, index_name):
            elasticsearch.create_terms_index(es, index_name)

        terms_iterator = terms_iterator_for_elasticsearch(fo, index_name)
        elasticsearch.bulk_load_docs(es, terms_iterator)

        # Remove old namespace index
        index_names = elasticsearch.get_all_index_names(es)
        for name in index_names:
            if name != index_name and index_prefix in name:
                elasticsearch.delete_index(es, name)

        # Add terms_alias to this index
        elasticsearch.add_index_alias(es, index_name, terms_alias)

        log.info('Load namespace terms', elapsed=timer.elapsed, namespace=metadata['metadata']['namespace'])

    # LOAD EQUIVALENCES INTO ArangoDB
    with timy.Timer('Load Term Equivalences') as timer:
        arango_client = arangodb.get_client()
        belns_db = arangodb.get_belns_handle(arango_client)
        arangodb.batch_load_docs(belns_db, terms_iterator_for_arangodb(fo, version))

        # TODO - delete old equivalences based on namespace and version
        # delete resources matching namespace and NOT current version

        log.info('Load namespace equivalences', elapsed=timer.elapsed, namespace=metadata['metadata']['namespace'])

    # Add metadata to resource metadata collection
    metadata['_key'] = f"Namespace_{metadata['metadata']['namespace']}"
    try:
        belns_db.collection(arangodb.belns_metadata_name).insert(metadata)
    except ArangoError as ae:
        belns_db.collection(arangodb.belns_metadata_name).replace(metadata)


def terms_iterator_for_arangodb(fo, version):

    species_list = config['bel_resources'].get('species_list', [])

    fo.seek(0)
    with gzip.open(fo, 'rt') as f:
        for line in f:
            term = json.loads(line)
            # skip if not term record (e.g. is a metadata record)
            if 'term' not in term:
                continue
            term = term['term']

            species_id = term.get('species_id', None)
            # Skip if species not listed in species_list
            if species_list and species_id and species_id not in species_list:
                continue

            if 'equivalences' in term:
                source = term['namespace']
                term_id = term['id']
                term_key = arangodb.arango_id_to_key(term_id)

                (ns, val) = term_id.split(':', maxsplit=1)

                yield (arangodb.equiv_nodes_name, {'_key': term_key, 'name': term_id, 'namespace': ns, 'source': source, 'version': version})

                for eqv in term['equivalences']:
                    (ns, val) = eqv.split(':', maxsplit=1)
                    eqv_key = arangodb.arango_id_to_key(eqv)

                    yield (arangodb.equiv_nodes_name, {'_key': eqv_key, 'name': eqv, 'namespace': ns, 'source': source, 'version': version})

                    arango_edge = {
                        '_from': f"{arangodb.equiv_nodes_name}/{term_key}",
                        '_to': f"{arangodb.equiv_nodes_name}/{eqv_key}",
                        '_key': bel.utils._create_hash(f'{term_key}>>{eqv_key}'),
                        'type': 'equivalent_to',
                        'source': source,
                        'version': version,
                    }
                    yield (arangodb.equiv_edges_name, arango_edge)


def terms_iterator_for_elasticsearch(fo: IO, index_name: str):
    """Add index_name to term documents for bulk load"""

    species_list = config['bel_resources'].get('species_list', [])

    fo.seek(0)  # Seek back to beginning of file
    with gzip.open(fo, 'rt') as f:
        for line in f:
            term = json.loads(line)
            # skip if not term record (e.g. is a metadata record)
            if 'term' not in term:
                continue
            term = term['term']

            # Filter species if enabled in config
            species_id = term.get('species_id', None)
            if species_list and species_id and species_id not in species_list:
                continue

            yield {
                '_op_type': 'index',
                '_index': index_name,
                '_type': 'term',
                '_id': term['id'],
                '_source': copy.deepcopy(term)
            }


def lowercase_term_id(term_id: str) -> str:
    """Lowercase the term value (not the namespace prefix)

    Args:
        term_id (str): term identifier with namespace prefix, e.g. MESH:Atherosclerosis

    Returns:
        str: lowercased, e.g. MESH:atherosclerosis
    """
    try:
        (ns, val) = term_id.split(':', maxsplit=1)
        term_id = f'{ns}:{val.lower()}'
        return term_id
    except Exception:
        return term_id
