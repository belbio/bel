#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Usage:  program.py <customer>

"""

from typing import Mapping, Any, List, MutableSequence
import copy
import itertools
import os
import json
import datetime
import urllib

import bel.lang.belobj
import bel.lang.bel_specification
import bel.lang.bel_utils as bel_utils
import bel.db.arangodb as arangodb
import bel.utils as utils
import bel.nanopub.files as files
import bel.nanopub.nanopubstore as nanopubstore

from bel.Config import config

import structlog
log = structlog.getLogger(__name__)

Edges = MutableSequence[Mapping[str, Any]]

arango_client = arangodb.get_client()
edgestore_db = arangodb.get_edgestore_handle(arango_client)


def save_nanopub_to_edgestore(nanopub_url: str, nanopub: dict = {}, rules: List[str] = [], orthologize_targets: list = []):
    """Save nanopub created edges into edgestore"""

    try:
        results = process_nanopub(nanopub_url=nanopub_url, nanopub=nanopub, rules=rules, orthologize_targets=orthologize_targets)

        # start_time = datetime.datetime.now()
        # arango_client = arangodb.get_client()
        # edgestore_db = arangodb.get_edgestore_handle(arango_client)
        # conn_time = utils.timespan(start_time)
        # log.info('Time to get db connection', delta_get_db_conn=conn_time)
        if results['success']:
            load_edges_into_db(edgestore_db, results['edges'])
            return {"msg": f"Loaded {len(results['edges'])} edges into edgestore", "success": True}
        else:
            return {"msg": "Could not process nanopub into edge", "success": False}

    except Exception as e:
        return {"msg": f"Could not process nanopub: {nanopub_url}", "success": False, "error": e}


def process_nanopub(nanopub_url: str = '', nanopub: dict = {}, rules: List[str] = [], orthologize_targets: list = []):
    """Process nanopub into edges and load into EdgeStore

    """

    if not nanopub_url and not nanopub:
        return {'edges': [], "success": False}
    elif nanopub_url and not nanopub:
        nanopub = nanopubstore.get_nanopub(nanopub_url)
        nanopub['source_url'] = nanopub_url

    try:
        start_time = datetime.datetime.now()

        if orthologize_targets == []:
            if config['bel_api'].get('edges', None):
                if config['bel_api']['edges'].get('orthologize_targets', None):
                    orthologize_targets = config['bel_api']['edges']['orthologize_targets']

        api_url = config['bel_api']['servers']['api_url']

        citation_string = normalize_nanopub_citation(nanopub)

        np_time = datetime.datetime.now()
        delta_get_np = np_time - start_time

        # Add unorthologized edges
        edges = create_edges(nanopub, api_url, citation_string)

        edges_time = datetime.datetime.now()
        delta_get_edges = edges_time - np_time

        # Add orthologized edges
        for orthologize_target in orthologize_targets:
            edges.extend(create_edges(nanopub, api_url, citation_string, orthologize_target=orthologize_target))

        log.info('Timings', delta_get_np=f'{delta_get_np.total_seconds() * 1000}ms', delta_get_edges=f'{delta_get_edges.total_seconds() * 1000}ms')

        return {"edges": edges, "nanopub_url": nanopub_url, "success": True}

    except Exception as e:
        log.error(f'Failed converting nanopub into edges NanopubUrl: {nanopub["source_url"]}', exc_info=True)
        return {"edges": edges, "nanopub_url": nanopub_url, "success": False}


def create_edges(nanopub: Mapping[str, Any], api_url: str, citation: str, rules: List[str] = [], orthologize_target: str = []) -> Edges:
    """Create edges from assertions

    Args:
        nanopub (Mapping[str, Any]): nanopub in nanopub_bel schema format
        api_url (str): BEL.bio API endpoint to use
        citation (str): citation string normalized from Nanopub citation object
        rules (List[str]): which computed edge rules to process, default is all,
           look at BEL Specification yaml file for computed edge signature keys,
           e.g. degradation, if any rule in list is 'skip', then skip computing edges
           just return primary_edge
        orthologize_target: species to convert BEL into, e.g. TAX:10090 for mouse, default option does not orthologize

    Returns:
        Tuple[List[Mapping[str, Any]], List[Tuple[str, List[str]]]]: (edge list, validation messages) - edge list with edge attributes (e.g. context) and parse validation messages

    Edge object:
        {
            "edge": {
                "subject": {
                    "name": subj_canon,
                    "name_lc": subj_canon.lower(),
                    "label": subj_lbl,
                    "label_lc": subj_lbl.lower(),
                    "components": subj_components,
                },
                "relation": {  # relation _key is based on a hash
                    "relation": edge_ast.bel_relation,
                    "edge_hash": edge_hash,
                    "edge_dt": edge_dt,
                    "nanopub_dt": gd:updateTS,
                    "nanopub_url": nanopub_url,
                    "nanopub_id": nanopub_id,
                    "citation": citation,
                    "subject_canon": subj_canon,
                    "subject": subj_lbl,
                    "object_canon": obj_canon,
                    "object": obj_lbl,
                    "annotations": nanopub['annotations'],
                    "metadata": nanopub['metadata'],
                    "public_flag": nanopub['isPublished'],
                    "edge_types": edge_types,
                },
                'object': {
                    "name": obj_canon,
                    "name_lc": obj_canon.lower(),
                    "label": obj_lbl,
                    "label_lc": obj_lbl.lower(),
                    "components": obj_components,
                }
            }
        }

    """

    edge_dt = utils.dt_utc_formatted()  # don't want this in relation_id

    # Extract BEL Version and make sure we can process this
    if nanopub['nanopub']['type']['name'].upper() == "BEL":
        bel_version = nanopub['nanopub']['type']['version']
        versions = bel.lang.bel_specification.get_bel_versions()
        if bel_version not in versions:
            log.error(f'Do not know this BEL Version: {bel_version}, these are the ones I can process: {versions.keys()}')
            return []
    else:
        log.error(f"Not a BEL Nanopub according to nanopub.type.name: {nanopub['nanopub']['type']['name']}")
        return []

    annotations = copy.deepcopy(nanopub['nanopub']['annotations'])
    metadata = copy.deepcopy(nanopub['nanopub']['metadata'])
    metadata.pop('gd:abstract', None)

    if orthologize_target:
        annotations = orthologize_context(orthologize_target, annotations)

    edges = []
    bo = bel.lang.belobj.BEL(bel_version, api_url)

    for assertion in nanopub['nanopub']['assertions']:

        if not assertion['relation']:
            continue  # Skip any subject only statements

        edge = {
            'edge': {
                'subject': {},
                'relation': {
                    'relation': assertion['relation'],
                    'edge_dt': edge_dt,
                    'nanopub_url': nanopub['source_url'],
                    'nanopub_id': os.path.basename(urllib.parse.urlparse(nanopub['source_url']).path),
                    'citation': citation,
                    'annotations': copy.deepcopy(annotations),
                    'metadata': copy.deepcopy(metadata),
                    'public_flag': nanopub['isPublished'],
                },
                'object': {},
            }
        }

        if assertion['relation']:
            bel_statement = f"{assertion['subject']} {assertion['relation']} {assertion['object']}"
        else:
            bel_statement = assertion['subject']

        bo.parse(bel_statement)
        if not bo.parse_valid:  # Continue processing BEL Nanopub assertions
            log.error(f'Invalid BEL Statement: {bo.validation_messages}')
            continue

        if 'backbone' in nanopub['source_url']:
            edge['edge']['relation']['edge_types'] = ['backbone']
        else:
            edge['edge']['relation']['edge_types'] = ['primary']

        # Orthologize #####################################################
        if orthologize_target:
            orig_bel_str = bo.to_string()
            bo.orthologize(orthologize_target)

            if bo.to_string() == orig_bel_str:
                log.info(f'Cannot orthologize BEL stmt to {orthologize_target}')
                continue

            edge['edge']['relation']['edge_types'].append('orthologized')

        # Add BEL causal edge type
        if bo.ast.bel_relation and 'causal' in bo.ast.spec['relations']['info'][bo.ast.bel_relation]['categories']:
            edge['edge']['relation']['edge_types'].append('causal')

        # Primary Edge
        process_belobj_into_triples(bo, edge)

        log.info(f'Edge: {edge}')
        edge_hash = utils._create_hash(f'{edge["edge"]["subject"]["name"]} {edge["edge"]["relation"]["relation"]} {edge["edge"]["object"]["name"]}')
        edge['edge']['relation']['edge_hash'] = edge_hash
        edges.append(edge)

        # Computed edges ##################################################
        computed_edges_ast = bo.compute_edges(rules=rules, ast_result=True)

        if orthologize_target:
            edge_types = ['computed', 'orthologized']
        else:
            edge_types = ['computed']

        for edge_ast in computed_edges_ast:
            edge = {
                'edge': {
                    'subject': {},
                    'relation': {
                        'relation': assertion['relation'],
                        'edge_dt': edge_dt,
                        'public_flag': True,
                        'edge_types': edge_types,
                    },
                    'object': {},
                }
            }

            bo.ast = edge_ast
            process_belobj_into_triples(bo, edge)

            edge_hash = utils._create_hash(f'{edge["edge"]["subject"]["name"]} {edge["edge"]["relation"]["relation"]} {edge["edge"]["object"]["name"]}')
            edge['edge']['relation']['edge_hash'] = edge_hash
            edges.append(edge)

    return edges


def process_belobj_into_triples(bo, edge):
    """Create triples (canonicalized and decanonicalized)

    Create SRO strings and components canonicalized and decanonicalized
    as well as the Subject and Object triples
    """

    bo.canonicalize()
    sro = bo.to_triple()
    edge['edge']['subject']['name'] = sro['subject']
    edge['edge']['subject']['name_lc'] = sro['subject'].lower()
    edge['edge']['relation']['subject_canon'] = sro['subject']

    edge['edge']['relation']['relation'] = sro['relation']
    edge['edge']['object']['name'] = sro['object']
    edge['edge']['object']['name_lc'] = sro['object'].lower()
    edge['edge']['relation']['object_canon'] = sro['object']

    edge['edge']['subject']['components'] = bo.ast.bel_subject.subcomponents(subcomponents=[])

    if bo.ast.bel_object.__class__.__name__ == 'BELAst':  # Nested BEL Assertion
        obj_components = bo.ast.bel_object.bel_subject.subcomponents(subcomponents=[])
        obj_components = bo.ast.bel_object.bel_object.subcomponents(subcomponents=obj_components)
    else:  # Normal BEL Assertion
        obj_components = bo.ast.bel_object.subcomponents(subcomponents=[])

    edge['edge']['object']['components'] = obj_components

    bo.decanonicalize()
    sro = bo.to_triple()
    edge['edge']['subject']['label'] = sro['subject']
    edge['edge']['subject']['label_lc'] = sro['subject'].lower()
    edge['edge']['relation']['subject'] = sro['subject']
    edge['edge']['object']['label'] = sro['object']
    edge['edge']['object']['label_lc'] = sro['object'].lower()
    edge['edge']['relation']['object'] = sro['object']


def orthologize_context(orthologize_target: str, annotations: Mapping[str, Any]) -> Mapping[str, Any]:
    """Orthologize context

    Replace Species context with new orthologize target and add a annotation type of OrthologizedFrom
    """

    url = f'{config["bel_api"]["servers"]["api_url"]}/terms/{orthologize_target}'
    r = utils.get_url(url)
    species_label = r.json().get("label", "unlabeled")

    for idx, annotation in enumerate(annotations):
        if annotation['type'] == 'Species':
            annotations[idx]['type'] = 'OrthologizedFrom'

    annotations.append({'type': 'Species', 'id': orthologize_target, 'label': species_label})

    return annotations


def edge_iterator(edges=[], edges_fn=None):
    """Yield documents from edge for loading into ArangoDB"""

    for edge in itertools.chain(edges, files.read_edges(edges_fn)):
        subj = copy.deepcopy(edge['edge']['subject'])
        subj_id = str(utils._create_hash_from_doc(subj))
        subj['_key'] = subj_id
        obj = copy.deepcopy(edge['edge']['object'])
        obj_id = str(utils._create_hash_from_doc(obj))
        obj['_key'] = obj_id
        relation = copy.deepcopy(edge['edge']['relation'])

        relation['_from'] = f'nodes/{subj_id}'
        relation['_to'] = f'nodes/{obj_id}'

        # Create edge _key
        relation_hash = copy.deepcopy(relation)
        relation_hash.pop('edge_dt', None)
        relation_hash.pop('edge_hash', None)
        relation_hash.pop('nanopub_dt', None)
        relation_hash.pop('nanopub_url', None)
        relation_hash.pop('subject_canon', None)
        relation_hash.pop('object_canon', None)
        relation_hash.pop('metadata', None)

        relation_id = str(utils._create_hash_from_doc(relation_hash))
        relation['_key'] = relation_id

        if edge.get('nanopub_id', None):
            if 'metadata' not in relation:
                relation['metadata'] = {}
            relation['metadata']['nanopub_id'] = edge['nanopub_id']

        yield('nodes', subj)
        yield('nodes', obj)
        yield('edges', relation)


def load_edges_into_db(db, edges=[], edges_fn=None, username: str = None, password: str = None):
    """Load edges into ArangoDB"""
    doc_iterator = edge_iterator(edges=edges, edges_fn=edges_fn)

    arangodb.batch_load_docs(db, doc_iterator)


def normalize_nanopub_citation(nanopub):

    citation_string = ''
    if 'database' in nanopub['nanopub']['citation']:
        if nanopub['nanopub']['citation']['database']['name'].lower() == 'pubmed':
            citation_string = f"PMID:{nanopub['nanopub']['citation']['database']['id']}"
        else:
            citation_string = f"{nanopub['nanopub']['citation']['database']['name']}:{nanopub['nanopub']['citation']['database']['id']}"
    elif 'reference' in nanopub['nanopub']['citation'] and isinstance(nanopub['nanopub']['citation']['reference'], str):
        citation_string = nanopub['nanopub']['citation']['reference']
    elif 'uri' in nanopub['nanopub']['citation']:
        citation_string = nanopub['nanopub']['citation']['uri']

    return citation_string


def deleted_nanopubs(deleted_nanopub_urls):
    """Remove edges for deleted nanopubs"""

    aql = f"""
    FOR doc in edges
        FILTER doc.relation.nanopub_url IN {deleted_nanopub_urls}
        REMOVE doc IN edges
    """

    edgestore_db.aql.execute(aql)


def main():

    deleted_nanopubs(['http://hi.there', 'http://me.back'])
    quit()
    (arango_client, edgestore_db) = arangodb.get_client()
    arangodb.delete_edgestore(arango_client)
    (arango_client, edgestore_db) = arangodb.get_client()
    load_edges_into_db(edgestore_db, edges_fn="edges.jsonl.gz")


if __name__ == '__main__':
    # Setup logging
    import logging.config
    module_fn = os.path.basename(__file__)
    module_fn = module_fn.replace('.py', '')

    if config.get('logging', False):
        logging.config.dictConfig(config.get('logging'))

    log = logging.getLogger(f'{module_fn}')

    main()



# # Here for reference - not being used
# def add_edge_old(nanopub, edges: Edges, edge_ast, nanopub_url: str, edge_types: List[str], citation: str, annotations: List[any]):
#     """Add edge to edges

