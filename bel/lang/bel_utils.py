# BEL object utilities

import re
import json
import yaml
import copy
from typing import Mapping, List

from bel.lang.ast import NSArg
from bel.Config import config
from bel.utils import get_url, url_path_param_quoting
import bel.terms.terms
import bel.terms.orthologs

import logging
log = logging.getLogger(__name__)


def convert_nsarg_db(nsarg: str) -> dict:
    """Get default canonical and decanonical versions of nsarg

    Returns:
        dict: {'canonical': <nsarg>, 'decanonical': <nsarg>}
    """


def convert_nsarg(nsarg: str, api_url: str = None, namespace_targets: Mapping[str, List[str]] = None, canonicalize: bool = False, decanonicalize: bool = False) -> str:
    """[De]Canonicalize NSArg

    Args:
        nsarg (str): bel statement string or partial string (e.g. subject or object)
        api_url (str): BEL.bio api url to use, e.g. https://api.bel.bio/v1
        namespace_targets (Mapping[str, List[str]]): formatted as in configuration file example
        canonicalize (bool): use canonicalize endpoint/namespace targets
        decanonicalize (bool): use decanonicalize endpoint/namespace targets

    Results:
        str: converted NSArg
    """

    if not api_url:
        api_url = config['bel_api']['servers']['api_url']
        if not api_url:
            log.error('Missing api url - cannot convert namespace')
            return None

    params = None
    if namespace_targets:
        namespace_targets_str = json.dumps(namespace_targets)
        params = {'namespace_targets': namespace_targets_str}

    if not namespace_targets:
        if canonicalize:
            api_url = api_url + '/terms/{}/canonicalized'
        elif decanonicalize:
            api_url = api_url + '/terms/{}/decanonicalized'
        else:
            log.warning('Missing (de)canonical flag - cannot convert namespaces')
            return nsarg
    else:

        api_url = api_url + '/terms/{}/canonicalized'  # overriding with namespace_targets

    request_url = api_url.format(url_path_param_quoting(nsarg))

    r = get_url(request_url, params=params, timeout=10)

    if r and r.status_code == 200:
        nsarg = r.json().get('term_id', nsarg)
    elif not r or r.status_code == 404:
        log.error(f'[de]Canonicalization endpoint missing: {request_url}')

    return nsarg


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

    # pattern - look for capitalized namespace followed by colon
    #           and either a quoted string or a string that
    #           can include any char other than space, comma or ')'
    matches = re.findall(r'([A-Z]+:"(?:\\.|[^"\\])*"|[A-Z]+:(?:[^\),\s]+))', bel_str)
    for nsarg in matches:
        if 'DEFAULT:' in nsarg:  # skip default namespaces
            continue

        updated_nsarg = convert_nsarg(nsarg, api_url=api_url, namespace_targets=namespace_targets, canonicalize=canonicalize, decanonicalize=decanonicalize)
        if updated_nsarg != nsarg:
            bel_str = bel_str.replace(nsarg, updated_nsarg)

    return bel_str


def convert_namespaces_ast(ast, api_url: str = None, namespace_targets: Mapping[str, List[str]] = None, canonicalize: bool = False, decanonicalize: bool = False):
    """Recursively convert namespaces of BEL Entities in BEL AST using API endpoint

    Canonicalization and decanonicalization is determined by endpoint used and namespace_targets.

    Args:
        ast (BEL): BEL AST
        api_url (str): endpoint url with a placeholder for the term_id (either /terms/<term_id>/canonicalized or /terms/<term_id>/decanonicalized)
        namespace_targets (Mapping[str, List[str]]): (de)canonical targets for converting BEL Entities

    Returns:
        BEL: BEL AST
    """

    if isinstance(ast, NSArg):
        given_term_id = '{}:{}'.format(ast.namespace, ast.value)

        # Get normalized term if necessary
        if (canonicalize and not ast.canonical) or (decanonicalize and not ast.decanonical):
            normalized_term = convert_nsarg(given_term_id, api_url=api_url, namespace_targets=namespace_targets, canonicalize=canonicalize, decanonicalize=decanonicalize)
            if canonicalize:
                ast.canonical = normalized_term
            elif decanonicalize:
                ast.decanonical = normalized_term

        # Update normalized term
        if canonicalize:
            ns, value = ast.canonical.split(':')
            ast.change_nsvalue(ns, value)
        elif decanonicalize:
            ns, value = ast.canonical.split(':')
            ast.change_nsvalue(ns, value)

    # Recursively process every NSArg by processing BELAst and Functions
    if hasattr(ast, 'args'):
        for arg in ast.args:
            convert_namespaces_ast(arg, api_url=api_url, namespace_targets=namespace_targets, canonicalize=canonicalize, decanonicalize=decanonicalize)

    return ast


