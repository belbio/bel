# BEL object utilities

import re
import json
import yaml
import requests
import sys
from typing import Mapping, List, TYPE_CHECKING

from bel_lang.ast import BELAst, NSArg, Function
from bel_lang.Config import config

import logging
log = logging.getLogger(__name__)

if TYPE_CHECKING:  # to allow type checking for a module that would be a circular import
    import bel_lang.bel


# TODO - normalize convert_namespaces_{str|ast} - too much duplicate code - not very elegant
def convert_namespaces_str(bel_str: str, api_url: str = None, namespace_targets: Mapping[str, List[str]] = None, canonicalize: bool = False, decanonicalize: bool = False) -> str:
    """Convert namespace in string

    Uses a regex expression to extract all NSArgs and replace them with the
    updated NSArg from the BEL.bio API terms endpoint.

    Args:
        bel_str (str): bel statement string or partial string (e.g. subject or object)
        api_url (str): BEL.bio api url to use, e.g. https://api.bel.bio/v1
        namespace_targets (Mapping[str, List[str]]): formatted as in configuration file example
        canonicalize (bool): use canonicalize endpoint/namespace targets
        decanonicalize (bool): use decanonicalize endpoint/namespace targets

    Results:
        str: bel statement with namespaces converted
    """

    if not api_url:
        api_url = config['bel_api']['servers']['api_url']
        if not api_url:
            log.error('Missing api url - cannot convert namespace')
            return None

    params = None
    if not namespace_targets:
        if canonicalize:
            api_url = api_url + '/terms/{}/canonicalized'
        elif decanonicalize:
            api_url = api_url + '/terms/{}/decanonicalized'
        else:
            log.warning('Missing namespace targets or (de)canonical flag - cannot convert namespaces')
            return bel_str
    else:
        namespace_targets_str = json.dumps(namespace_targets)
        params = {'namespace_targets': namespace_targets_str}
        api_url = api_url + '/terms/{}/canonicalized'  # overriding with namespace_targets

    # pattern - look for capitalized namespace followed by colon
    #           and either a quoted string or a string that
    #           can include any char other than space, comma or ')'
    matches = re.findall(r'([A-Z]+:"(?:\\.|[^"\\])*"|[A-Z]+:(?:[^\),\s]+))', bel_str)
    for match in matches:
        if 'DEFAULT:' in match:  # skip default namespaces
            continue

        request_url = api_url.format(match)
        try:
            r = requests.get(request_url, params=params, timeout=5)
            if r.status_code == 200:
                updated_term = r.json().get('term_id', match)
                bel_str = bel_str.replace(match, updated_term)

        except requests.exceptions.Timeout:
            log.error(f'Request timeout occurred for {request_url} in bel_utils.convert_namespaces_str')

    return bel_str


def convert_namespaces_ast(ast: 'bel_lang.bel.BEL', endpoint: str, namespace_targets: Mapping[str, List[str]] = None) -> 'bel_lang.bel.BEL':
    """Convert namespaces of BEL Entities in BEL AST using API endpoint

    Canonicalization and decanonicalization is determined by endpoint used and namespace_targets.

    Args:
        ast (BEL): BEL AST
        endpoint (str): endpoint url with a placeholder for the term_id (either /terms/<term_id>/canonicalized or /terms/<term_id>/decanonicalized)
        namespace_targets (Mapping[str, List[str]]): (de)canonical targets for converting BEL Entities

    Returns:
        BEL: BEL AST
    """

    if isinstance(ast, NSArg):
        given_term_id = '{}:{}'.format(ast.namespace, ast.value)
        try:
            request_url = endpoint.format(given_term_id)
            if namespace_targets:
                namespace_targets_str = json.dumps(namespace_targets)
                params = {'namespace_targets': namespace_targets_str}
                r = requests.get(request_url, params=params, timeout=5)
            else:
                r = requests.get(request_url, timeout=5)

            if r.status_code == 200:
                updated_id = r.json().get('term_id', given_term_id)
                ns, value = updated_id.split(':')
                ast.change_nsvalue(ns, value)
        except requests.exceptions.Timeout:
            log.error(f'Request timeout occurred for {request_url} in bel_utils.convert_namespaces_ast')

    # Recursively process every NSArg by processing BELAst and Functions
    if hasattr(ast, 'args'):
        for arg in ast.args:
            convert_namespaces_ast(arg, endpoint, namespace_targets)

    return ast


def orthologize(ast, bo: 'bel_lang.bel.BEL', species_id: str) -> 'bel_lang.bel.BEL':
    """Orthologize BEL Entities in BEL AST using API endpoint

    NOTE: - will take first ortholog returned in BEL.bio API result (which may return more than one ortholog)

    Args:
        ast (BEL): BEL AST
        endpoint (str): endpoint url with a placeholder for the term_id

    Returns:
        BEL: BEL AST
    """

    if not species_id:
        bo.validation_messages.append(('WARNING', 'No species id was provided'))
        return ast

    if isinstance(ast, NSArg):
        given_term_id = '{}:{}'.format(ast.namespace, ast.value)
        orthologize_req_url = f'{bo.endpoint}/orthologs/{given_term_id}/{species_id}'
        r = requests.get(orthologize_req_url)

        if r.status_code == 200:
            orthologs = r.json().get('orthologs')
            if orthologs:
                ortholog_id = orthologs[0]
                ns, value = ortholog_id.split(':')
                ast.change_nsvalue(ns, value)
        else:
            bo.validation_messages.append(('WARNING', f'No ortholog found for {given_term_id}'))

    # Recursively process every NSArg by processing BELAst and Functions
    if hasattr(ast, 'args'):
        for arg in ast.args:
            orthologize(arg, bo, species_id)

    return ast


