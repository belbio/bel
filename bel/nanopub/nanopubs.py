from typing import Mapping, Any, List, Iterable, Tuple
import gzip
import bel.lang.belobj
import jsonschema
import requests
from cityhash import CityHash64

import bel.edge.edges
from bel.Config import config

import logging
log = logging.getLogger(__name__)


# TODO is this code being used?  We also have bel.nanopub.validate.validate(nanopub, error_level) for validation


class Nanopub(object):
    """Nanopub object to manage Nanopub processing"""

    def __init__(self, endpoint: str = config.get('api', '')) -> None:
        """ Initialize Nanopub

        Args:
            endpoint (str): BEL.bio API endpoint uri, e.g. https://api.bel.bio/v1, default read from config
        """
        self.endpoint = endpoint

    def validate(self, nanopub: Mapping[str, Any]) -> Tuple[bool, List[Tuple[str, str]]]:
        """Validates using the nanopub schema

        Args:
            nanopub (Mapping[str, Any]): nanopub dict

        Returns:
            Tuple[bool, List[Tuple[str, str]]]:
                bool: Is valid?  Yes = True, No = False
                List[Tuple[str, str]]: Validation issues, empty if valid, tuple is ('ERROR|WARNING', msg)
                    e.g. [('WARNING', "Context ID not found")]        """

        # Validate nanopub
        (is_valid, messages) = validate_to_schema(nanopub, self.nanopub_schema)
        if not is_valid:
            return messages

        # Extract BEL Version
        if nanopub['nanopub']['type']['name'].upper() == "BEL":
            bel_version = nanopub['nanopub']['type']['version']
        else:
            is_valid = False
            return (is_valid, f"Not a BEL Nanopub according to nanopub.type.name: {nanopub['nanopub']['type']['name']}")

        all_messages = []
        # Validate BEL Statements
        bel_obj = bel.lang.belobj.BEL(bel_version, self.endpoint)
        for edge in nanopub['nanopub']['edges']:
            bel_statement = f"{edge['subject']} {edge['relation']} {edge['object']}"
            parse_obj = bel_obj.parse(bel_statement)
            if not parse_obj.valid:
                all_messages.extend(('ERROR', f"BEL statement parse error {parse_obj.error}, {parse_obj.err_visual}"))

        # Validate nanopub.context
        for context in nanopub['nanopub']['context']:
            (is_valid, messages) = self.validate_context(context)
            all_messages.extend(messages)

        is_valid = True
        for _type, msg in all_messages:
            if _type == 'ERROR':
                is_valid = False

        return (is_valid, all_messages)

    def validate_context(self, context: Mapping[str, Any]) -> Tuple[bool, List[Tuple[str, str]]]:
        """ Validate context

        Args:
            context (Mapping[str, Any]): context dictionary of type, id and label

        Returns:
            Tuple[bool, List[Tuple[str, str]]]:
                bool: Is valid?  Yes = True, No = False
                List[Tuple[str, str]]: Validation issues, empty if valid, tuple is ('ERROR|WARNING', msg)
                    e.g. [('WARNING', "Context ID not found")]
        """

        url = f'{self.endpoint}/terms/{context["id"]}'

        res = requests.get(url)
        if res.status_code == 200:
            return (True, [])
        else:
            return (False, [('WARNING', f'Context {context["id"]} not found at {url}')])

    def bel_edges(self, nanopub: Mapping[str, Any], namespace_targets: Mapping[str, List[str]] = {}, rules: List[str] = [], orthologize_target: str = None) -> List[Mapping[str, Any]]:
        """Create BEL Edges from BEL nanopub

        Args:
            nanopub (Mapping[str, Any]): bel nanopub
            namespace_targets (Mapping[str, List[str]]): what namespaces to canonicalize
            rules (List[str]): which computed edge rules to process, default is all,
               look at BEL Specification yaml file for computed edge signature keys,
               e.g. degradation, if any rule in list is 'skip', then skip computing edges
               just return primary_edge
            orthologize_target (str): species to convert BEL into, e.g. TAX:10090 for mouse, default option does not orthologize

        Returns:
            List[Mapping[str, Any]]: edge list with edge attributes (e.g. context)
        """

        edges = bel.edge.edges.create_edges(nanopub, self.endpoint, namespace_targets=namespace_targets, rules=rules, orthologize_target=orthologize_target)

        return edges