def populate_ast_nsarg_defaults(ast, belast, species_id=None):
    """Recursively populate NSArg AST entries for default (de)canonical values

    This was added specifically for the BEL Pipeline. It is designed to
    run directly against ArangoDB and not through the BELAPI.

    Args:
        ast (BEL): BEL AST

    Returns:
        BEL: BEL AST
    """

    if isinstance(ast, NSArg):
        given_term_id = '{}:{}'.format(ast.namespace, ast.value)

        r = bel.terms.terms.get_normalized_terms(given_term_id)
        ast.canonical = r['canonical']
        ast.decanonical = r['decanonical']

        r = bel.terms.terms.get_terms(ast.canonical)

        if len(r) > 0:
            ast.species_id = r[0].get('species_id', False)
            ast.species_label = r[0].get('species_label', False)

        # Check to see if species is set and if it's consistent
        #   if species is not consistent for the entire AST - set species_id/label
        #   on belast to False (instead of None)
        if ast.species_id and species_id is None:
            species_id = ast.species_id
            belast.species.add((ast.species_id, ast.species_label, ))

        elif ast.species_id and species_id and species_id != ast.species_id:
            belast.species_id = False
            belast.species_label = False

    # Recursively process every NSArg by processing BELAst and Functions
    if hasattr(ast, 'args'):
        for arg in ast.args:
            populate_ast_nsarg_defaults(arg, belast, species_id)

    return ast


def orthologize(ast, bo, species_id: str):
    """Recursively orthologize BEL Entities in BEL AST using API endpoint

    NOTE: - will take first ortholog returned in BEL.bio API result (which may return more than one ortholog)

    Args:
        ast (BEL): BEL AST
        endpoint (str): endpoint url with a placeholder for the term_id

    Returns:
        BEL: BEL AST
    """

    # if species_id == 'TAX:9606' and str(ast) == 'MGI:Sult2a1':
    #     import pdb; pdb.set_trace()

    if not species_id:
        bo.validation_messages.append(('WARNING', 'No species id was provided for orthologization'))
        return ast

    if isinstance(ast, NSArg):
        if ast.orthologs:
            # log.debug(f'AST: {ast.to_string()}  species_id: {species_id}  orthologs: {ast.orthologs}')
            if ast.orthologs.get(species_id, None):
                orthologized_nsarg_val = ast.orthologs[species_id]['decanonical']
                ns, value = orthologized_nsarg_val.split(':')
                ast.change_nsvalue(ns, value)
                ast.canonical = ast.orthologs[species_id]['canonical']
                ast.decanonical = ast.orthologs[species_id]['decanonical']
                ast.orthologized = True
                print(f'AST1: {ast} orthologs: {ast.orthologs}  SpeciesID: {species_id}')
                bo.ast.species.add((species_id, ast.orthologs[species_id]['species_label']))
            else:
                bo.ast.species.add((ast.species_id, ast.species_label))
                print(f'AST2: {ast} orthologs: {ast.orthologs}  SpeciesID: {species_id}')
                bo.validation_messages.append(('WARNING', f'No ortholog found for {ast.namespace}:{ast.value}'))
        elif ast.species_id:
            bo.ast.species.add((ast.species_id, ast.species_label))

    # Recursively process every NSArg by processing BELAst and Functions
    if hasattr(ast, 'args'):
        for arg in ast.args:
            orthologize(arg, bo, species_id)

    return ast


def populate_ast_nsarg_orthologs(ast, species):
    """Recursively collect NSArg orthologs for BEL AST

    This requires bo.collect_nsarg_norms() to be run first so NSArg.canonical is available

    Args:
        ast: AST at recursive point in belobj
        species: dictionary of species ids vs labels for or
    """

    ortholog_namespace = 'EG'

    if isinstance(ast, NSArg):
        if re.match(ortholog_namespace, ast.canonical):
            orthologs = bel.terms.orthologs.get_orthologs(ast.canonical, list(species.keys()))
            for species_id in species:
                if species_id in orthologs:
                    orthologs[species_id]['species_label'] = species[species_id]

            ast.orthologs = copy.deepcopy(orthologs)

    # Recursively process every NSArg by processing BELAst and Functions
    if hasattr(ast, 'args'):
        for arg in ast.args:
            populate_ast_nsarg_orthologs(arg, species)

    return ast


