#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
This file contains tools used in our parser for BEL statements.
"""

import collections
import math
import os
import pprint
import random
import re
import string

import yaml
from bel_lang.exceptions import *
from bel_lang.objects import *


###################
# STATEMENT TOOLS #
###################


class InvalidStatementObject(object):

    def __init__(self, s, r, o):
        self.subject = s
        self.relationship = r
        self.object = o
        self.string_form = self.to_string_form(s, r, o)

    def to_string_form(self, s, r, o):

        sub = self.stmt_creation_decode(s)
        rlt = r
        obj = self.stmt_creation_decode(o)

        return '{} {} {}'.format(sub, rlt, obj)

    def stmt_creation_decode(self, ast_dict):

        arg_type = ast_dict.get('type', False)
        arg_value = ast_dict.get('value', False)

        if arg_type == 'Function':
            f_name = ast_dict.get('name', None)

            tmp = self.stmt_creation_decode(arg_value[0])

            for param in arg_value[1:]:
                tmp += ', {}'.format(self.stmt_creation_decode(param))

            return '{}({})'.format(f_name, tmp)

        elif arg_type == 'String':
            return arg_value
        elif arg_type == 'Entity':
            return arg_value
        else:
            return 'UNK'


def create_invalid(bel_obj, count, max_params):

    list_of_statement_objs = []

    for _ in range(count):
        stmt_obj = make_statement(bel_obj, max_params)
        list_of_statement_objs.append(stmt_obj)

    return list_of_statement_objs


def make_statement(bel_obj, max_params):

    s = choose_and_make_function(bel_obj, max_params)
    r = choose_rand_relationship(bel_obj.relationships)
    o = choose_and_make_function(bel_obj, max_params)

    return InvalidStatementObject(s, r, o)


def choose_and_make_function(bel_obj, max_params):

    full_func = {'name': choose_rand_function(bel_obj.function_signatures), 'type': 'Function', 'value': []}

    num_args = random.randint(1, max_params)  # how many args to have
    for _ in range(num_args):

        t = random.choice(['Entity', 'String', 'Function'])
        arg = {'type': t}

        if t == 'Entity':
            arg['value'] = random_namespace_param()
        elif t == 'String':
            arg['value'] = random_quoted_string()
        elif t == 'Function':
            arg = choose_and_make_function(bel_obj, max_params)
        else:
            pass

        full_func['value'].append(arg)

    return full_func


def func_name_translate(bel_obj):
    translated = {}

    yaml_dict = bel_obj.yaml_dict

    for fn in yaml_dict.get('functions', []):
        f_name = fn.get('name', 'unknown')
        f_abbr = fn.get('abbreviation', 'unknown')
        translated[f_abbr] = f_name
        translated[f_name] = f_abbr

    for m_fn in yaml_dict.get('modifier_functions', []):
        mf_name = m_fn.get('name', 'unknown')
        mf_abbr = m_fn.get('abbreviation', 'unknown')
        translated[mf_abbr] = mf_name
        translated[mf_name] = mf_abbr

    return translated


def get_all_relationships(bel_obj):

    yaml_dict = bel_obj.yaml_dict

    relationships = set()

    for relationship in yaml_dict.get('relationships', []):
        r_name = relationship.get('name', None)
        r_abbr = relationship.get('abbreviation', None)

        relationships.add(r_name)
        relationships.add(r_abbr)

    return list(relationships)


def get_all_function_signatures(bel_obj):
    yaml_dict = bel_obj.yaml_dict

    signature_dict = {}

    for func in yaml_dict.get('function_signatures', []):  # for each function in the yaml function signatures...
        f_name = func.get('name', 'unknown')  # get the name of the function in yaml
        f_sigs = func.get('signatures', [])  # get the signatures of the function
        signature_dict[f_name] = f_sigs  # set function name as key, and yaml's f_sigs as the value for this key

        for valid_sig in f_sigs:  # for each signature from signatures...
            params = valid_sig.get('parameters', None)  # get the parameter types of this signature
            required_params = collections.OrderedDict()  # required param types list (must be ordered)
            optional_params = collections.OrderedDict()  # optional param types list (does not need to be ordered)

            for par in params:  # for each type in parameter types
                par_type = par.get('type', 'Unknown')  # get the type name
                optional = par.get('optional', False)  # get the optional boolean
                multiple = par.get('multiple', False)  # get the multiple boolean

                # param is REQUIRED AND SINGULAR
                # set the value as the number of times this type can appear
                if not optional and not multiple:
                    required_params[par_type] = required_params.get(par_type, 0) + 1

                # param is REQUIRED AND MULTIPLE
                # set the value to infinity as we'll always have 1 or more of this type
                elif not optional and multiple:
                    required_params[par_type] = math.inf

                # param is OPTIONAL AND SINGULAR
                # set the value as the number of times this type can appear
                elif optional and not multiple:
                    optional_params[par_type] = optional_params.get(par_type, 0) + 1

                # param is OPTIONAL AND MULTIPLE
                # set the value to infinity as we'll always have 0 or more of this type
                else:
                    optional_params[par_type] = math.inf

            # add these two OrderedDicts as key/values within valid_sig so we can refer to them later on
            valid_sig['required'] = required_params
            valid_sig['optional'] = optional_params

        # clone the value of f_name into its respective abbreviation key
        # e.g. signature_dict[activity] == signature_dict[act]; signature_dict[pathology] == signature_dict[path]
        signature_dict[bel_obj.translate_terms[f_name]] = f_sigs

    return signature_dict


def get_all_primary_funcs(bel_obj):

    primary = []
    fns = bel_obj.yaml_dict.get('functions', [])
    for fn in fns:
        primary.append(fn.get('name', None))
        primary.append(fn.get('abbreviation', None))

    return primary


def get_all_modifier_funcs(bel_obj):

    modifier = []
    mfns = bel_obj.yaml_dict.get('modifier_functions', [])
    for mfn in mfns:
        modifier.append(mfn.get('name', None))
        modifier.append(mfn.get('abbreviation', None))

    return modifier


def get_all_computed_sigs(bel_obj):
    d = bel_obj.yaml_dict
    sigs = d.get('computed_signatures', [])

    # give each term's alternative name the same computed rule
    for initial_name in list(sigs):
        try:
            alternate = bel_obj.translate_terms[initial_name]
            sigs[alternate] = sigs[initial_name]
        except KeyError:
            continue

    return sigs


def get_all_computed_funcs(bel_obj):
    comp_sigs = bel_obj.computed_sigs
    comp_fns = []

    for f in comp_sigs:
        if f in bel_obj.primary_functions:
            comp_fns.append(f)
            comp_fns.append(bel_obj.translate_terms[f])

    return list(set(comp_fns))


def get_all_computed_mfuncs(bel_obj):
    comp_sigs = bel_obj.computed_sigs
    comp_mfns = []

    for f in comp_sigs:
        if f in bel_obj.modifier_functions:
            comp_mfns.append(f)
            comp_mfns.append(bel_obj.translate_terms[f])

    return list(set(comp_mfns))


def choose_rand_relationship(relationships):

    return random.choice(relationships)


def choose_rand_function(func_sigs):

    return random.choice(list(func_sigs.keys()))


def random_namespace_param():
    ascii_letters = string.ascii_uppercase + string.ascii_lowercase
    ascii_alphanumeric_upper = string.ascii_uppercase + string.digits
    ascii_alphanumeric = ascii_letters + string.digits

    i = random.randint(2, 5)
    rand_nspace = 'NS' + ''.join(random.choice(ascii_alphanumeric_upper) for _ in range(i))

    j = random.randint(5, 25)

    if random.random() < 0.5:  # quoted nsvalue
        rand_nsvalue = ''.join(random.choice(ascii_alphanumeric + ' \' - , + /.') for _ in range(j))
        rand_nsvalue = '"{}"'.format(rand_nsvalue)
    else:  # unquoted nsvalue
        rand_nsvalue = ''.join(random.choice(ascii_alphanumeric) for _ in range(j))

    return '{}: {}'.format(rand_nspace, rand_nsvalue)


def random_quoted_string():
    ascii_letters = string.ascii_uppercase + string.ascii_lowercase
    ascii_alphanumeric = ascii_letters + string.digits

    j = random.randint(5, 25)

    rand_nsvalue = ''.join(random.choice(ascii_alphanumeric + ' \' - , + /.') for _ in range(j))
    return '"{}"'.format(rand_nsvalue)


def decode(ast_dict):
    for key, value in ast_dict.items():
        if key == 'ns_arg':
            return '{}:{}'.format(value['nspace'], value['ns_value'])
        elif key == 'str_arg':
            return '{}'.format(value)
        elif key == 'function':
            tmp = []
            f_name = value
            f_args = ast_dict.get('function_args', [])

            for arg_dict in f_args:
                tmp.append(decode(arg_dict))

            return '{}({})'.format(f_name, ', '.join(tmp))
        elif key == 'm_function':
            tmp = []
            m_f_name = value
            m_f_args = ast_dict.get('m_function_args', [])

            for m_arg_dict in m_f_args:
                tmp.append(decode(m_arg_dict))

            return '{}({})'.format(m_f_name, ', '.join(tmp))
        elif key == 'bel_statement':
            new_ast = value

            s = new_ast.get('subject', None)
            r = new_ast.get('relationship', None)
            o = new_ast.get('object', None)

            if r is None:  # if no relationship, this means only subject is present
                sub = decode(s)
                final = '({})'.format(sub)
            else:  # else the full form BEL statement with subject, relationship, and object are present
                sub = decode(s)
                obj = decode(o)
                final = '({} {} {})'.format(sub, r, obj)

                return final
        else:
            pass


# def get_computable_function_dicts(ast_dict, bel_obj):
#
#     computables = []
#
#     for item_type, item_value in ast_dict.items():
#         if item_type in ['function', 'm_function']:  # this item is a function or m_function
#
#             computable = {
#                 'f_type': function_type,
#                 'full': full,
#                 'fn_name': function_name
#             }
#
#             print(function_name)
#             pprint.pprint(arguments)
#             print(full)
#             print()
#             print()
#
#             for arg in arguments:
#                 get_computable_function_dicts(arg, bel_obj)
#
#         elif item_type == 'bel_statment':
#             print('we reached a BEL statment.')
#             pass
#
#         else:
#             return []
#
#     return computables


def compute(ast_dict, bel_obj, parent_info=None):

    computed_object = {}
    computed = []

    for func_type, func_name in ast_dict.items():
        if func_type in ['function', 'm_function']:  # this item is a function or m_function

            if parent_info is None:
                parent_info = {}
            computable = False  # default to False until we know it needs to be computed

            func_alternate_name = bel_obj.translate_terms[func_name]
            func_object_full = ast_dict.asjson()

            print('{}FUNC FULL: {}{}'.format(Colors.RED, func_object_full, Colors.END))

            tmp_fn_obj = Function('primary', func_name, func_alternate_name)
            tmp_fn_obj.set_full_string(decode(ast_dict))

            if func_type == 'function':  # this is a primary function
                tmp_fn_obj_args = ast_dict.get('function_args', None)
            else:  # else must be a modifier function
                tmp_fn_obj.change_type('modifier')
                tmp_fn_obj_args = ast_dict.get('m_function_args', None)

            # for each argument in tmp_fn_obj_args, add it to our function object using add_args_to_compute_obj()
            add_args_to_compute_obj(bel_obj, tmp_fn_obj, tmp_fn_obj_args)

            print('\n{}'.format(tmp_fn_obj))
            pprint.pprint(vars(tmp_fn_obj))





            # print('\n{}'.format(tmp_fn_obj))
            # pprint.pprint(vars(tmp_fn_obj))
            #
            # for a in tmp_fn_obj.args:
            #     print('\n{}'.format(a))
            #     pprint.pprint(vars(a))

            exit()
            new_func_params = simple_params(func_params, bel_obj)

            print('FUNCTION: {}'.format(func_name))
            print('FUNCTION PARAMS:')
            pprint.pprint(new_func_params)

            new_parent_info = {
                'parent_type': func_type,
                'parent_name': func_name,
                'parent_full': func_object_full,
                'parent_params': func_params
            }

            if func_name in bel_obj.computed_funcs or func_name in bel_obj.computed_mfuncs:
                # start computing in here
                computable = True
                sig_to_use = bel_obj.computed_sigs[func_name]
                sub_rule = sig_to_use.get('subject', None)
                effect_rule = sig_to_use.get('relationship', None)
                obj_rule = sig_to_use.get('object', None)

                computable_info = {
                    'f_type': func_type,
                    'full': func_object_full,
                    'fn_name': func_name,
                    'p_name': parent_info.get('parent_name', ''),
                    'p_full': parent_info.get('parent_full', ''),
                    'p_parameters': parent_info.get('parent_params', ''),
                    'sig_to_use': sig_to_use
                }

                # extract subject and object params given rules
                subjects_from_rule = extract_params_from_rule(sub_rule, func_params, computable_info)
                objects_from_rule = extract_params_from_rule(obj_rule, func_params, computable_info)

                # print('SUBJECTS FROM RULE -------------------------------------------------')
                # print(subjects_from_rule)
                # print('-------------------------------------------------')
                #
                # print('OBJECTS FROM RULE -------------------------------------------------')
                # print(objects_from_rule)
                # print('-------------------------------------------------')

                for sub_comp in subjects_from_rule:
                    for obj_comp in objects_from_rule:
                        comp_string = '{} {} {}'.format(sub_comp, effect_rule, obj_comp)
                        computed_object = comp_string

                        computed_object = {
                            'subject': 'test-sub',
                            'effect': effect_rule,
                            'object': 'test-obj'
                        }

                        if computable:
                            computed.append(computed_object)
                        else:
                            pass

                # computed_object = {
                #     'sub_rule': sub_rule,
                #     'effect_rule': effect_rule,
                #     'obj_rule': obj_rule
                # }

            # if computable:
            #     computed.append(computed_object)
            # else:
            #     pass

            # then send each parameter back to compute() for computation
            for parameter in func_params:
                tmp_list = compute(parameter, bel_obj, parent_info=new_parent_info)
                computed.extend(tmp_list)

    return computed


def add_args_to_compute_obj(our_bel_obj, our_obj, our_obj_args):

    tmp_all_args_objs = []

    for argument in our_obj_args:

        f_args = []
        tmp_arg_obj = None

        if 'function' in argument:
            f_name = argument.get('function', None)
            f_alt_name = our_bel_obj.translate_terms[f_name]
            f_parent = our_obj
            f_args = argument.get('function_args', [])

            tmp_arg_obj = Function('primary', f_name, f_alt_name, parent_function=f_parent)

        elif 'm_function' in argument:
            f_name = argument.get('m_function', None)
            f_alt_name = our_bel_obj.translate_terms[f_name]
            f_parent = our_obj
            f_args = argument.get('m_function_args', [])

            tmp_arg_obj = Function('modifier', f_name, f_alt_name, parent_function=f_parent)

        elif 'ns_arg' in argument:
            ns = argument['ns_arg']['nspace']
            nsv = argument['ns_arg']['ns_value']
            ns_parent = our_obj

            tmp_arg_obj = NSParam(ns, nsv, ns_parent)

        elif 'str_arg' in argument:
            sv = argument.get('str_arg', None)
            sv_parent = our_obj

            tmp_arg_obj = StrParam(sv, sv_parent)

        else:
            continue

        if f_args:
            add_args_to_compute_obj(our_bel_obj, tmp_arg_obj, f_args)

        if tmp_arg_obj is not None:
            tmp_arg_obj.set_full_string(decode(argument))
            our_obj.add_argument(tmp_arg_obj)
            tmp_all_args_objs.append(tmp_arg_obj)

    # nested loop to add siblings to each arg. exclude the arg itself as its own sibling by ignoring if index match.
    for idx, arg_obj in enumerate(tmp_all_args_objs):
        for sibling_idx, sibling_arg_obj in enumerate(tmp_all_args_objs):

            if idx == sibling_idx:
                continue
            else:
                arg_obj.add_sibling(sibling_arg_obj)

        print('\n{}'.format(arg_obj))
        pprint.pprint(vars(arg_obj))

    return


def simple_params(params, bel_obj):

    new_params = []

    for p in params:

        if 'function' in p:
            obj_type = 'function'
            f_type = 'primary'
            obj = {
                'name': p['function'],
                'type': f_type,
                'alternate': bel_obj.translate_terms[p['function']],
                'full_string': decode(p),
                'params': simple_params(p['function_args'], bel_obj)
            }
        elif 'm_function' in p:
            obj_type = 'function'
            f_type = 'modifier'
            obj = {
                'name': p['m_function'],
                'type': f_type,
                'alternate': bel_obj.translate_terms[p['m_function']],
                'full_string': decode(p),
                'params': simple_params(p['m_function_args'], bel_obj)
            }
        elif 'ns_arg' in p:
            obj_type = 'ns_variable'
            obj = {
                'namespace': p['ns_arg']['nspace'],
                'value': p['ns_arg']['ns_value'],
                'full_string': decode(p)
            }
        else:
            obj_type = 'str_variable'
            obj = {
                'value': p['str_arg'],
            }

        new_params.append({obj_type: obj})

    return new_params


def extract_params_from_rule(rule, args, variables):

    params = []

    print('OLD RULE: {}'.format(rule))
    rule = rule.replace('{{ ', '').replace(' }}', '')

    # instead of replacing the keyword with the given variable, we need to actually create an object....

    rule = rule.replace('p_full', variables['p_full'])
    rule = rule.replace('p_name', variables['p_name'])

    rule = rule.replace('full', variables['full'])  # this should be the func object string
    rule = rule.replace('fn_name', variables['fn_name'])  # this should be the function object
    print('NEW RULE: {}'.format(rule))
    print()

    args_wanted = []

    parameter_pattern = '(p_)?parameters(\[[fmns]\])?'
    regex_ppattern = re.compile(parameter_pattern)
    param_matched_rule = regex_ppattern.search(rule)

    if param_matched_rule:  # if parameters are needed, loop through
        final_to_replace = param_matched_rule.group()
        use_parent_params = None

        try:
            use_parent_params = param_matched_rule.group(1)
            filter_string = param_matched_rule.group(2)
            if filter_string is None:
                filter_string = ''
        except IndexError as e:
            filter_string = ''  # stands for all

        # print('Use parent params: {}'.format(bool(use_parent_params)))
        # print('Filter string: {}'.format(filter_string))

        allowed_type = ''

        if 'f' in filter_string:
            allowed_type = 'function'
        elif 'm' in filter_string:
            allowed_type = 'm_function'
        elif 'n' in filter_string:
            allowed_type = 'ns_arg'
        elif 's' in filter_string:
            allowed_type = 'str_arg'

        if use_parent_params is not None:  # use the parent's args
            args_to_loop = variables['p_parameters']
        else:
            args_to_loop = args

        for a in args_to_loop:
            if allowed_type == '' or allowed_type in list(a):
                decoded_arg = decode(a)
                final_rule = rule.replace(final_to_replace, decoded_arg)
                args_wanted.append(final_rule)
                make_simple_ast(a)

    else:
        return [rule]

    return args_wanted


def make_simple_ast(a):
    print('FUNCTION:')
    print(a.get('function', None))
    print('FUNCTION ARGS:')
    print(a.get('function_args', None))

#################
# PARSING TOOLS #
#################


class Colors:
    PINK = '\033[95m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


class ParseObject(object):
    def __init__(self, ast, error, err_visual):
        self.ast = ast
        self.error = error
        self.err_visual = err_visual


class ValidationObject(ParseObject):
    def __init__(self, ast, error, err_visual, valid):
        ParseObject.__init__(self, ast, error, err_visual)
        self.valid = valid


def preprocess_bel_line(line):
    l = line.strip()  # remove newline at end of line
    l = re.sub(r',+', ',', l)  # remove multiple commas
    l = re.sub(r',', ', ', l)  # add space after each comma
    l = re.sub(r' +', ' ', l)  # remove multiple spaces

    # check for even number of parenthesis
    left_p_ct = l.count('(')
    right_p_ct = l.count(')')

    if left_p_ct < right_p_ct:
        raise MissingParenthesis('Missing left parenthesis somewhere!')
    elif right_p_ct < left_p_ct:
        raise MissingParenthesis('Missing right parenthesis somewhere!')

    # check for even number of quotation marks
    quote_ct = l.count('"')

    if quote_ct % 2 != 0:  # odd number of quotations
        raise MissingQuotation('Missing quotation mark somewhere!')

    return l


def handle_syntax_error(e):
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
                    'Check that you have a valid relationship.'.format(col_failed)
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
