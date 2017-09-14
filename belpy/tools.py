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
from belpy.exceptions import *


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
        alternate = bel_obj.translate_terms[initial_name]
        sigs[alternate] = sigs[initial_name]

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


def compute(ast_dict, bel_obj):

    for key, value in ast_dict.items():

        tmp_list = []

        # print(key, value)

        if key == 'function':
            f_name = value
            f_args = ast_dict.get('function_args', [])

            tmp = []
            mod_found = False

            for arg_dict in f_args:
                tmp.append(decode(arg_dict))

                # if there is a computable modifier contained in the parent function
                if arg_dict.get('m_function', None) in bel_obj.computed_mfuncs:

                    m_func = arg_dict.get('m_function', None)
                    m_func_args = arg_dict.get('m_function_args', [])

                    full = decode(arg_dict)
                    fn_name = m_func
                    p_name = f_name
                    p_full = decode(ast_dict)

                    sig_to_use = bel_obj.computed_sigs[m_func]

                    sub_rule = sig_to_use.get('subject', None).replace('{{ ', '').replace(' }}', '')
                    rel_rule = sig_to_use.get('relationship', None)
                    obj_rule = sig_to_use.get('object', None).replace('{{ ', '').replace(' }}', '')
                    computed = '{} {} {}'.format(sub_rule, rel_rule, obj_rule)

                    print(computed)

                    tmp_computed = []

                    # print('{}() need to be computed'.format(m_func))
                    # print('modifier function found: {}'.format(m_func))
                    # print('modifier function args: {}'.format(m_func_args))
                    # print('full: {}'.format(full))
                    # print('p_name: {}'.format(p_name))
                    # print('p_full: {}'.format(p_full))
                    # print('\n\n\n\n')

                    if 'p_parameters' in computed:  # loop through f_args
                        for a in f_args:
                            pass
                            # print(a)
                            # print(decode(a))
                    if 'parameters' in computed:  # loop through m_func_args
                        for m_a in m_func_args:
                            pass
                            # print(m_a)
                            # print(decode(m_a))


                    mod_found = True

                else:
                    mod_found = False
                    continue


                    # if m_func in ['variant', 'var']:
                    #     full = '{} hasVariant {}'.format(flattened_func, decode(ast_dict))
                    #     tmp_list.append(full)
                    # elif m_func in ['fusion', 'fus']:
                    #
                    #     for m in m_func_args:
                    #         if 'ns_arg' in m:
                    #             full = '{}({}) hasFusion {}'.format(f_name, decode(m), decode(ast_dict))
                    #             tmp_list.append(full)
                    #
                    # elif m_func in ['proteinModification', 'pmod']:
                    #     full = '{} hasModification {}'.format(flattened_func, decode(ast_dict))
                    #     tmp_list.append(full)
                    #
                    # else:
                    #     mod_found = False

            if mod_found:
                return tmp_list

            if f_name in ['list']:
                formatted = '{0} hasMember {1}'
            elif f_name in ['compositeAbundance', 'composite']:
                formatted = '{0} hasMember {1}'
            elif f_name in ['complexAbundance', 'complex']:
                formatted = '{0} hasComponent {1}'
            elif f_name in ['degradation', 'deg']:
                formatted = '{0} directlyDecreases {1}'
            elif f_name in ['activity', 'act']:
                formatted = '{1} hasActivity {0}'
            else:
                formatted = ''

            for arg in f_args:
                if 'm_function' in arg:
                    continue
                edge = formatted.format(decode(ast_dict), decode(arg))
                tmp_list.append(edge)

        elif key == 'bel_statement':
            new_ast = value
            s = new_ast.get('subject', None)
            o = new_ast.get('object', None)

            if o is None:  # if no object, this means only subject is present
                compute_list = compute(s)
                tmp_list.extend(compute_list)
            else:  # else the full form BEL statement with subject, relationship, and object are present
                compute_list_subject = compute(s)
                compute_list_object = compute(o)
                tmp_list.extend(compute_list_subject)
                tmp_list.extend(compute_list_object)

        else:
            continue

        return tmp_list


#################
# PARSING TOOLS #
#################

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
