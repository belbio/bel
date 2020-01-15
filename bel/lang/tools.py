#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
This file contains tools used in our parser for BEL statements.
"""

import collections
import json
import math
import os
import pprint
import random
import re
import string
from typing import Any, List, Mapping

import bel.lang.exceptions as bel_ex
import requests
import yaml
from bel.lang.ast import Arg, BELAst, Function, NSArg, StrArg

###################
# STATEMENT TOOLS #
###################


class InvalidStatementObject(object):
    def __init__(self, s, r, o):
        self.subject = s
        self.relation = r
        self.object = o
        self.string_form = self.to_string_form(s, r, o)

    def to_string_form(self, s, r, o):

        sub = self.stmt_creation_decode(s)
        rlt = r
        obj = self.stmt_creation_decode(o)

        return "{} {} {}".format(sub, rlt, obj)

    def stmt_creation_decode(self, ast_dict):

        arg_type = ast_dict.get("type", False)
        arg_value = ast_dict.get("value", False)

        if arg_type == "Function":
            f_name = ast_dict.get("name", None)

            tmp = self.stmt_creation_decode(arg_value[0])

            for arg in arg_value[1:]:
                tmp += ", {}".format(self.stmt_creation_decode(arg))

            return "{}({})".format(f_name, tmp)

        elif arg_type == "String":
            return arg_value
        elif arg_type == "Entity":
            return arg_value
        else:
            return "UNK"


# TODO: move these functions to appropriate place; create_invalid , make_statement, etc. need not be in tools.
def create_invalid(bel_obj, count, max_args):

    list_of_statement_objs = []

    for _ in range(count):
        stmt_obj = make_statement(bel_obj, max_args)
        list_of_statement_objs.append(stmt_obj)

    return list_of_statement_objs


def make_statement(bel_obj, max_args):

    s = choose_and_make_function(bel_obj, max_args)
    r = choose_rand_relation(bel_obj.relations)
    o = choose_and_make_function(bel_obj, max_args)

    return InvalidStatementObject(s, r, o)


def choose_and_make_function(bel_obj, max_args):

    full_func = {
        "name": choose_rand_function(bel_obj.function_signatures),
        "type": "Function",
        "value": [],
    }

    num_args = random.randint(1, max_args)  # how many args to have
    for _ in range(num_args):

        t = random.choice(["Entity", "String", "Function"])
        arg = {"type": t}

        if t == "Entity":
            arg["value"] = random_namespace_arg()
        elif t == "String":
            arg["value"] = random_quoted_string()
        elif t == "Function":
            arg = choose_and_make_function(bel_obj, max_args)
        else:
            pass

        full_func["value"].append(arg)

    return full_func


def choose_rand_relation(relations):

    return random.choice(relations)


def choose_rand_function(func_sigs):

    return random.choice(list(func_sigs.keys()))


def random_namespace_arg():
    ascii_letters = string.ascii_uppercase + string.ascii_lowercase
    ascii_alphanumeric_upper = string.ascii_uppercase + string.digits
    ascii_alphanumeric = ascii_letters + string.digits

    i = random.randint(2, 5)
    rand_nspace = "NS" + "".join(random.choice(ascii_alphanumeric_upper) for _ in range(i))

    j = random.randint(5, 25)

    if random.random() < 0.5:  # quoted nsvalue
        rand_nsvalue = "".join(random.choice(ascii_alphanumeric + " ' - , + /.") for _ in range(j))
        rand_nsvalue = '"{}"'.format(rand_nsvalue)
    else:  # unquoted nsvalue
        rand_nsvalue = "".join(random.choice(ascii_alphanumeric) for _ in range(j))

    return "{}: {}".format(rand_nspace, rand_nsvalue)


def random_quoted_string():
    ascii_letters = string.ascii_uppercase + string.ascii_lowercase
    ascii_alphanumeric = ascii_letters + string.digits

    j = random.randint(5, 25)

    rand_nsvalue = "".join(random.choice(ascii_alphanumeric + " ' - , + /.") for _ in range(j))
    return '"{}"'.format(rand_nsvalue)


# def simple_args(args, bel_obj):
#
#     new_args = []
#
#     for p in args:
#
#         if 'function' in p:
#             obj_type = 'function'
#             f_type = 'primary'
#             obj = {
#                 'name': p['function'],
#                 'type': f_type,
#                 'alternate': bel_obj.translate_terms[p['function']],
#                 'full_string': decode(p),
#                 'args': simple_args(p['function_args'], bel_obj)
#             }
#         elif 'm_function' in p:
#             obj_type = 'function'
#             f_type = 'modifier'
#             obj = {
#                 'name': p['m_function'],
#                 'type': f_type,
#                 'alternate': bel_obj.translate_terms[p['m_function']],
#                 'full_string': decode(p),
#                 'args': simple_args(p['m_function_args'], bel_obj)
#             }
#         elif 'ns_arg' in p:
#             obj_type = 'ns_variable'
#             obj = {
#                 'namespace': p['ns_arg']['nspace'],
#                 'value': p['ns_arg']['ns_value'],
#                 'full_string': decode(p)
#             }
#         else:
#             obj_type = 'str_variable'
#             obj = {
#                 'value': p['str_arg'],
#             }
#
#         new_args.append({obj_type: obj})
#
#     return new_args


# def extract_args_from_rule(rule, function_obj):
#
#     args = []
#
#     print('OLD RULE: {}'.format(rule))
#     rule = rule.replace('{{ ', '').replace(' }}', '')
#
#     # instead of replacing the keyword with the given variable, we need to actually create an object....
#
#     rule = rule.replace('p_full', variables['p_full'])
#     rule = rule.replace('p_name', variables['p_name'])
#
#     rule = rule.replace('full', variables['full'])  # this should be the func object string
#     rule = rule.replace('fn_name', variables['fn_name'])  # this should be the function object
#     print('NEW RULE: {}'.format(rule))
#     print()
#
#     args_wanted = []
#
#     arg_pattern = '(p_)?args(\[[fmns]\])?'
#     regex_pattern = re.compile(arg_pattern)
#     arg_matched_rule = regex_pattern.search(rule)
#
#     if arg_matched_rule:  # if args are needed, loop through
#         final_to_replace = arg_matched_rule.group()
#         use_parent_args = None
#
#         try:
#             use_parent_args = arg_matched_rule.group(1)
#             filter_string = arg_matched_rule.group(2)
#             if filter_string is None:
#                 filter_string = ''
#         except IndexError as e:
#             filter_string = ''  # stands for all
#
#         # print('Use parent args: {}'.format(bool(use_parent_args)))
#         # print('Filter string: {}'.format(filter_string))
#
#         allowed_type = ''
#
#         if 'f' in filter_string:
#             allowed_type = 'function'
#         elif 'm' in filter_string:
#             allowed_type = 'm_function'
#         elif 'n' in filter_string:
#             allowed_type = 'ns_arg'
#         elif 's' in filter_string:
#             allowed_type = 'str_arg'
#
#         if use_parent_args is not None:  # use the parent's args
#             args_to_loop = variables['p_args']
#         else:
#             args_to_loop = args
#
#         for a in args_to_loop:
#             if allowed_type == '' or allowed_type in list(a):
#                 decoded_arg = decode(a)
#                 final_rule = rule.replace(final_to_replace, decoded_arg)
#                 args_wanted.append(final_rule)
#                 make_simple_ast(a)
#
#     else:
#         return [rule]
#
#     return args_wanted


#################
# PARSING TOOLS #
#################


class Colors:
    PINK = "\033[95m"
    BLUE = "\033[94m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    END = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"