#     Args:
#         edges: list of edges
#         edge_ast: Edge AST to add to edges list
#         nanopub_url: URL of nanopub in NanopubStore
#         edge_types: list of edge types (e.g. primary, orthologized, computed)
#         citation: normalized citation string (uri, reference, database normalization)
#         annotations: list of annotations pulled from nanopub
#     """

#     # TODO Update convert_namespaces_ast to use it instead of convert_namespaces_str -- need lots of changes to that function

#     nanopub_id = os.path.basename(urllib.parse.urlparse(nanopub_url).path)

#     # Add BEL causal edge type
#     if edge_ast.bel_relation and 'causal' in edge_ast.spec['relations']['info'][edge_ast.bel_relation]['categories']:
#         edge_types.append('causal')

#     # Add backbone edge type
#     if 'backbone' in nanopub_url:
#         edge_types.append('backbone')
#         edge_types = [edge_type for edge_type in edge_types if edge_type != 'primary']

#     subj_canon = edge_ast.bel_subject.to_string()
#     subj_lbl = bel_utils.convert_namespaces_str(subj_canon, decanonicalize=True)

#     subj_components = edge_ast.bel_subject.subcomponents(subcomponents=[])

#     obj_canon = edge_ast.bel_object.to_string()
#     obj_lbl = bel_utils.convert_namespaces_str(obj_canon, decanonicalize=True)

