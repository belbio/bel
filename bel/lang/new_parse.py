#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Completion notes
1. Won't complete inside of a quote.  If there are mis-matched quotes
   it will break completions
2. terms upstream of a '(' are functions/modifiers
3. commas separate arguments of upstream function


"""

import os
import re
import yaml
import json
import timy
import itertools

import logging
import logging.config

from bel_db.Config import config

logging.config.dictConfig(config['logging'])
log = logging.getLogger(__name__)

start_arg_chars = ['(', ',']
end_arg_chars = [')', ',']

relations_pattern = re.compile('\)\s+([a-zA-Z=->\|:]+)\s+([\w(]+)')


def parse_chars(bels, errors):
    pstack, qstack = [], []
    parens, quotes, commas = {}, {}, {}
    bad_escaped_quotes = []

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
            errors.append(('ERROR', f'Escaped quote outside of quoted string at location: {i - 1}'))

        # Find all opening parens
        elif notquoted_flag and c == '(' and bels[prior_char] not in ['\\', ' ']:
            pstack.append(i)

        # Find all closing parens
        elif notquoted_flag and c == ')' and bels[prior_char] != '\\':
            if len(pstack):
                if len(pstack) > 1:
                    parens[pstack.pop()] = (i, 'child')
                else:
                    parens[pstack.pop()] = (i, 'top')
            else:
                errors.append(('ERROR', f'Missing left parenthesis for right parenthesis at location {i}'))
        # Find comma outside of quoted string
        elif notquoted_flag and c == ',' and len(qstack) == 0:
            sparen = pstack[-1]
            if sparen not in commas:
                commas[sparen] = [i]
            else:
                commas[sparen].append(i)

    while len(pstack):
        errors.append(('ERROR', f'Missing right parenthesis for left parenthesis at location {pstack[-1]}'))
        if len(pstack) > 1:
            parens[pstack.pop()] = (-1, 'child')
        else:
            parens[pstack.pop()] = (-1, 'top')

    if len(qstack):
        errors.append(('ERROR', f'Missing right quote for left quote at location {qstack.pop()}'))

    return {
        'parens': parens,
        'quotes': quotes,
        'commas': commas,
        'bad_quotes': bad_escaped_quotes,
    }, errors


def parse_functions(bels, char_locs, errors):
    parens = char_locs['parens']
    functions = {}

    for sp in sorted(parens):
        ep, function_level = parens[sp]

        # look in front of start paren for function name
        for i in range(sp - 1, 0, -1):
            if bels[i] in [' ', ',', '(']:  # function name boundary chars
                if i < sp - 1:
                    span = (i + 1, ep)
                    functions[(i + 1, ep)] = {'name': ''.join(bels[i + 1:sp]),
                        'type': 'Function', 'span': span,
                        'name_span': (i + 1, sp - 1), 'parens_span': (sp, ep),
                        'function_level': function_level,
                    }
                break
        else:
            span = (0, ep)
            functions[span] = {'name': ''.join(bels[0:sp]), 'type': 'Function',
                'span': span, 'name_span': (0, sp - 1), 'parens_span': (sp, ep),
                'function_level': function_level,
            }

    return functions, errors


def parse_args(bels, char_locs, functions, errors):

    commas = char_locs['commas']

    for span in functions:
        sp, ep = functions[span]['parens_span']
        if ep == -1:  # supports bel completion
            function_end = len(bels) + 1
        else:
            function_end = ep

        args = []
        if sp in commas and commas[sp]:
            start = sp + 1
            for comma in commas[sp]:
                while start < function_end - 1 and bels[start] == ' ':
                    start += 1

                if start > comma:
                    break
                arg = ''.join(bels[start:comma])
                args.append({'arg': arg, 'span': (start, comma - 1)})
                start = comma + 1

            while start < function_end - 1 and bels[start] == ' ':
                start += 1

            arg = ''.join(bels[start:function_end])
            args.append({'arg': arg, 'span': (start, function_end - 1)})
        else:
            start = sp + 1
            while start < function_end - 1 and bels[start] == ' ':
                start += 1

            arg = ''.join(bels[start:function_end])
            args.append({'arg': arg, 'span': (start, function_end - 1)})

        functions[span]['args'] = args

    return functions, errors


def arg_types(functions, errors):

    func_pattern = re.compile('\s*[a-zA-Z]+\(')
    nsarg_pattern = re.compile('^\s*([A-Z]+):(.*?)\s*$')

    for span in functions:
        for i, arg in enumerate(functions[span]['args']):
            nsarg_matches = nsarg_pattern.match(arg['arg'])
            if func_pattern.match(arg['arg']):
                functions[span]['args'][i].update({'type': 'Function'})
            elif nsarg_matches:
                (start, end) = arg['span']
                ns = nsarg_matches.group(1)
                ns_val = nsarg_matches.group(2)
                ns_span = nsarg_matches.span(1)
                ns_span = (ns_span[0] + start, ns_span[1] + start - 1)
                ns_val_span = nsarg_matches.span(2)
                ns_val_span = (ns_val_span[0] + start, ns_val_span[1] + start - 1)

                functions[span]['args'][i].update({'type': 'NSArg', 'ns': ns, 'ns_span': ns_span, 'ns_val': ns_val, 'ns_val_span': ns_val_span})
            else:
                functions[span]['args'][i].update({'type': 'StrArg'})

    return functions, errors


def parse_relations(bel, char_locs, errors):

    quotes = char_locs['quotes']
    quoted_range = set([i for start, end in quotes.items() for i in range(start, end)])

    relations = []
    for match in relations_pattern.finditer(bel):
        (start, end) = match.span(1)
        if start != end:
            test_range = set(range(start, end))
        else:
            test_range = set(start)

        # Skip if relation overlaps with quoted string
        if test_range.intersection(quoted_range):
            continue

        relations.append({'name': match.group(1), 'span': (start, end)})

    return relations, errors


def dump_json(dic):
    import json
    k = dic.keys()
    v = dic.values()
    k1 = [str(i) for i in k]
    print(json.dumps(dict(zip(*[k1, v])), indent=4))


def collect_spans(functions):

    spans = []
    max_idx = 0
    for f in functions:
        if 'name_span' in functions[f]:
            spans.append(('F', functions[f]['name_span']))
            if functions[f]['name_span'][1] > max_idx:
                max_idx = functions[f]['name_span'][1]
        for arg in functions[f]['args']:
            if arg['type'] == 'NSArg':
                spans.append(('N', arg['ns_span']))
                spans.append(('V', arg['ns_val_span']))
                if arg['ns_val_span'][1] > max_idx:
                    max_idx = arg['ns_val_span'][1]
            if arg['type'] == 'StrArg':
                spans.append(('S', arg['span']))
                if arg['span'][1] > max_idx:
                    max_idx = arg['span'][1]

    return spans, max_idx


def print_spans(spans, max_idx):

    bel_spans = [' '] * (max_idx + 1)
    for val, span in spans:
        for i in range(span[0], span[1] + 1):
            bel_spans[i] = val

    print(''.join(bel_spans))


def function_tree(tree, function, functions):

    pass


# TODO - finish
def create_ast(functions, relations, subj_or_object=None):

    ast = {}
    if subj_or_object == 'object' and relations:
        return ast, [('ERROR', 'Cannot have full BEL assertion in subject - only object')]

    ftree = {}
    for span in functions:
        pass


def parse_function_string(bel):

    errors = []
    bels = list(bel)
    char_locs, errors = parse_chars(bels, errors)
    functions, errors = parse_functions(bel, char_locs, errors)
    functions, errors = parse_args(bels, char_locs, functions, errors)
    functions, errors = arg_types(functions, errors)

    return functions, errors


def parse_stmt_string(bel):

    errors = []
    bels = list(bel)
    char_locs, errors = parse_chars(bels, errors)
    functions, errors = parse_functions(bel, char_locs, errors)
    functions, errors = parse_args(bels, char_locs, functions, errors)
    functions, errors = arg_types(functions, errors)
    relations, errors = parse_relations(bel, char_locs, errors)
    # dump_json(functions)
    ast = create_ast(functions, relations)
    # check_spans(bel, functions)
    return ast, errors


def main():

    bel = 'activity(proteinAbundance(SFAM:"GSK3 \"Family"), molecularActivity(DEFAULT:kin))'
    bel = 'proteinAbundance(HGNC:VHL) increases (proteinAbundance(HGNC:TNF) increases biologicalProcess(GOBP:"cell death"))'
    bel = 'complexAbundance(proteinAbundance(HGNC:VHL), proteinAbundance(HGNC:PRKCZ))'
    bel = 'activity(proteinAbundance(SFAM:"PRKA Family"), molecularActivity(DEF:kin)) directlyIncreases proteinAbundance(SFAM:"PDE4 Long Family", proteinModification(Ph, S, 20))'  # made up (added the 20 in the pmod)
    # bel = 'p(fus(HGNC:EGF, 20, '
    # bel = 'p('
    with timy.Timer() as timer:
        functions, errors = parse_function_string(bel)
        spans, max_idx = collect_spans(functions)
        # print(bel)
        # print_spans(spans, max_idx)
        # dump_json(functions)


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


