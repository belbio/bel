from typing import Tuple

import bel.db.elasticsearch
import bel.lang.belobj
from bel.Config import config

import structlog
log = structlog.getLogger(__name__)

es = bel.db.elasticsearch.get_client()


def validate(nanopub: dict, error_level: str = 'WARNING') -> Tuple[str, str, str]:
    """Validate Nanopub

    Error Levels are similar to log levels - selecting WARNING includes both
    WARNING and ERROR, selecting ERROR just includes ERROR

    The validation result is a list of tuples containing what level of validation
    issue this is, followed by what aspect of the nanopub "STRUCTURE" or
    "ASSERTION" or "ANNOTATION", followed by the validation warning or error message.

    Args:
        nanopub: nanopub record starting with nanopub...
        level: return WARNING or just ERROR?  defaults to warnings and errors
    Returns:
        list(tuples): [("ERROR|WARNING", "STRUCTURE|ASSERTION|ANNOTATION", <msg>]

    """

    if 'nanopub' in nanopub:
        nanopub = nanopub['nanopub']

    # Validation results
    v = {
        'ERROR': {"STRUCTURE": [], 'ASSERTION': [], 'ANNOTATION': []},
        'WARNING': {"STRUCTURE": [], 'ASSERTION': [], 'ANNOTATION': []},
    }

    bel_version = config['bel']['lang']['default_bel_version']
    # Structural checks
    try:
        if not isinstance(nanopub['assertions'], list):
            v['ERROR']['STRUCTURE'].append("Assertions must be a list/array")
    except Exception as e:
        v['ERROR']['STRUCTURE'].append('Missing nanopub["assertions"]')

    try:
        if 'name' in nanopub['type'] and 'version' in nanopub['type']:
            pass
        if nanopub['type']['name'].upper() == 'BEL':
            bel_version = nanopub['type']['version']

    except Exception as e:
        v['ERROR']['STRUCTURE'].append('Missing or badly formed type - must have nanopub["type"] = {"name": <name>, "version": <version}')

    try:
        for key in ['uri', 'database', 'reference']:
            if key in nanopub['citation']:
                break
        else:
            v['ERROR']['STRUCTURE'].append('nanopub["citation"] must have either a uri, database or reference key.')
    except Exception as e:
        v['ERROR']['STRUCTURE'].append('nanopub must have a "citation" key with either a uri, database or reference key.')

    # Assertion checks

    if 'assertions' in nanopub:
        for assertion in nanopub['assertions']:
            bo = bel.lang.belobj.BEL(bel_version, config['bel_api']['servers']['api_url'])
            belstr = f'{assertion.get("subject")} {assertion.get("relation", "")} {assertion.get("object", "")}'
            belstr = belstr.replace('None', '')
            try:
                messages = bo.parse(belstr, error_level=error_level).validation_messages
                for message in messages:
                    (level, msg) = message
                    v[level]['ASSERTION'].append(msg)
            except Exception as e:
                v['ERROR']['ASSERTION'].append(f'Could not parse: {belstr}')
                log.exception(f'Could not parse: {belstr}')

    # Annotation checks
    if error_level == 'WARNING':
        for annotation in nanopub.get('annotations', []):
            term_type = annotation['type']
            term_id = annotation['id']
            # term_label = annotation['label']
            log.info(f'Annotation: {term_type}  ID: {term_id}')

            search_body = {
                "_source": ["src_id", "id", "name", "label", "annotation_types"],
                "query": {"term": {"id": term_id}}
            }

            results = es.search(index='terms', doc_type='term', body=search_body)
            if len(results['hits']['hits']) > 0:
                result = results['hits']['hits'][0]['_source']
                if term_type not in result['annotation_types']:
                    v['WARNING']['ANNOTATION'].append(f'Annotation type: {term_type} for {term_id} does not match annotation types in database: {result["annotation_types"]}')
            else:
                v['WARNING']['ANNOTATION'].append(f'Annotation term: {term_id} not found in database')

    return v
