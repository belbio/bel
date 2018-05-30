import timy
import json
import gzip

from arango import ArangoError

from typing import IO

import bel.utils
import bel.db.arangodb as arangodb

from bel.Config import config

from structlog import get_logger
log = get_logger()


def load_orthologs(fo: IO, metadata: dict):
    """Load orthologs into ArangoDB

    Args:
        fo: file obj - orthologs file
        metadata: dict containing the metadata for orthologs
    """

    version = metadata['metadata']['version']

    # LOAD ORTHOLOGS INTO ArangoDB
    with timy.Timer('Load Orthologs') as timer:
        arango_client = arangodb.get_client()
        belns_db = arangodb.get_belns_handle(arango_client)
        arangodb.batch_load_docs(belns_db, orthologs_iterator(fo, version))

        # TODO - delete old orthologs based on source and version

        log.info('Load orthologs', elapsed=timer.elapsed, source=metadata['metadata']['source'])

    # Add metadata to resource metadata collection
    metadata['_key'] = f"Orthologs_{metadata['metadata']['source']}"
    try:
        belns_db.collection(arangodb.belns_metadata_name).insert(metadata)
    except ArangoError as ae:
        belns_db.collection(arangodb.belns_metadata_name).replace(metadata)


def orthologs_iterator(fo, version):
    """Ortholog node and edge iterator"""

    species_list = config['bel_resources'].get('species_list', [])

    fo.seek(0)
    with gzip.open(fo, 'rt') as f:
        for line in f:
            edge = json.loads(line)
            if 'metadata' in edge:
                source = edge['metadata']['source']
                continue

            if 'ortholog' in edge:
                edge = edge['ortholog']
                subj_tax_id = edge['subject']['tax_id']
                obj_tax_id = edge['object']['tax_id']

                # Skip if species not listed in species_list
                if species_list and subj_tax_id and subj_tax_id not in species_list:
                    continue
                if species_list and obj_tax_id and obj_tax_id not in species_list:
                    continue

                # Converted to ArangoDB legal chars for _key
                subj_key = arangodb.arango_id_to_key(edge['subject']['id'])
                subj_id = edge['subject']['id']

                # Converted to ArangoDB legal chars for _key
                obj_key = arangodb.arango_id_to_key(edge['object']['id'])
                obj_id = edge['object']['id']

                # Subject node
                yield (arangodb.ortholog_nodes_name, {'_key': subj_key, 'name': subj_id, 'tax_id': edge['subject']['tax_id'], 'source': source, 'version': version})
                # Object node
                yield (arangodb.ortholog_nodes_name, {'_key': obj_key, 'name': obj_id, 'tax_id': edge['object']['tax_id'], 'source': source, 'version': version})

                arango_edge = {
                    '_from': f"{arangodb.ortholog_nodes_name}/{subj_key}",
                    '_to': f"{arangodb.ortholog_nodes_name}/{obj_key}",
                    '_key': bel.utils._create_hash(f'{subj_key}>>{obj_key}'),
                    'type': 'ortholog_to',
                    'source': source,
                    'version': version,
                }

                yield (arangodb.ortholog_edges_name, arango_edge)

