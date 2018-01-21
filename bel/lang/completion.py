#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Completion notes
1. Won't complete inside of a quote.  If there are mis-matched quotes
   it will break completions
2. terms upstream of a '(' are functions/modifiers
3. commas separate arguments of upstream function


"""

from typing import Mapping, Any, List, Tuple, Optional
import re
import json
import copy

import bel.utils
import bel.lang.partialparse as pparse
import bel.lang.bel_specification as bel_specification

import logging
import logging.config

from bel.Config import config

# logging.config.dictConfig(config['logging'])
log = logging.getLogger(__name__)

default_bel = config['bel']['lang']['default_bel_version']

# Custom Typing definitions
Span = Tuple[int, int]
AST = Mapping[str, Any]
BELSpec = Mapping[str, Any]


def in_span(loc: int, span: Span) -> bool:
    """Checks if loc is inside span"""

    if loc >= span[0] and loc <= span[1]:
        return True
    else:
        return False


def cursor(belstr: str, ast: AST, cursor_loc: int, result: Mapping[str, Any] = None) -> Mapping[str, Any]:
    """Find BEL function or argument at cursor location

    Args:
        belstr: BEL String used to create the completion_text
        ast (Mapping[str, Any]): AST (dict) of BEL String
        cursor_loc (int): given cursor location from input field
            cursor_loc starts at 0, think of it like a block cursor covering each char
        result: used to recursively return the result
    Returns:
        result dict
    """

    log.debug(f'SubAST: {json.dumps(ast, indent=4)}')

    # Recurse down through subject, object, nested to functions
    log.debug(f'Cursor keys {ast.keys()}')

    if len(belstr) == 0:
        return {'type': 'Function', 'replace_span': (0, 0), 'completion_text': ''}

    if 'relation' in ast and in_span(cursor_loc, ast['relation']['span']):
        log.debug('In relation')

        completion_text = belstr[ast['relation']['span'][0]:cursor_loc + 1]
        return {
            'type': 'Relation',
            'replace_span': ast['relation']['span'],
            'completion_text': completion_text,
        }

    # Handle subject, object and nested keys in tree
    elif 'span' not in ast and isinstance(ast, dict):
        for key in ast:
            if key in ['subject', 'object', 'nested']:
                log.debug(f'Recursing Keys {key}')
                result = cursor(belstr, ast[key], cursor_loc, result=result)
                if result:
                    return result

    # Matches Functions, NSArgs and StrArgs/StrArgNSArg
    if 'span' in ast and in_span(cursor_loc, ast['span']):
        log.debug('Inside subject/object subAST')
        if 'function' in ast:
            name_span = ast['function']['name_span']
            if in_span(cursor_loc, name_span):
                return {
                    'type': 'Function',
                    'replace_span': name_span,
                    'completion_text': belstr[name_span[0]:cursor_loc + 1]
                }
            for idx, arg in enumerate(ast['args']):
                if cursor_loc == ast['function']['parens_span'][0] and ast['function']['parens_span'][1] == -1:
                    return {
                        'type': 'StrArg',  # default type if unknown
                        'arg_idx': idx,
                        'replace_span': arg['span'],  # replace entire strarg
                        'parent_function': ast['function']['name'],
                        'completion_text': '',
                    }

                elif in_span(cursor_loc, arg['span']):
                    log.debug('In argument span {arg["span"]}  Cursor_loc: {cursor_loc}')
                    if arg['type'] == 'Function':
                        if in_span(cursor_loc, arg['function']['name_span']):
                            log.debug('Found replace_span in args: Function type')
                            return {
                                'type': 'Function',
                                'replace_span': arg['function']['name_span'],  # replace function name only
                                'arg_idx': idx,
                                'args': copy.deepcopy(ast['args']),
                                'parent_function': ast['function']['name'],
                                'completion_text': belstr[arg['function']['name_span'][0]:cursor_loc + 1]
                            }
                        else:
                            log.debug(f'Recursing Function  {arg["span"]}')
                            result = cursor(belstr, arg, cursor_loc, result=result)
                    elif arg['type'] == 'NSArg':

                        result = {
                            'type': 'NSArg',
                            'replace_span': arg['span'],  # replace entire nsarg
                            'arg_idx': idx,
                            'args': copy.deepcopy(ast['args']),
                            'parent_function': ast['function']['name'],
                        }

                        # Filter on namespace and query on ns_val chars up to cursor_loc
                        if in_span(cursor_loc, arg['nsarg']['ns_val_span']):
                            result['namespace'] = arg['nsarg']['ns']  # provide namespace for nsarg filtering
                            result['completion_text'] = belstr[arg['nsarg']['ns_val_span'][0]:cursor_loc + 1]
                        # Query on nsarg chars up to cursor_loc
                        else:
                            result['completion_text'] = belstr[arg['nsarg']['ns_span'][0]:cursor_loc + 1]

                        log.debug(f'Found replace_span in args: NSArg {result}')
                        return result
                    elif arg['type'] == 'StrArg':  # in case this is a default namespace StrArg
                        if arg['span'][0] == arg['span'][1]:  # handle case like p() cursor=2
                            completion_text = ''
                        else:
                            completion_text = belstr[arg['span'][0]:cursor_loc + 1]

                        return {
                            'type': 'StrArg',
                            'arg_idx': idx,
                            'replace_span': arg['span'],  # replace entire strarg
                            'parent_function': ast['function']['name'],
                            'completion_text': completion_text,
                        }
    return result  # needed to pass result back up recursive stack


def nsarg_completions(completion_text: str, entity_types: list, bel_spec: BELSpec, namespace: str, species_id: str, bel_fmt: str, size: int):
    """Namespace completions

    Args:
        completion_text
        entity_types: used to filter namespace search results
        bel_spec: used to search default namespaces
        namespace: used to filter namespace search results
        species_id: used to filter namespace search results
        bel_fmt: used to select full name or abbrev for default namespaces
        size: how many completions to return

    Results:
        list of replacement text objects
    """

    minimal_nsarg_completion_len = 2

    species = [species_id]
    namespaces = [namespace]
    replace_list = []

    if len(completion_text) >= minimal_nsarg_completion_len:
        try:
            import services.terms
            annotation_types = []
            namespaces = []
            results = services.terms.get_term_completions(completion_text, size, entity_types, annotation_types, species, namespaces)
            ns_completions = {'completion_text': completion_text, 'completions': results}

        except ModuleNotFoundError as e:
            url = f'{config["bel_api"]["servers"]["api_url"]}/terms/completions/{completion_text}'
            params = {'size': size, 'entity_types': entity_types, 'namespaces': namespaces, 'species': species}
            r = bel.utils.get_url(url, params=params)
            if r.status_code == 200:
                ns_completions = r.json()
            else:
                ns_completions = {}

        for complete in ns_completions.get('completions', []):
            replace_list.append({'replacement': complete['id'], 'label': complete['label'], 'highlight': complete['highlight'][-1], 'type': 'NSArg'})

    # Check default namespaces
    for entity_type in entity_types:
        for obj in bel_spec['namespaces']['default'].get(entity_type, []):
            if bel_fmt == 'long' and re.match(completion_text, obj['name'], re.IGNORECASE):
                replacement = obj['name']
                highlight = replacement.replace(completion_text, f'<em>{completion_text}</em>')
                replace_list.insert(0, {'replacement': replacement, 'label': replacement, 'highlight': highlight, 'type': 'NSArg'})
            elif bel_fmt in ['short', 'medium'] and re.match(completion_text, obj['abbreviation'], re.IGNORECASE):
                replacement = obj['abbreviation']
                highlight = replacement.replace(completion_text, f'<em>{completion_text}</em>')
                replace_list.insert(0, {'replacement': replacement, 'label': replacement, 'highlight': highlight, 'type': 'NSArg'})

    return replace_list[:size]


def relation_completions(completion_text: str, bel_spec: BELSpec, bel_fmt: str, size: int) -> list:
    """Filter BEL relations by prefix

    Args:
        prefix: completion string
        bel_fmt: short, medium, long BEL formats
        spec: BEL specification

    Returns:
        list: list of BEL relations that match prefix
    """

    if bel_fmt == 'short':
        relation_list = bel_spec['relations']['list_short']
    else:
        relation_list = bel_spec['relations']['list_long']

    matches = []
    for r in relation_list:
        print('R', r, 'C', completion_text)
        if re.match(completion_text, r):
            matches.append(r)

    replace_list = []
    for match in matches:
        highlight = match.replace(completion_text, f'<em>{completion_text}</em>')
        replace_list.append({'replacement': match, 'label': match, 'highlight': highlight, 'type': 'Relation'})

    return replace_list[:size]


def function_completions(completion_text: str, bel_spec: BELSpec, function_list: list, bel_fmt: str, size: int) -> list:
    """Filter BEL functions by prefix

    Args:
        prefix: completion string
        bel_fmt: short, medium, long BEL formats
        spec: BEL specification

    Returns:
        list: list of BEL functions that match prefix
    """

    # Convert provided function list to correct bel_fmt
    if function_list:
        if bel_fmt in ['short', 'medium']:
            function_list = [bel_spec['functions']['to_short'][fn] for fn in function_list]
        else:
            function_list = [bel_spec['functions']['to_long'][fn] for fn in function_list]
    elif bel_fmt in ['short', 'medium']:
        function_list = bel_spec['functions']['primary']['list_short']
    else:
        function_list = bel_spec['functions']['primary']['list_long']

    matches = []
    for f in function_list:
        if re.match(completion_text, f):
            matches.append(f)

    replace_list = []
    for match in matches:
        if completion_text:
            highlight = match.replace(completion_text, f'<em>{completion_text}</em>')
        else:
            highlight = completion_text

        replace_list.append({'replacement': match, 'label': match, 'highlight': highlight, 'type': 'Function'}, )

    return replace_list[:size]


def arg_completions(completion_text: str, parent_function: str, args: list, arg_idx: int, bel_spec: BELSpec, bel_fmt: str, species_id: str, namespace: str, size: int):
    """Function argument completion

    Only allow legal options for completion given function name, arguments and index of argument
    to replace.

    Args:
        completion_text: text to use for completion - used for creating highlight
        parent_function: BEL function containing these args
        args: arguments of BEL function
        arg_idx: completing on this argument identified by this index
        bel_spec: BEL Specification
        bel_fmt: short, medium, long BEL function/relation formats
        species_id: filter on this species id, e.g. TAX:9606 if available
        namespace: filter on this namespace if available
        size: number of completions to return

    Return:
        list of replacements
    """

    function_long = bel_spec['functions']['to_long'].get(parent_function)
    if not function_long:
        return []

    signatures = bel_spec['functions']['signatures'][function_long]['signatures']

    # Position based argument  ###################################
    function_list = []
    entity_types = []
    fn_replace_list, ns_arg_replace_list = [], []

    for signature in signatures:
        sig_arg = signature['arguments'][arg_idx]
        sig_type = sig_arg['type']

        if sig_arg.get('position', False):
            if sig_type in ['Function', 'Modifier']:
                function_list.extend(sig_arg['values'])
            elif sig_type in ['NSArg', 'StrArgNSArg']:
                entity_types.extend(sig_arg['values'])

    if function_list:
        log.info(f'ArgComp - position-based Function list: {function_list}')
        fn_replace_list = function_completions(completion_text, bel_spec, function_list, bel_fmt, size)

    if entity_types:
        log.info(f'ArgComp - position-based Entity types: {entity_types}')
        ns_arg_replace_list = nsarg_completions(completion_text, entity_types, bel_spec, namespace, species_id, bel_fmt, size)

    replace_list = fn_replace_list + ns_arg_replace_list

    if replace_list:
        return replace_list

    # Non position based argument #################################
    # Collect optional and multiple Function types
    # TODO Figure out how to handle NSArg mult_arg in complex() signature (bel_v2_0_0.json)
    #      can't filter for Complex entity_types at this point

    opt, mult = set(), set()
    for signature in signatures:
        for val in signature['opt_args']:
            opt.add(val)
        for val in signature['mult_args']:
            mult.add(val)

    for idx, arg in enumerate(args):
        # Skip argument we are completing on for removing optional Functions from function_list
        if arg_idx == idx:
            continue

        # Remove optional argument functions if they've been used already so we don't suggest them again
        if arg['type'] == 'Function':
            opt.discard(bel_spec['functions']['to_long'][arg['function']['name']])

    function_list = list(opt) + list(mult)
    if 'NSArg' in function_list:
        log.info('ArgCompletion - removed NSArg from opt/mult list')
        function_list.remove('NSArg')

    log.info(f'ArgComp - opt/multi Function list: {function_list}')

    replace_list.extend(function_completions(completion_text, bel_spec, function_list, bel_fmt, size))

    return replace_list


def add_completions(replace_list: list, belstr: str, replace_span: Span, completion_text: str) -> List[Mapping[str, Any]]:
    """Create completions to return given replacement list

    Args:
        replace_list: list of completion replacement values
        belstr: BEL String
        replace_span: start, stop of belstr to replace
        completion_text: text to use for completion - used for creating highlight
    Returns:
        [{
            "replacement": replacement,
            "cursor_loc": cursor_loc,
            "highlight": highlight,
            "label": label,
        }]
    """

    completions = []

    for r in replace_list:
        if '(' not in belstr:
            replacement = f'{r["replacement"]}()'
            cursor_loc = len(replacement) - 1  # inside parenthesis
        elif r['type'] == 'Function' and replace_span[1] == len(belstr):
            replacement = belstr[0:replace_span[0]] + f"{r['replacement']}()"
            cursor_loc = len(replacement) - 1  # inside parenthesis
        else:
            replacement = belstr[0:replace_span[0]] + r['replacement'] + belstr[replace_span[1] + 1:]
            cursor_loc = len(belstr[0:replace_span[0]] + r['replacement'])  # move cursor just past replacement

        completions.append({
            "replacement": replacement,
            "cursor_loc": cursor_loc,
            "highlight": r['highlight'],
            "label": r['label'],
        })

    return completions


def get_completions(belstr: str, cursor_loc: int, bel_spec: BELSpec, bel_comp: str, bel_fmt: str, species_id: str, size: int):
    """Get BEL Assertion completions

    Args:

    Results:

    """

    ast, errors = pparse.get_ast_dict(belstr)

    # print('AST:\n', json.dumps(ast, indent=4))

    # TODO - update collect_spans to use AST
    spans = []
    # spans = pparse.collect_span(ast)

    completions = []
    function_help = []

    log.debug(f'Cursor location BELstr: {belstr}  Cursor idx: {cursor_loc}')
    cursor_results = cursor(belstr, ast, cursor_loc)
    log.debug(f'Cursor results: {cursor_results}')

    if not cursor_results:
        log.debug('Cursor results is empty')
        return ([], [], [], [])

    completion_text = cursor_results.get('completion_text', '')

    replace_span = cursor_results['replace_span']
    namespace = cursor_results.get('namespace', None)

    if 'parent_function' in cursor_results:
        parent_function = cursor_results['parent_function']
        function_help = bel.lang.bel_specification.get_function_help(cursor_results['parent_function'], bel_spec)

        args = cursor_results.get('args', [])
        arg_idx = cursor_results.get('arg_idx')

        replace_list = arg_completions(completion_text, parent_function, args, arg_idx, bel_spec, bel_fmt, species_id, namespace, size)
    elif cursor_results['type'] == 'Function':
        function_list = None
        replace_list = function_completions(completion_text, bel_spec, function_list, bel_fmt, size)
    elif cursor_results['type'] == 'Relation':
        replace_list = relation_completions(completion_text, bel_spec, bel_fmt, size)

    completions.extend(add_completions(replace_list, belstr, replace_span, completion_text))

    return completion_text, completions, function_help, spans


def bel_completion(belstr: str, cursor_loc: int = -1, bel_version: str = default_bel, bel_comp: str = None, bel_fmt: str = 'medium', species_id: str = None, size: int = 10) -> Mapping[str, Any]:
    """BEL Completion

    Args:
        belstr (str): BEL String to provide completion for
        cursor_loc (int): cursor location - default of -1 means end of string
        bel_version (str): BEL Language version to use for completion
        bel_comp (str): ['subject', 'object', 'full', None] - a nested statement has to be found in object or full statement
        bel_fmt (str): ['short', 'medium', 'long'] BEL function/relation format
        species_id (str): optional, species id is used to filter namespace values if applicable (e.g. Gene, RNA, ... entity_types)
        size: how many completions to return, defaults to 10

    Returns:
        Mapping[str, Any]:
            {
                'completions': completions,
                'function_help': function_help,
                'entity_spans': spans
            }
    """

    """
    Completion object: {
        completions: [
            {
                'replacement': <replacement text field string,
                'cursor_loc': <new cursor location>
                'highlight': <highlighted match>
                'label': <label for completion>
            },
        ],
        function_help: [{
            "function_summary": <template>,
            "argument_help": [<argument help>],
            "description": <desc>
        }],
        "entity_spans": {<span info>}
    }

    """
    bel_spec = bel_specification.get_specification(bel_version)

    belstrlen = len(belstr)
    if cursor_loc == -1:
        cursor_loc = belstrlen - 1
    elif cursor_loc >= belstrlen:
        cursor_loc = belstrlen - 1

    # with timy.Timer() as timer:
    #     (completion_text, completions, function_help, spans) = get_completions(belstr, cursor_loc, bel_spec, bel_comp, bel_fmt, species_id, size)

    (completion_text, completions, function_help, spans) = get_completions(belstr, cursor_loc, bel_spec, bel_comp, bel_fmt, species_id, size)

    return {'completion_text': completion_text, 'completions': completions, 'function_help': function_help, 'entity_spans': spans}


def main():

    bel_version = '2.0.0'
    bel_spec = bel_specification.get_specification(bel_version)

    belstr = 'compositeAbundance(proteinAbundance(HGNC:FN1), proteinAbundance(HGNC:VEGFA)) increases translocation(proteinAbundance(HGNC:PRKCA), fromLoc(MESH:Intracellular Space), toLoc(MESH:Cell Membrane))'
    belstr = 'proteinAbundance(HGNC:VEGFA) increases (compositeAbundance(proteinAbundance(HGNC:ITGB1), proteinAbundance(HGNC:PRKCA, ma(kin))) increases biologicalProcess(GO:\"cell-matrix adhesion\"))'
    belstr = 'complex(p(HGNC:EGFR))'
    # belstr = 'p(HGNC:AKT)'

    cursor_loc = 18
    completions = bel_completion(belstr, cursor_loc, bel_fmt="long")
    print('Completions:\n', json.dumps(completions, indent=4))



    quit()
    ast, errors = pparse.get_ast_dict(belstr)
    # print('AST:\n', json.dumps(ast, indent=4))
    # quit()
    cursor_loc = 8
    results = cursor(belstr, ast, cursor_loc)
    print(f'Cursor{cursor_loc}:\n', json.dumps(results, indent=4))
    quit()




    bel_comp = ''
    bel_fmt = 'long'
    species_id = 'TAX:9606'
    completions = get_completions(belstr, cursor_loc, functions, bel_spec, bel_comp, bel_fmt, species_id)
    print('Completions:\n', json.dumps(completions, indent=4))
    quit()


    completions = ns_completions('AKT', ['Protein'], 'TAX:9606', 10)
    print('Completions:\n', json.dumps(completions, indent=4))
    quit()

    # completions = bel_completion('pa', bel_fmt='long')
    # print('DumpVar:\n', json.dumps(completions, indent=4))

    completions = bel_completion('path(', cursor_loc=1, bel_fmt='medium')
    print('DumpVar:\n', json.dumps(completions, indent=4))


if __name__ == '__main__':
    main()