#     if edge_ast.bel_object.__class__.__name__ == 'BELAst':  # Nested BEL Assertion
#         obj_components = edge_ast.bel_object.bel_subject.subcomponents(subcomponents=[])
#         obj_components = edge_ast.bel_object.bel_object.subcomponents(subcomponents=obj_components)
#     else:  # Normal BEL Assertion
#         obj_components = edge_ast.bel_object.subcomponents(subcomponents=[])

#     edge_hash = utils._create_hash(f'{subj_canon} {edge_ast.bel_relation} {obj_canon}')

#     # Add edge_dt after creating hash id in edge_iterator
#     edge = {
#         "edge": {
#             "subject": {
#                 "name": subj_canon,
#                 "name_lc": subj_canon.lower(),
#                 "label": subj_lbl,
#                 "label_lc": subj_lbl.lower(),
#                 "components": subj_components,
#             },
#             "relation": {
#                 "relation": edge_ast.bel_relation,
#                 "edge_hash": edge_hash,
#                 "nanopub_url": nanopub_url,
#                 "nanopub_id": nanopub_id,
#                 "citation": citation,
#                 "subject_canon": subj_canon,
#                 "subject": subj_lbl,
#                 "object_canon": obj_canon,
#                 "object": obj_lbl,
#                 "annotations": annotations,
#                 "public_flag": nanopub['isPublished'],
#                 "edge_types": edge_types,
#             },
#             'object': {
#                 "name": obj_canon,
#                 "label": obj_lbl,
#                 "components": obj_components,
#             }
#         }
#     }

#     if nanopub['nanopub']['metadata'].get('gd:creator', None):
#         edge['edge']['relation']['creator'] = nanopub['nanopub']['metadata']['gd:creator']

#     if nanopub['nanopub']['metadata'].get('project', None):
#         edge['edge']['relation']['project'] = nanopub['nanopub']['metadata']['project']

#     edges.append(copy.deepcopy(edge))
#     return edges