def validate_to_schema(nanopub, schema) -> Tuple[bool, List[Tuple[str, str]]]:
    """Validate nanopub against jsonschema for nanopub

    Args:
        nanopub (Mapping[str, Any]): nanopub dict
        schema (Mapping[str, Any]): nanopub schema

    Returns:
        Tuple[bool, List[str]]:
            bool: Is valid?  Yes = True, No = False
            List[Tuple[str, str]]: Validation issues, empty if valid, tuple is ('Error|Warning', msg)
                e.g. [('ERROR', "'subject' is a required property")]
    """

    v = jsonschema.Draft4Validator(schema)
    messages = []
    errors = sorted(v.iter_errors(nanopub), key=lambda e: e.path)
    for error in errors:
        for suberror in sorted(error.context, key=lambda e: e.schema_path):
            print(list(suberror.schema_path), suberror.message, sep=", ")
            messages.append(('ERROR', suberror.message))

    is_valid = True
    if errors:
        is_valid = False

    return (is_valid, messages)


# Following is used in nanopub-tools codebase
def hash_nanopub(nanopub: Mapping[str, Any]) -> str:
    """Create CityHash64 from nanopub for duplicate check

    TODO - check that this hash value is consistent between C# and Python running on
    laptop and server

    Build string to hash

    Collect flat array of (all values.strip()):
        nanopub.type.name
        nanopub.type.version

        One of:
            nanopub.citation.database.name
            nanopub.citation.database.id

            OR

            nanopub.citation.database.uri

            OR

            nanopub.citation.database.reference

        Extend with sorted list of assertions (SRO as single string with space between S, R and O)

        Extend with sorted list of annotations (nanopub.annotations.type + ' ' + nanopub.annotations.id)

    Convert array to string by joining array elements separated by a space

    Create CityHash64(str) and return

    """

    hash_list = []

    # Type
    hash_list.append(nanopub['nanopub']['type'].get('name', '').strip())
    hash_list.append(nanopub['nanopub']['type'].get('version', '').strip())

    # Citation
    if nanopub['nanopub']['citation'].get('database', False):
        hash_list.append(nanopub['nanopub']['citation']['database'].get('name', '').strip())
        hash_list.append(nanopub['nanopub']['citation']['database'].get('id', '').strip())
    elif nanopub['nanopub']['citation'].get('uri', False):
        hash_list.append(nanopub['nanopub']['citation'].get('uri', '').strip())
    elif nanopub['nanopub']['citation'].get('reference', False):
        hash_list.append(nanopub['nanopub']['citation'].get('reference', '').strip())

    # Assertions
    assertions = []
    for assertion in nanopub['nanopub']['assertions']:
        if assertion.get('relation') is None:
            assertion['relation'] = ''
        if assertion.get('object') is None:
            assertion['object'] = ''
        assertions.append(' '.join((assertion['subject'].strip(), assertion.get('relation', '').strip(), assertion.get('object', '').strip())).strip())
    assertions = sorted(assertions)
    hash_list.extend(assertions)

    # Annotations
    annotations = []

    for anno in nanopub['nanopub']['annotations']:
        annotations.append(' '.join((anno.get('type', '').strip(), anno.get('id', '').strip())).strip())

    annotations = sorted(annotations)
    hash_list.extend(annotations)

    np_string = ' '.join([l.lower() for l in hash_list])
    print(f'NP string for hash:{np_string}')

    return '{:x}'.format(CityHash64(np_string))
