#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
This file contains tools used in our parser for BEL statements.
"""

import re
import collections
import math
import random
import yaml
import string
import os
from belpy.exceptions import *


###################
# STATEMENT TOOLS #
###################

CURRENT_STORED_DIRECTORY = os.path.dirname(__file__)


class TestBELStatementGenerator(object):
    def __init__(self, version='2.0.0'):

        version_dots_to_underscore = version.replace('.', '_')

        try:
            yaml_file_name = 'versions/bel_v{}.yaml'.format(version_dots_to_underscore)
            yaml_file_path = '{}/{}'.format(CURRENT_STORED_DIRECTORY, yaml_file_name)
            yaml_dict = yaml.load(open(yaml_file_path, 'r').read())
        except Exception as e:
            print(e)
            print('The create() method for version {} is not defined yet.'.format(version))
            return

        self.abbre_to_name = self.abbreviations_to_names(yaml_dict)
        self.name_to_abbre = self.names_to_abbreviations(yaml_dict)

        self.function_signatures = self.get_function_signatures(yaml_dict)
        self.relationships = self.get_all_relationships(yaml_dict)

    def get_function_signatures(self, yaml_dict):
        """

        :param yaml_dict: the dictionary parsed from the given YAML file defined by the user.
        :return: signature dictionary.
        """

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
            signature_dict[self.name_to_abbre[f_name]] = f_sigs

        return signature_dict

    def get_all_relationships(self, yaml_dict):
        """

        :param yaml_dict: the dictionary parsed from the given YAML file defined by the user.
        :return: list of relationships.
        """

        relationships = set()

        for relationship in yaml_dict.get('relationships', []):
            r_name = relationship.get('name', None)
            r_abbr = relationship.get('abbreviation', None)

            relationships.add(r_name)
            relationships.add(r_abbr)

        return list(relationships)

    def abbreviations_to_names(self, yaml_dict):

        abbreviations = {}

        for fn in yaml_dict.get('functions', []):
            f_name = fn.get('name', 'unknown')
            f_abbr = fn.get('abbreviation', 'unknown')
            abbreviations[f_abbr] = f_name

        for m_fn in yaml_dict.get('modifier_functions', []):
            mf_name = m_fn.get('name', 'unknown')
            mf_abbr = m_fn.get('abbreviation', 'unknown')
            abbreviations[mf_abbr] = mf_name

        return abbreviations

    def names_to_abbreviations(self, yaml_dict):

        names = {}

        for fn in yaml_dict.get('functions', []):
            f_name = fn.get('name', 'unknown')
            f_abbr = fn.get('abbreviation', 'unknown')
            names[f_name] = f_abbr

        for m_fn in yaml_dict.get('modifier_functions', []):
            mf_name = m_fn.get('name', 'unknown')
            mf_abbr = m_fn.get('abbreviation', 'unknown')
            names[mf_name] = mf_abbr

        return names

    def make_statement(self, max_params):

        s = self.choose_and_make_function(max_params)
        r = self.choose_rand_relationship()
        o = self.choose_and_make_function(max_params)

        return TestBELStatement(s, r, o)

    def choose_and_make_function(self, max_params):

        full_func = {'name': self.choose_rand_function(), 'type': 'Function', 'value': []}

        num_args = random.randint(1, max_params)  # how many args to have
        for _ in range(num_args):

            t = random.choice(['Entity', 'String', 'Function'])
            arg = {'type': t}

            if t == 'Entity':
                arg['value'] = random_namespace_param()
            elif t == 'String':
                arg['value'] = random_quoted_string()
            elif t == 'Function':
                arg = self.choose_and_make_function(max_params)
            else:
                pass

            full_func['value'].append(arg)

        return full_func

    def choose_rand_relationship(self):

        return random.choice(self.relationships)

    def choose_rand_function(self):

        return random.choice(list(self.function_signatures.keys()))


class TestBELStatement(object):
    def __init__(self, s, r, o):
        self.subject = s
        self.relationship = r
        self.object = o
        self.string_form = self.to_string_form(s, r, o)

    def to_string_form(self, s, r, o):

        sub = self.decode(s)
        rlt = r
        obj = self.decode(o)

        return '{} {} {}'.format(sub, rlt, obj)

    def decode(self, dict):

        t = dict.get('type', False)
        v = dict.get('value', False)

        if t == 'Function':
            f_name = dict.get('name', None)

            tmp = self.decode(v[0])

            for param in v[1:]:
                tmp += ', {}'.format(self.decode(param))

            return '{}({})'.format(f_name, tmp)

        elif t == 'String':
            return v
        elif t == 'Entity':
            return v
        else:
            return 'UNK'


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


def decode(dict):
    for key, value in dict.items():
        if key == 'ns_arg':
            return '{}:{}'.format(value['nspace'], value['ns_value'])
        elif key == 'str_arg':
            return '{}'.format(value)
        elif key == 'function':
            tmp = []
            f_name = value
            f_args = dict.get('function_args', [])

            for arg_dict in f_args:
                tmp.append(decode(arg_dict))

            return '{}({})'.format(f_name, ', '.join(tmp))
        elif key == 'm_function':
            tmp = []
            m_f_name = value
            m_f_args = dict.get('m_function_args', [])

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
            print('**************************************')


def compute(ast_dict):
    for key, value in ast_dict.items():

        tmp_list = []

        if key == 'function':
            f_name = value
            f_args = ast_dict.get('function_args', [])

            tmp = []
            mod_found = False

            for arg_dict in f_args:
                tmp.append(decode(arg_dict))

                if 'm_function' in arg_dict: # if there is a modifier function contained in the parent function

                    m_func = arg_dict.get('m_function', None)
                    m_func_args = arg_dict.get('m_function_args', None)

                    flattened_func = '{}({})'.format(f_name, decode(f_args[0]))

                    mod_found = True

                    if m_func in ['variant', 'var']:
                        full = '{} hasVariant {}'.format(flattened_func, decode(ast_dict))
                        tmp_list.append(full)
                    elif m_func in ['fusion', 'fus']:

                        for m in m_func_args:
                            if 'ns_arg' in m:
                                full = '{}({}) hasFusion {}'.format(f_name, decode(m), decode(ast_dict))
                                tmp_list.append(full)

                    elif m_func in ['proteinModification', 'pmod']:
                        full = '{} hasModification {}'.format(flattened_func, decode(ast_dict))
                        tmp_list.append(full)

                    else:
                        mod_found = False

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
        error_msg = 'Failed parse at position {}. Check that you have a valid relationship.'.format(col_failed)
    elif undefined_type == 'funcs':
        error_msg = 'Failed parse at position {}. Check that you have a valid primary or modifier function.'.format(
            col_failed)
    elif undefined_type == 'function_open':
        error_msg = 'Failed parse at position {}. Check that you have have opened your parenthesis correctly before this point.'.format(
            col_failed)
    elif undefined_type == 'function_close':
        error_msg = 'Failed parse at position {}. Check that you have have closed your parenthesis correctly before this point.'.format(
            col_failed)
    elif undefined_type == 'full_nsv':
        error_msg = 'Failed parse at position {}. Check that you have a valid namespace argument.'.format(col_failed)
    else:
        error_msg = 'Failed parse at position {}. Check to make sure commas/spaces are not missing.'.format(col_failed, undefined_type)

    return error_msg, err_visualizer