def preprocess_bel_stmt(stmt):
    """Clean up basic formatting of BEL statement

    Args:
        stmt (str): BEL statement as single string

    Returns:
        (str): cleaned BEL statement
    """

    stmt = stmt.strip()  # remove newline at end of stmt
    stmt = re.sub(r',+', ',', stmt)  # remove multiple commas
    stmt = re.sub(r',', ', ', stmt)  # add space after each comma
    stmt = re.sub(r' +', ' ', stmt)  # remove multiple spaces

    return stmt


# See TODO in bel.py for this function - not currently enabled
def simple_checks(stmt):
    """Simple typo checks for BEL statement

    Args:
        stmt (str): BEL statement as single string

    Returns:
        Tuple[bool, List[Tuple[str, str]]]: is valid? and list o f
    """
    messages = []
    is_valid = True

    # check for even number of parenthesis
    left_p_ct = stmt.count('(')
    right_p_ct = stmt.count(')')

    if left_p_ct < right_p_ct:
        messages.append(('ERROR', 'Unbalanced parenthesis: Missing left parenthesis somewhere!'))
    elif right_p_ct < left_p_ct:
        messages.append(('ERROR', 'Unbalanced parenthesis: Missing right parenthesis somewhere!'))

    # check for even number of quotation marks
    single_quote_ct = stmt.count('\'')
    double_quote_ct = stmt.count('"')

    if single_quote_ct > 0:  # single quotes not allowed
        messages.append(('ERROR', 'Single quotes are not allowed! Please use double quotes.'))

    if double_quote_ct % 2 != 0:  # odd number of quotations
        messages.append(('ERROR', 'Unbalanced quotations: Missing quotation mark somewhere!'))

    if messages:
        is_valid = False

    (is_valid, messages)


def handle_parser_syntax_error(e):
    col_failed = e.pos
    info = e.buf.line_info(e.pos)
    text = info.text.rstrip()
    leading = re.sub(r'[^\t]', ' ', text)[:info.col]
    text = text.expandtabs()
    leading = leading.expandtabs()
    undefined_type = e.stack[-1]

    err_visualizer = '{}\n{}^'.format(text, leading)
    if undefined_type == 'relations':
        error_msg = 'Failed parse at position {}. ' \
                    'Check that you have a valid relation.'.format(col_failed)
    elif undefined_type == 'funcs':
        error_msg = 'Failed parse at position {}. ' \
                    'Check that you have a valid primary or modifier function.'.format(col_failed)
    elif undefined_type == 'function_open':
        error_msg = 'Failed parse at position {}. ' \
                    'Check that you have have opened your parenthesis correctly before this point.'.format(col_failed)
    elif undefined_type == 'function_close':
        error_msg = 'Failed parse at position {}. ' \
                    'Check that you have have closed your parenthesis correctly before this point.'.format(col_failed)
    elif undefined_type == 'full_nsv':
        error_msg = 'Failed parse at position {}. ' \
                    'Check that you have a valid namespace argument.'.format(col_failed)
    else:
        error_msg = 'Failed parse at position {}. ' \
                    'Check to make sure commas/spaces are not missing.'.format(col_failed, undefined_type)

    return error_msg, err_visualizer


def _dump_spec(spec):
    """Dump bel specification dictionary using YAML

    Formats this with an extra indentation for lists to make it easier to
    use cold folding on the YAML version of the spec dictionary.
    """
    with open('spec.yaml', 'w') as f:
        yaml.dump(spec, f, Dumper=MyDumper, default_flow_style=False)


def _default_to_version(version, available_versions):

    if not available_versions:
        log.error('No versions available.')
        return ''

    version_semantic_regex = r'(\d+)(?:\.(\d+))?(?:\.(\d+))?'
    our_match = re.match(version_semantic_regex, version)

    if our_match:
        major = int(our_match.group(1)) if our_match.group(1) else 0
        minor = int(our_match.group(2)) if our_match.group(2) else 0
        patch = int(our_match.group(3)) if our_match.group(3) else 0
        formatted_version = '{}.{}.{}'.format(major, minor, patch)
    else:
        log.error('Invalid version number entered. Examples: \'2\', \'3.1\', \'3.2.6\'.')
        return ''

    if formatted_version in available_versions:
        return formatted_version

    # now we need to find closest available version

    available_versions.sort(key=lambda s: list(map(int, s.split('.'))))

    v = None

    for v in available_versions:
        v_split = v.split('.')
        v_maj = int(v_split[0])
        v_min = int(v_split[1])
        v_pat = int(v_split[2])

        if v_maj > major or (v_maj == major and v_min > minor) or (v_maj == major and v_min == minor and v_pat > patch):
            break
        else:
            continue

    log.error('Version {} is not available in bel_lang library package.\nDefaulting to version {}.'.format(version, v))

    return v


class MyDumper(yaml.Dumper):

    def increase_indent(self, flow=False, indentless=False):
        return super(MyDumper, self).increase_indent(flow, False)
