#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Usage:  program.py <customer>

"""

from typing import Mapping, Any, List
import copy
import itertools
import yaml
import os

import bel.lang.bel
import bel.lang.bel_specification
import bel.lang.bel_utils as bel_utils
import bel.db.arangodb as arangodb
import bel.utils as utils
import bel.nanopub.files as files

import logging
log = logging.getLogger(__name__)


def create_edges(nanopub: Mapping[str, Any], endpoint: str, namespace_targets: Mapping[str, List[str]], rules: List[str] = [], orthologize_target: str = None) -> List[Mapping[str, Any]]:
    """Create edges for Nanopub

    Args:
        nanopub (Mapping[str, Any]): nanopub in nanopub_bel schema format
        endpoint (str): BEL.bio API endpoint to use
        rules (List[str]): which computed edge rules to process, default is all,
           look at BEL Specification yaml file for computed edge signature keys,
           e.g. degradation, if any rule in list is 'skip', then skip computing edges
           just return primary_edge
        namespace_targets (Mapping[str, List[str]]): what namespaces to canonicalize
        orthologize_target (str): species to convert BEL into, e.g. TAX:10090 for mouse, default option does not orthologize

    Returns:
        Tuple[List[Mapping[str, Any]], List[Tuple[str, List[str]]]]: (edge list, validation messages) - edge list with edge attributes (e.g. context) and parse validation messages
    """

    # Extract BEL Version
    if nanopub['nanopub']['type']['name'].upper() == "BEL":
        bel_version = nanopub['nanopub']['type']['version']
        versions = bel.lang.bel_specification.get_bel_versions()
        if bel_version not in versions:
            log.error(f'Do not know this BEL Version: {bel_version}, these are the ones I can process: {versions}')
            return []
    else:
        log.error(f"Not a BEL Nanopub according to nanopub.type.name: {nanopub['nanopub']['type']['name']}")
        return []

    computed_edges = []

    edges = []
    bo = bel.lang.bel.BEL(bel_version, endpoint)
    for edge in nanopub['nanopub']['edges']:
        if edge['relation']:
            bel_statement = f"{edge['subject']} {edge['relation']} {edge['object']}"
        else:
            bel_statement = edge['subject']

        computed_edges = []
        nodes = {}  # list of BEL nodes without componentOf only nodes
        if orthologize_target:
            bo.parse(bel_statement).orthologize(orthologize_target).canonicalize(namespace_targets=namespace_targets)
        else:
            bo.parse(bel_statement).canonicalize(namespace_targets=namespace_targets)

        if not rules or 'skip' not in rules:
            computed_edges.extend(bo.compute_edges(rules=rules))

        if not bo.parse_valid:
            log.error(f'Invalid BEL Statement: {bo.validation_messages}')
            return ([], bo.validation_messages)

        primary_edge = bo.ast.to_components(fmt="medium")
        # Add primary edge to edges
        subject_lbl = bel_utils.convert_namespaces_str(primary_edge['subject'], decanonicalize=True)
        object_lbl = bel_utils.convert_namespaces_str(primary_edge.get('object', ''), decanonicalize=True)
        edge = {
            "edge": {
                "subject": {
                    "name": primary_edge['subject'],
                    "label": subject_lbl
                },
                "relation": {
                    "name": primary_edge.get('relation', None),
                    "subject_lbl": subject_lbl,
                    "relation_lbl": primary_edge.get('relation', None),
                    "object_lbl": object_lbl,
                },
                'object': {
                    "name": primary_edge.get('object', None),
                    "label": object_lbl
                }
            }
        }
        # Collect bel nodes without componentOf only nodes
        nodes[primary_edge['subject']] = 1
        if primary_edge.get('object', None):
            nodes[primary_edge['object']] = 1

        # Don't add context to primary edge unless it has a relation and object
        context = copy.deepcopy(nanopub['nanopub']['context'])
        if orthologize_target:
            context = orthologize_context(orthologize_target, context)

        if primary_edge.get('relation', None) is not None:
            edge['edge']['relation']['context'] = context
            edge['edge']['relation']['metadata'] = {
                'nanopub_id': nanopub['nanopub'].get('id', None),
                'primary': True,
                'computed': False,
            }

        edges.append(copy.deepcopy(edge))

        for computed_edge in computed_edges:
            if computed_edge['relation'] == 'componentOf':
                continue

            subject_lbl = bel_utils.convert_namespaces_str(computed_edge['subject'], decanonicalize=True)
            object_lbl = bel_utils.convert_namespaces_str(computed_edge['object'], decanonicalize=True)
            edge = {
                "edge": {
                    "subject": {
                        "name": computed_edge['subject'],
                        "label": subject_lbl
                    },
                    "relation": {
                        "name": computed_edge['relation'],
                        "subject_lbl": subject_lbl,
                        "relation_lbl": computed_edge.get('relation', None),
                        "object_lbl": object_lbl,
                    },
                    'object': {
                        "name": computed_edge['object'],
                        "label": object_lbl
                    }
                }
            }
            # Collect bel nodes without componentOf only nodes
            nodes[computed_edge['subject']] = 1
            if computed_edge.get('object', None):
                nodes[computed_edge.get('object')] = 1

            edge['edge']['relation']['metadata'] = {
                "computed": True,
                "primary": False,
            }

            edges.append(copy.deepcopy(edge))

        for computed_edge in computed_edges:
            if computed_edge['relation'] != 'componentOf':
                continue

            subject_lbl = bel_utils.convert_namespaces_str(computed_edge['subject'], decanonicalize=True)
            object_lbl = bel_utils.convert_namespaces_str(computed_edge['object'], decanonicalize=True)
            edge = {
                "edge": {
                    "subject": {
                        "name": computed_edge['subject'],
                        "label": subject_lbl
                    },
                    "relation": {
                        "name": computed_edge['relation'],
                        "subject_lbl": subject_lbl,
                        "relation_lbl": computed_edge.get('relation', None),
                        "object_lbl": object_lbl,
                    },
                    'object': {
                        "name": computed_edge['object'],
                        "label": object_lbl
                    }
                }
            }
            # Flag actual BEL nodes as opposed to componentOf only nodes
            if nodes.get(computed_edge['object'], False):
                edge['edge']['object']['bel_node'] = True

            edges.append(copy.deepcopy(edge))

    return (edges, bo.validation_messages)


def orthologize_context(orthologize_target: str, context: Mapping[str, Any]) -> Mapping[str, Any]:
    """Orthologize context

    Replace Species context with new orthologize target and add a context type of OrthologizedTo
    """
    pass


def edge_iterator(edges=[], edges_fn=None):
    """Yield documents from edge for loading into ArangoDB

    """

    node_name = 'nodes'  # node collection name
    comp_node_name = 'comp_nodes'  # node collection name
    edges_name = 'edges'  # edge collection name
    comp_edges_name = 'comp_edges'  # edge collection name

    # TODO - figure out why nodes/79657358527909756137033889823637958754 isn't showing up in edges collection
    #   it's in the comp_edges collection and is a bel_node
    for edge in itertools.chain(edges, files.read_edges(edges_fn)):
        # import json
        # print('DumpVar:\n', json.dumps(edge, indent=4))
        subject = copy.deepcopy(edge['edge']['subject'])
        subject_id = str(utils._create_hash_from_doc(subject))
        subject['_key'] = subject_id
        object_ = copy.deepcopy(edge['edge']['object'])
        object_id = str(utils._create_hash_from_doc(object_))
        object_['_key'] = object_id
        relation = copy.deepcopy(edge['edge']['relation'])

        # If componentOf edge - put it in component edge collection
        #    if the componentOf object node is a BEL node - add it to
        #    regular node collection otherwise to the component node collection
        #    subject nodes for componentOf are always component nodes
        if relation['name'] == 'componentOf':
            subject_collection_name = comp_node_name
            edges_collection_name = comp_edges_name

            relation['_from'] = f'{comp_node_name}/{subject_id}'
            if object_.get('bel_node', False):
                object_collection_name = node_name
                relation['_to'] = f'{node_name}/{subject_id}'
            else:
                relation['_from'] = f'{comp_node_name}/{subject_id}'
        else:
            subject_collection_name = node_name
            edges_collection_name = edges_name
            object_collection_name = node_name

        relation['_from'] = f'{subject_collection_name}/{subject_id}'
        relation['_to'] = f'{object_collection_name}/{object_id}'
        relation_id = str(utils._create_hash_from_doc(relation))
        relation['_key'] = relation_id

        if edge.get('nanopub_id', None):
            if 'metadata' not in relation:
                relation['metadata'] = {}
            relation['metadata']['nanopub_id'] = edge['nanopub_id']

        yield(subject_collection_name, subject_id, subject)
        yield(object_collection_name, object_id, object_)
        yield(edges_collection_name, relation_id, relation)


def load_edges_into_db(db, edges=[], edges_fn=None, username: str = None, password: str = None):
    """Load edges into ArangoDB


    """

    doc_iterator = edge_iterator(edges=edges, edges_fn=edges_fn)

    arangodb.batch_load_docs(db, doc_iterator)


def main():

    (arango_client, edgestore_db) = arangodb.get_client()
    arangodb.delete_edgestore(arango_client)
    (arango_client, edgestore_db) = arangodb.get_client()
    load_edges_into_db(edgestore_db, edges_fn="edges.jsonl.gz")


if __name__ == '__main__':
    # Setup logging
    import logging.config
    module_fn = os.path.basename(__file__)
    module_fn = module_fn.replace('.py', '')

    logging_conf_fn = "./logging-conf.yaml"

    with open(logging_conf_fn, mode='r') as f:
        logging.config.dictConfig(yaml.load(f))
        log = logging.getLogger(f'{module_fn}')

    main()