def preprocess_bel_stmt(stmt: str) -> str:
    """Clean up basic formatting of BEL statement

    Args:
        stmt: BEL statement as single string

    Returns:
        cleaned BEL statement
    """

    stmt = stmt.strip()  # remove newline at end of stmt
    stmt = re.sub(r',+', ',', stmt)  # remove multiple commas
    stmt = re.sub(r',', ', ', stmt)  # add space after each comma
    stmt = re.sub(r' +', ' ', stmt)  # remove multiple spaces

    return stmt


# TODO remove AST normalize_nsarg_value for this and add tests
def quoting_nsarg(nsarg_value):
    """Quoting nsargs

    If needs quotes (only if it contains whitespace, comma or ')' ), make sure
        it is quoted, else don't add them.


    """
    quoted = re.findall(r'^"(.*)"$', nsarg_value)

    if re.search(r'[),\s]', nsarg_value):  # quote only if it contains whitespace, comma or ')'
        if quoted:
            return nsarg_value
        else:
            return f'"{nsarg_value}"'
    else:
        if quoted:
            return quoted[0]
        else:
            return nsarg_value


# # See TODO in bel.py for this function - not currently enabled
# def simple_checks(stmt):
#     """Simple typo checks for BEL statement

#     Args:
#         stmt (str): BEL statement as single string

#     Returns:
#         Tuple[bool, List[Tuple[str, str]]]: is valid? and list of ...
#     """
#     messages = []
#     is_valid = True

#     # check for even number of parenthesis
#     left_p_ct = stmt.count('(')
#     right_p_ct = stmt.count(')')

#     if left_p_ct < right_p_ct:
#         messages.append(('ERROR', 'Unbalanced parenthesis: Missing left parenthesis somewhere!'))
#     elif right_p_ct < left_p_ct:
#         messages.append(('ERROR', 'Unbalanced parenthesis: Missing right parenthesis somewhere!'))

#     # check for even number of quotation marks
#     single_quote_ct = stmt.count('\'')
#     double_quote_ct = stmt.count('"')

#     if single_quote_ct > 0:  # single quotes not allowed
#         messages.append(('ERROR', 'Single quotes are not allowed! Please use double quotes.'))

#     if double_quote_ct % 2 != 0:  # odd number of quotations
#         messages.append(('ERROR', 'Unbalanced quotations: Missing quotation mark somewhere!'))

#     if messages:
#         is_valid = False

#     (is_valid, messages)


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
        return None

    if any(char.isalpha() for char in version):
        log.error('Invalid version number entered. Examples: \'2\', \'3.1\', \'3.2.6\'.')
        return None

    version_semantic_regex = r'(\d+)(?:\.(\d+))?(?:\.(\d+))?'
    our_match = re.match(version_semantic_regex, version)

    if our_match:
        wanted_major = int(our_match.group(1)) if our_match.group(1) else 'x'
        wanted_minor = int(our_match.group(2)) if our_match.group(2) else 'x'
        wanted_patch = int(our_match.group(3)) if our_match.group(3) else 'x'
        formatted_version = '{}.{}.{}'.format(wanted_major, wanted_minor, wanted_patch)
    else:
        log.error('Invalid version number entered. Examples: \'2\', \'3.1\', \'3.2.6\'.')
        return None

    if formatted_version in available_versions:
        return formatted_version

    # now we need to find closest available version that is EQUAL OR GREATER

    available_versions.sort(key=lambda s: list(map(int, s.split('.'))))

    best_choice = None

    for v in available_versions:
        v_split = v.split('.')
        v_maj = int(v_split[0])
        v_min = int(v_split[1])
        v_pat = int(v_split[2])

        if wanted_major == v_maj and wanted_minor == v_min and wanted_patch == v_pat:
            return v  # exact version found. return.
        elif wanted_major == v_maj and wanted_minor == v_min and wanted_patch == 'x':
            best_choice = v  # continue to see if higher patch number available
            continue
        elif wanted_major == v_maj and wanted_minor == 'x' and wanted_patch == 'x':
            best_choice = v  # continue to see if higher minor/patch number available
            continue

    if best_choice is not None:
        log.error('Version {} not available in library. Defaulting to {}.'.format(version, best_choice))
    else:
        log.error('Version {} not available in library.'.format(version))

    return best_choice


class MyDumper(yaml.Dumper):

    def increase_indent(self, flow=False, indentless=False):
        return super(MyDumper, self).increase_indent(flow, False)
