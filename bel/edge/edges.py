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


def nanopub_to_edges(nanopub: dict = {}, rules: List[str] = [], orthologize_targets: list = []):
    """Process nanopub into edges and load into EdgeStore

    """

    nanopub_url = nanopub.get('source_url', '')

    try:
        if orthologize_targets == []:
            if config['bel_api'].get('edges', None):
                orthologize_targets = config['bel_api']['edges'].get('orthologize_targets', [])

        api_url = config['bel_api']['servers']['api_url']

        citation_string = normalize_nanopub_citation(nanopub)

        start_time = datetime.datetime.now()

        # Add unorthologized edges
        edges = create_edges(nanopub, api_url, citation_string)
        end_time1 = datetime.datetime.now()
        delta_ms = f'{(end_time1 - start_time).total_seconds() * 1000:.1f}'
        log.info('Timing - Get unorthologized edges from nanopub', delta_ms=delta_ms)

        # Add orthologized edges
        for orthologize_target in orthologize_targets:
            edges.extend(create_edges(nanopub, api_url, citation_string, orthologize_target=orthologize_target))

        end_time2 = datetime.datetime.now()
        delta_ms = f'{(end_time2 - end_time1).total_seconds() * 1000:.1f}'
        log.info('Timing - Get orthologized edges from nanopub', delta_ms=delta_ms)

        return {"edges": edges, "nanopub_id": nanopub['nanopub']['id'], "nanopub_url": nanopub_url, "success": True}

    except Exception as e:
        log.error(f'Failed converting nanopub into edges NanopubUrl: {nanopub_url}', exc_info=True)
        return {"nanopub_id": nanopub['nanopub']['id'], "nanopub_url": nanopub_url, "success": False, "error": str(e)}


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

        start_time = datetime.datetime.now()

        if not assertion['relation']:
            continue  # Skip any subject only statements

        edge = {
            'edge': {
                'subject': {},
                'relation': {
                    'relation': assertion['relation'],
                    'edge_dt': edge_dt,
                    'nanopub_url': nanopub['source_url'],
                    'nanopub_id': nanopub['nanopub']['id'],
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

        end_time1 = datetime.datetime.now()
        delta_ms = f'{(end_time1 - start_time).total_seconds() * 1000:.1f}'
        log.info('Timing - Parse bel statement', delta_ms=delta_ms)

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

        end_time2 = datetime.datetime.now()
        # Primary Edge
        process_belobj_into_triples(bo, edge)
        end_time3 = datetime.datetime.now()
        delta_ms = f'{(end_time3 - end_time2).total_seconds() * 1000:.1f}'
        log.info('Timing - Canonicalize into triples', delta_ms=delta_ms)

        # log.debug(f'Edge: {edge}')
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

    end_time1 = datetime.datetime.now()
    delta_ms = f'{(end_time1 - start_time).total_seconds() * 1000:.1f}'
    log.info('Timing - Assertion to edges', delta_ms=delta_ms)

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

    log.info(f'BO {bo}')

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


def main():
    pass


if __name__ == '__main__':
    # Setup logging
    import logging.config
    module_fn = os.path.basename(__file__)
    module_fn = module_fn.replace('.py', '')

    if config.get('logging', False):
        logging.config.dictConfig(config.get('logging'))

    log = logging.getLogger(f'{module_fn}')

    main()
