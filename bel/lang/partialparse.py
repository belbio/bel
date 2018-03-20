#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Completion notes
1. Won't complete inside of a quote.  If there are mis-matched quotes
   it will break completions
2. terms upstream of a '(' are functions/modifiers
3. commas separate arguments of upstream function


"""
import pdb

import re

import copy
from typing import Mapping, Any, List, Tuple, MutableMapping, Optional

import logging
import logging.config

from bel.Config import config

if config.get('logging', False):
    logging.config.dictConfig(config.get('logging'))
log = logging.getLogger(__name__)

start_arg_chars = ['(', ',']
end_arg_chars = [')', ',']

relations_pattern_middle = re.compile('\)\s+([a-zA-Z\=\-\>\|\:]+)\s+[\w\(]+')
relations_pattern_end = re.compile('\)\s+([a-zA-Z\=\-\>\|\:]+)\s*$')

Errors = List[Tuple[str, str, Optional[Tuple[int, int]]]]  # (<"Error"|"Warning">, "message", (start_span, end_span))
Parsed = MutableMapping[str, Any]
AST = MutableMapping[str, Any]
CharLocs = Mapping[str, Any]

"""Parsed data structure example
{
   "(77, 104)": {
        "name": "proteinAbundance",
        "type": "Function",
        "span": [
            77,
            104
        ],
        "name_span": [
            77,
            92
        ],
        "parens_span": [
            93,
            104
        ],
        "function_level": "child",
        "args": [
            {
                "arg": "HGNC:ITGB1",
                "span": [
                    94,
                    103
                ],
                "type": "NSArg",
                "ns": "HGNC",
                "ns_span": [
                    94,
                    97
                ],
                "ns_val": "ITGB1",
                "ns_val_span": [
                    99,
                    103
                ]
            }
        ]
    },
    "(29, 38)": {
        "type": "Relation",
        "name": "increases",
        "span": [
            29,
            38
        ]
    },
    "(160, 169)": {
        "type": "Relation",
        "name": "increases",
        "span": [
            160,
            169
        ]
    },
    "(39, 214)": {
        "type": "Nested",
        "span": [
            39,
            214
        ]
    }
}
"""


def parse_chars(bels: list, errors: Errors) -> Tuple[CharLocs, Errors]:
    """Scan BEL string to map parens, quotes, commas

    Args:
        bels: bel string as an array of characters
        errors: list of error tuples ('<type>', '<msg>')

    Returns:
        (char_locs, errors): character locations and errors
    """
    pstack, qstack, nested_pstack = [], [], []
    parens, nested_parens, quotes, commas = {}, {}, {}, {}

    notquoted_flag = True

    for i, c in enumerate(bels):
        prior_char = i - 1
        # print('BEL', prior_char, b[prior_char])

        # Find starting quote
        if (c == '"' and bels[prior_char] != '\\' and len(qstack) == 0):
            qstack.append(i)
            notquoted_flag = False

        # Find closing quote
        elif c == '"' and bels[prior_char] != '\\':
            quotes[qstack.pop()] = i
            notquoted_flag = True

        # Find all escaped quotes outside of quoted string
        elif c == '"' and bels[prior_char] == '\\' and len(qstack) == 0:
            errors.append(('ERROR', f'Escaped quote outside of quoted string at location: {i - 1}', (i - 1, i - 1)))

        # Find all nested object opening parens
        elif notquoted_flag and c == '(' and bels[prior_char] == ' ':
            if len(nested_pstack) > 1:
                errors.append(('ERROR', f'More than one nested parenthesis or left parenthesis following a space character', (i, i)))

            nested_pstack.append(i)

        # Find all opening parens
        elif notquoted_flag and c == '(' and bels[prior_char] not in ['\\']:
            pstack.append(i)

        # Find all closing parens
        elif notquoted_flag and c == ')' and bels[prior_char] != '\\':
            if len(pstack):
                if len(pstack) > 1:
                    parens[pstack.pop()] = (i, 'child')
                else:
                    parens[pstack.pop()] = (i, 'top')
            elif len(nested_pstack):
                nested_parens[nested_pstack.pop()] = (i, 'top')
            else:
                errors.append(('ERROR', f'Missing left parenthesis for right parenthesis at location {i}', (i, i)))
        # Find comma outside of quoted string
        elif notquoted_flag and c == ',' and len(qstack) == 0:
            sparen = pstack[-1]
            if sparen not in commas:
                commas[sparen] = [i]
            else:
                commas[sparen].append(i)

    while len(pstack):
        errors.append(('ERROR', f'Missing right parenthesis for left parenthesis at location {pstack[-1]}', (pstack[-1], pstack[-1])))
        if len(pstack) > 1:
            parens[pstack.pop()] = (-1, 'child')
        else:
            parens[pstack.pop()] = (-1, 'top')

    while len(nested_pstack):
        errors.append(('ERROR', f'Missing right parenthesis for nested object left parenthesis at location {nested_pstack[-1]}', (nested_pstack[-1], nested_pstack[-1])))
        nested_parens[nested_pstack.pop()] = (-1, 'top')

    if len(qstack):
        missing_quote = qstack.pop()
        errors.append(('ERROR', f'Missing right quote for left quote at location {missing_quote}', (missing_quote, missing_quote)))

    return {
        'parens': parens,
        'nested_parens': nested_parens,
        'quotes': quotes,
        'commas': commas,
    }, errors


def parse_functions(bels: list, char_locs: CharLocs, parsed: Parsed, errors: Errors) -> Tuple[Parsed, Errors]:
    """Parse functions from BEL using paren, comma, quote character locations

    Args:
        bels: BEL string as list of chars
        char_locs: paren, comma, quote character locations
        errors: Any error messages generated during the parse

    Returns:
        (functions, errors): function names and locations and error messages
    """
    parens = char_locs['parens']

    # Handle partial top-level function name
    if not parens:
        bels_len = len(bels) - 1
        span = (0, bels_len)
        parsed[span] = {
            'name': ''.join(bels), 'type': 'Function',
            'span': span, 'name_span': (span),
            'function_level': 'top',
        }
        return parsed, errors

    for sp in sorted(parens):  # sp = starting paren, ep = ending_paren
        ep, function_level = parens[sp]

        # Functions can't have a space between function name and left paren
        if bels[sp - 1] == ' ':
            continue

        # look in front of start paren for function name
        for i in range(sp - 1, 0, -1):
            if bels[i] in [' ', ',', '(']:  # function name upstream boundary chars
                if i < sp - 1:
                    if ep == -1:
                        span = (i + 1, len(bels) - 1)
                    else:
                        span = (i + 1, ep)

                    parsed[span] = {'name': ''.join(bels[i + 1:sp]),
                        'type': 'Function', 'span': span,
                        'name_span': (i + 1, sp - 1), 'parens_span': (sp, ep),
                        'function_level': function_level,
                    }
                break
        else:
            if ep == -1:
                span = (0, len(bels) - 1)
            else:
                span = (0, ep)

            parsed[span] = {
                'name': ''.join(bels[0:sp]), 'type': 'Function',
                'span': span, 'name_span': (0, sp - 1), 'parens_span': (sp, ep),
                'function_level': function_level,
            }

    return parsed, errors


def parse_args(bels: list, char_locs: CharLocs, parsed: Parsed, errors: Errors) -> Tuple[Parsed, Errors]:
    """Parse arguments from functions

    Args:
        bels: BEL string as list of chars
        char_locs: char locations for parens, commas and quotes
        parsed: function locations
        errors: error messages

    Returns:
        (functions, errors): function and arg locations plus error messages
    """

    commas = char_locs['commas']

    # Process each span key in parsed from beginning
    for span in parsed:
        if parsed[span]['type'] != 'Function' or 'parens_span' not in parsed[span]:
            continue  # Skip if not argument-less
        sp, ep = parsed[span]['parens_span']

        # calculate args_end position
        if ep == -1:  # supports bel completion
            args_end = len(bels) - 1  # 1
        else:
            args_end = ep - 1  # 1

        # Parse arguments
        args = []
        arg_start = sp + 1
        each_arg_end_list = sorted([end - 1 for end in commas.get(sp, [])] + [args_end])
        for arg_end in each_arg_end_list:
            # log.debug(f'Arg_start: {arg_start}  Arg_end: {arg_end}')

            # Skip blanks at beginning of argument
            while arg_start < args_end and bels[arg_start] == ' ':
                arg_start += 1

            # Trim arg_end (e.g. HGNC:AKT1  , HGNC:EGF) - if there are spaces before comma
            trimmed_arg_end = arg_end
            while trimmed_arg_end > arg_start and bels[trimmed_arg_end] == ' ':
                trimmed_arg_end -= 1

            if trimmed_arg_end < arg_start:
                trimmed_arg_end = arg_start

            arg = ''.join(bels[arg_start:trimmed_arg_end + 1])

            # log.debug(f'Adding arg to args: {arg_start} {trimmed_arg_end}')
            args.append({'arg': arg, 'span': (arg_start, trimmed_arg_end)})
            arg_start = arg_end + 2

        parsed[span]['args'] = args

    return parsed, errors


def arg_types(parsed: Parsed, errors: Errors) -> Tuple[Parsed, Errors]:
    """Add argument types to parsed function data structure

    Args:
        parsed: function and arg locations in BEL string
        errors: error messages

    Returns:
        (parsed, errors): parsed, arguments with arg types plus error messages
    """

    func_pattern = re.compile('\s*[a-zA-Z]+\(')
    nsarg_pattern = re.compile('^\s*([A-Z]+):(.*?)\s*$')

    for span in parsed:
        if parsed[span]['type'] != 'Function' or 'parens_span' not in parsed[span]:
            continue

        for i, arg in enumerate(parsed[span]['args']):
            nsarg_matches = nsarg_pattern.match(arg['arg'])
            if func_pattern.match(arg['arg']):
                parsed[span]['args'][i].update({'type': 'Function'})
            elif nsarg_matches:
                (start, end) = arg['span']
                ns = nsarg_matches.group(1)
                ns_val = nsarg_matches.group(2)
                ns_span = nsarg_matches.span(1)
                ns_span = (ns_span[0] + start, ns_span[1] + start - 1)
                ns_val_span = nsarg_matches.span(2)
                ns_val_span = (ns_val_span[0] + start, ns_val_span[1] + start - 1)

                parsed[span]['args'][i].update({'type': 'NSArg', 'ns': ns, 'ns_span': ns_span, 'ns_val': ns_val, 'ns_val_span': ns_val_span})
            else:
                parsed[span]['args'][i].update({'type': 'StrArg'})

    return parsed, errors


def parse_relations(belstr: str, char_locs: CharLocs, parsed: Parsed, errors: Errors) -> Tuple[Parsed, Errors]:
    """Parse relations from BEL string

    Args:
        belstr: BEL string as one single string (not list of chars)
        char_locs: paren, comma and quote char locations
        parsed: data structure for parsed functions, relations, nested
        errors: error messages

    Returns:
        (parsed, errors):
    """
    quotes = char_locs['quotes']
    quoted_range = set([i for start, end in quotes.items() for i in range(start, end)])

    for match in relations_pattern_middle.finditer(belstr):
        (start, end) = match.span(1)
        log.debug(f'Relation-middle {match}')
        end = end - 1  # adjust end to match actual end character index
        if start != end:
            test_range = set(range(start, end))
        else:
            test_range = set(start)

        # Skip if relation overlaps with quoted string
        if test_range.intersection(quoted_range):
            continue

        span_key = (start, end)
        parsed[span_key] = {'type': 'Relation', 'name': match.group(1), 'span': (start, end)}

    for match in relations_pattern_end.finditer(belstr):
        (start, end) = match.span(1)
        log.debug(f'Relation-end {match}')
        end = end - 1  # adjust end to match actual end character index
        if start != end:
            test_range = set(range(start, end))
        else:
            test_range = set(start)

        # Skip if relation overlaps with quoted string
        if test_range.intersection(quoted_range):
            continue

        span_key = (start, end)
        parsed[span_key] = {'type': 'Relation', 'name': match.group(1), 'span': (start, end)}

    return parsed, errors


def parse_nested(bels: list, char_locs: CharLocs, parsed: Parsed, errors: Errors) -> Tuple[Parsed, Errors]:
    """ Parse nested BEL object """

    for sp in char_locs['nested_parens']:  # sp = start parenthesis, ep = end parenthesis
        ep, level = char_locs['nested_parens'][sp]
        if ep == -1:
            ep = len(bels) + 1
        parsed[(sp, ep)] = {'type': 'Nested', 'span': (sp, ep)}

    return parsed, errors


def dump_json(d: dict) -> None:
    """Dump json when using tuples for dictionary keys

    Have to convert tuples to strings to dump out as json
    """

    import json
    k = d.keys()
    v = d.values()
    k1 = [str(i) for i in k]
    print(json.dumps(dict(zip(*[k1, v])), indent=4))


def collect_spans(ast: AST) -> List[Tuple[str, Tuple[int, int]]]:
    """Collect flattened list of spans of BEL syntax types

    Provide simple list of BEL syntax type spans for highlighting.
    Function names, NSargs, NS prefix, NS value and StrArgs will be
    tagged.

    Args:
        ast: AST of BEL assertion

    Returns:
        List[Tuple[str, Tuple[int, int]]]: list of span objects (<type>, (<start>, <end>))
    """

    spans = []

    if ast.get('subject', False):
        spans.extend(collect_spans(ast['subject']))

    if ast.get('object', False):
        spans.extend(collect_spans(ast['object']))

    if ast.get('nested', False):
        spans.extend(collect_spans(ast['nested']))

    if ast.get('function', False):
        log.info(f'Processing function')
        spans.append(('Function', ast['function']['name_span']))
        log.info(f'Spans: {spans}')

    if ast.get('args', False):
        for idx, arg in enumerate(ast['args']):
            log.info(f'Arg  {arg}')

            if arg.get('function', False):
                log.info(f'Recursing on arg function')
                results = collect_spans(arg)
                log.info(f'Results {results}')
                spans.extend(results)  # Recurse arg function
            elif arg.get('nsarg', False):
                log.info(f'Processing NSArg   Arg {arg}')
                spans.append(('NSArg', arg['span']))
                spans.append(('NSPrefix', arg['nsarg']['ns_span']))
                spans.append(('NSVal', arg['nsarg']['ns_val_span']))
            elif arg['type'] == 'StrArg':
                spans.append(('StrArg', arg['span']))

    log.debug(f'Spans: {spans}')
    return spans

    # max_idx = 0
    # for key in parsed:
    #     if parsed[key]['type'] == 'Function':
    #         spans.append(('Function', parsed[key]['name_span']))
    #         if parsed[key]['name_span'][1] > max_idx:
    #             max_idx = parsed[key]['name_span'][1]

    #         for arg in parsed[key]['args']:
    #             if arg['type'] == 'NSArg':
    #                 spans.append(('NSArg', arg['span']))
    #                 spans.append(('Prefix', arg['ns_span']))
    #                 spans.append(('Value', arg['ns_val_span']))
    #                 if arg['ns_val_span'][1] > max_idx:
    #                     max_idx = arg['ns_val_span'][1]
    #             if arg['type'] == 'StrArg':
    #                 spans.append(('StrArg', arg['span']))
    #                 if arg['span'][1] > max_idx:
    #                     max_idx = arg['span'][1]
    #     elif parsed[key]['type'] == 'Relation':
    #         spans.append(('Relation', parsed[key]['span']))

    #     elif parsed[key]['type'] == 'Nested':
    #         spans.append(('Nested', parsed[key]['span']))


def print_spans(spans, max_idx: int) -> None:
    """Quick test to show how character spans match original BEL String

    Mostly for debugging purposes
    """

    bel_spans = [' '] * (max_idx + 3)
    for val, span in spans:
        if val in ['Nested', 'NSArg']:
            continue
        for i in range(span[0], span[1] + 1):
            bel_spans[i] = val[0]

    print(''.join(bel_spans))

    # Add second layer for Nested Objects if available
    bel_spans = [' '] * (max_idx + 3)
    for val, span in spans:
        if val not in ['Nested']:
            continue
        for i in range(span[0], span[1] + 1):
            bel_spans[i] = val[0]

    print(''.join(bel_spans))


def parsed_function_to_ast(parsed: Parsed, parsed_key):
    """Create AST for top-level functions"""

    sub = parsed[parsed_key]

    subtree = {
        'type': 'Function',
        'span': sub['span'],
        'function': {
            'name': sub['name'],
            'name_span': sub['name_span'],
            'parens_span': sub.get('parens_span', []),
        }
    }

    args = []
    for arg in parsed[parsed_key].get('args', []):

        # pdb.set_trace()

        if arg['type'] == 'Function':
            args.append(parsed_function_to_ast(parsed, arg['span']))
        elif arg['type'] == 'NSArg':
            args.append({
                "arg": arg['arg'],
                "type": arg['type'],
                'span': arg['span'],
                'nsarg': {
                    "ns": arg['ns'],
                    "ns_val": arg['ns_val'],
                    "ns_span": arg['ns_span'],
                    "ns_val_span": arg['ns_val_span'],
                }
            })
        elif arg['type'] == 'StrArg':
            args.append({
                "arg": arg['arg'],
                "type": arg['type'],
                'span': arg['span'],
            })

    subtree['args'] = copy.deepcopy(args)

    return subtree


def parsed_top_level_errors(parsed, errors, component_type: str = '') -> Errors:
    """Check full parse for errors

    Args:
        parsed:
        errors:
        component_type: Empty string or 'subject' or 'object' to indicate that we
            are parsing the subject or object field input
    """

    # Error check
    fn_cnt = 0
    rel_cnt = 0
    nested_cnt = 0
    for key in parsed:
        if parsed[key]['type'] == 'Function':
            fn_cnt += 1
        if parsed[key]['type'] == 'Relation':
            rel_cnt += 1
        if parsed[key]['type'] == 'Nested':
            nested_cnt += 1

    if not component_type:
        if nested_cnt > 1:
            errors.append(('Error', 'Too many nested objects - can only have one per BEL Assertion'))

        if nested_cnt:
            if rel_cnt > 2:
                errors.append(('Error', 'Too many relations - can only have two in a nested BEL Assertion'))
            elif fn_cnt > 4:
                errors.append(('Error', 'Too many BEL subject and object candidates'))

        else:
            if rel_cnt > 1:
                errors.append(('Error', 'Too many relations - can only have one in a BEL Assertion'))
            elif fn_cnt > 2:
                errors.append(('Error', 'Too many BEL subject and object candidates'))

    elif component_type == 'subject':
        if rel_cnt > 0:
            errors.append(('Error', 'Too many relations - cannot have any in a BEL Subject'))
        elif fn_cnt > 1:
            errors.append(('Error', 'Too many BEL subject candidates - can only have one'))

    elif component_type == 'object':
        if nested_cnt:
            if rel_cnt > 1:
                errors.append(('Error', 'Too many relations - can only have one in a nested BEL object'))
            elif fn_cnt > 2:
                errors.append(('Error', 'Too many BEL subject and object candidates in a nested BEL object'))
        else:
            if rel_cnt > 0:
                errors.append(('Error', 'Too many relations - cannot have any in a BEL Subject'))
            elif fn_cnt > 1:
                errors.append(('Error', 'Too many BEL subject candidates - can only have one'))

    return errors


def parsed_to_ast(parsed: Parsed, errors: Errors, component_type: str = ''):
    """Convert parsed data struct to AST dictionary

    Args:
        parsed:
        errors:
        component_type: Empty string or 'subject' or 'object' to indicate that we
            are parsing the subject or object field input
    """

    ast = {}
    sorted_keys = sorted(parsed.keys())

    log.debug(f'To AST {dump_json(parsed)}')

    # Setup top-level tree
    for key in sorted_keys:
        if parsed[key]['type'] == 'Nested':
            nested_component_stack = ['subject', 'object']

    if component_type:
        component_stack = [component_type]
    else:
        component_stack = ['subject', 'object']

    for key in sorted_keys:
        if parsed[key]['type'] == 'Function' and parsed[key]['function_level'] == 'top':
            ast[component_stack.pop(0)] = parsed_function_to_ast(parsed, key)
        elif parsed[key]['type'] == 'Relation' and 'relation' not in ast:
            ast['relation'] = {
                'name': parsed[key]['name'],
                'type': 'Relation',
                'span': key,
            }
        elif parsed[key]['type'] == 'Nested':
            ast['nested'] = {}
            for nested_key in sorted_keys:
                if nested_key <= key:
                    continue

                if parsed[nested_key]['type'] == 'Function' and parsed[nested_key]['function_level'] == 'top':
                    ast['nested'][nested_component_stack.pop(0)] = parsed_function_to_ast(parsed, nested_key)
                elif parsed[nested_key]['type'] == 'Relation' and 'relation' not in ast['nested']:
                    ast['nested']['relation'] = {
                        'name': parsed[nested_key]['name'],
                        'type': 'Relation',
                        'span': parsed[nested_key]['span'],
                    }

            return ast, errors

    return ast, errors


def get_ast_dict(belstr, component_type: str = ''):
    """Convert BEL string to AST dictionary

    Args:
        belstr: BEL string
        component_type: Empty string or 'subject' or 'object' to indicate that we
            are parsing the subject or object field input
    """

    errors = []
    parsed = {}
    bels = list(belstr)
    char_locs, errors = parse_chars(bels, errors)
    parsed, errors = parse_functions(belstr, char_locs, parsed, errors)
    parsed, errors = parse_args(bels, char_locs, parsed, errors)
    parsed, errors = arg_types(parsed, errors)
    parsed, errors = parse_relations(belstr, char_locs, parsed, errors)
    parsed, errors = parse_nested(bels, char_locs, parsed, errors)
    errors = parsed_top_level_errors(parsed, errors)

    ast, errors = parsed_to_ast(parsed, errors, component_type=component_type)

    return ast, errors


def main():

    import json

    belstr = 'activity(proteinAbundance(SFAM:"GSK3 \"Family"), molecularActivity(DEFAULT:kin))'
    belstr = 'proteinAbundance(HGNC:VHL) increases (proteinAbundance(HGNC:TNF) increases biologicalProcess(GOBP:"cell death"))'
    belstr = 'complexAbundance(proteinAbundance(HGNC:VHL), proteinAbundance(HGNC:PRKCZ))'
    belstr = 'activity(proteinAbundance(SFAM:"PRKA Family"), molecularActivity(DEF:kin)) directlyIncreases proteinAbundance(SFAM:"PDE4 Long Family", proteinModification(Ph, S, 20))'  # made up (added the 20 in the pmod)
    belstr = 'proteinAbundance(HGNC:VEGFA) increases (compositeAbundance(proteinAbundance(HGNC:ITGB1), proteinAbundance(HGNC:PRKCA, ma(kin))) increases biologicalProcess(GO:\"cell-matrix adhesion\"))'
    belstr = 'complex(p(HGNC:AKT1))'
    # belstr = 'p(fus(HGNC:EGF, 20, '
    # belstr = 'pa'

    ast, errors = get_ast_dict(belstr)
    print('AST:\n', json.dumps(ast, indent=4))

    spans = collect_spans(ast)

    print('\n\nBELStr', belstr)
    print('Spans:\n', json.dumps(spans, indent=4))

    # print('AST:\n', json.dumps(ast, indent=4))


if __name__ == '__main__':
    main()


def walk_ast(ast):
    pass
    # https://stackoverflow.com/questions/12507206/python-recommended-way-to-walk-complex-dictionary-structures-imported-from-json
    # Recursively process tree - add parents as list passed in recursive function
    #     (first item in list is root, second one-level down, etc)
    #  https://ruslanspivak.com/lsbasi-part7/
    # https://stackoverflow.com/questions/37772704/how-to-walk-this-tree-consisting-of-lists-tuples-and-strings

    # https://stackoverflow.com/questions/6340351/python-iterating-through-list-of-list
    # def traverse(o, tree_types=(list, tuple)):
    #     if isinstance(o, tree_types):
    #         for value in o:
    #             for subvalue in traverse(value, tree_types):
    #                 yield subvalue
    #     else:
    #         yield o

    # https://www.andreas-dewes.de/articles/abstract-syntax-trees-in-python.html


