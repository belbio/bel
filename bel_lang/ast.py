#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
ast_dict from Tatsu is converted to this Ast Class object and used for
validation and BEL transformation (e.g. canonicalization, orthologization, etc)
"""

from typing import Mapping, Any
import re

import logging
log = logging.getLogger(__name__)


########################
# BEL statement AST #
########################
class BELAst(object):

    def __init__(self, bel_subject, bel_relation, bel_object, spec):
        self.bel_subject = bel_subject
        self.bel_relation = bel_relation
        self.bel_object = bel_object
        self.spec = spec  # bel specification dictionary
        self.args = [bel_subject, bel_relation, bel_object]

    def to_string(self, fmt: str = 'medium') -> str:
        """Convert AST object to string

        Args:
            fmt (str): short, medium, long formatted BEL statements
                short = short function and short relation format
                medium = short function and long relation format
                long = long function and long relation format

        Returns:
            str: string version of BEL AST
        """
        if self.bel_subject and self.bel_relation and self.bel_object:
            if isinstance(self.bel_object, BELAst):
                return '{} {} ({})'.format(self.bel_subject, self.bel_relation, self.bel_object)
            else:
                return '{} {} {}'.format(self.bel_subject, self.bel_relation, self.bel_object)

        elif self.bel_subject:
            return '{}'.format(self.bel_subject)

        else:
            return ''

    def to_components(self, fmt='medium'):
        if self.bel_subject and self.bel_relation and self.bel_object:
            if fmt == 'short':
                bel_relation = self.spec['relation_to_short'].get(self.bel_relation, None)
            else:
                bel_relation = self.spec['relation_to_long'].get(self.bel_relation, None)

            bel_subject = self.bel_subject.to_string(fmt)

            if isinstance(self.bel_object, (BELAst)):
                bel_object = f'({self.bel_object.to_string(fmt)})'
            else:
                bel_object = self.bel_object.to_string(fmt)
            return {
                'subject': bel_subject,
                'relation': bel_relation,
                'object': bel_object,
            }

        elif self.bel_subject:
            return {'subject': self.bel_subject.to_string(fmt), }

        else:
            return None

    def __str__(self):
        return self.to_string(self)

    __repr__ = __str__

    def print_tree(self, ast_obj=None):
        if not ast_obj:
            ast_obj = self
        self.bel_subject.print_tree(ast_obj, indent=0)
        print(self.bel_relation)
        self.bel_object.print_tree(ast_obj, indent=0)


###################
# Function object #
###################

class Function(object):

    def __init__(self, name, spec, parent_function=None):

        if name in spec['function_list']:
            self.function_type = 'primary'
            self.name = spec['function_to_long'][name]
            self.name_short = spec['function_to_short'][name]

        elif name in spec['modifier_list']:
            self.function_type = 'modifier'
            self.name = spec['modifier_to_long'][name]
            self.name_short = spec['modifier_to_short'][name]

        self.parent_function = parent_function
        self.spec = spec
        self.position_dependent = False
        self.args = []
        self.siblings = []

    def is_primary(self):
        if self.function_type == 'primary':
            return True
        return False

    def is_modifier(self):
        if self.function_type == 'modifier':
            return True
        return False

    def add_argument(self, arg):
        self.args.append(arg)

    def add_sibling(self, sibling):
        self.siblings.append(sibling)

    def change_function_type(self, function_type):
        self.function_type = function_type

    def to_string(self, fmt: str = 'medium') -> str:
        """Convert AST object to string

        Args:
            fmt (str): short, medium, long formatted BEL statements
                short = short function and short relation format
                medium = short function and long relation format
                long = long function and long relation format

        Returns:
            str: string version of BEL AST
        """

        arg_string = ', '.join([a.to_string(fmt=fmt) for a in self.args])

        function_name = self.name

        if fmt in ['short', 'medium']:
            function_name = self.spec['function_to_short'].get(self.name, self.spec['modifier_to_short'].get(self.name, self.name))

        return '{}({})'.format(function_name, arg_string)

    def __str__(self):
        arg_string = ', '.join([a.to_string() for a in self.args])
        return '{}({})'.format(self.name, arg_string)

    __repr__ = __str__

    def print_tree(self, ast_obj=None, indent=0):
        if not ast_obj:
            ast_obj = self
        print('\t' * indent + str(self))
        for arg in self.args:
            if arg.__class__.__name__ == 'Function':
                arg.print_tree(arg, indent + 1)
            else:
                print('\t' * (indent + 1) + str(arg))


#####################
# Argument objects #
#####################
class Arg(object):

    def __init__(self, parent_function):
        self.parent_function = parent_function
        self.siblings = []
        self.optional = False

    def add_sibling(self, sibling):
        self.siblings.append(sibling)


class NSArg(Arg):

    def __init__(self, namespace, value, parent_function, value_types=[]):
        Arg.__init__(self, parent_function)
        self.namespace = namespace
        self.value = self.normalize_nsarg_value(value)
        self.value_types = value_types

        # What entity types can this be from the function signatures?
        #    this is used for statement autocompletion and entity validation
        self.entity_types = []

    def change_nsvalue(self, namespace, value):
        self.namespace = namespace
        self.value = value

    def add_value_types(self, value_types):
        self.value_types = value_types

    def normalize_nsarg_value(self, nsarg_value):
        """Normalize NSArg value

        If needs quotes (only if it contains whitespace, comma or ')' ), make sure
        it is quoted, else remove quotes

        Args:
            nsarg_value (str): NSArg value, e.g. AKT1 of HGNC:AKT1

        Returns:
            str:

        """
        quoted = re.findall('^"(.*)"$', nsarg_value)

        if re.search('[),\s]', nsarg_value):  # quote only if it contains whitespace, comma or ')'
            if quoted:
                return nsarg_value
            else:
                return f'"{nsarg_value}"'
        else:
            if quoted:
                return quoted[0]
            else:
                return nsarg_value

    def to_string(self, fmt: str = 'medium') -> str:
        """Convert AST object to string

        Args:
            fmt (str): short, medium, long formatted BEL statements
                short = short function and short relation format
                medium = short function and long relation format
                long = long function and long relation format

        Returns:
            str: string version of BEL AST
        """
        return '{}:{}'.format(self.namespace, self.value)

    def __str__(self):
        return 'NSArg: {}:{}'.format(self.namespace, self.value)

    __repr__ = __str__


class StrArg(Arg):

    def __init__(self, value, parent_function, value_types=[]):
        Arg.__init__(self, parent_function)
        self.value = value
        self.value_types = value_types

    def add_value_types(self, value_types):
        self.value_types = value_types

    def to_string(self, fmt: str = 'medium') -> str:
        """Convert AST object to string

        Args:
            fmt (str): short, medium, long formatted BEL statements
                short = short function and short relation format
                medium = short function and long relation format
                long = long function and long relation format

        Returns:
            str: string version of BEL AST
        """
        return '{}'.format(self.value)

    def __str__(self):
        return 'StrArg: {}'.format(self.value)

    __repr__ = __str__


def ast_dict_to_objects(ast_dict: Mapping[str, Any], bel_obj) -> BELAst:
    """Convert Tatsu AST dictionary to BEL AST object

    Args:
        ast_dict (Mapping[str, Any])

    Returns:
        BELAst: object representing the BEL Statement AST
    """
    ast_subject = ast_dict.get('subject', None)
    ast_object = ast_dict.get('object', None)

    bel_subject = None
    bel_object = None
    bel_relation = ast_dict.get('relation')

    if ast_subject:
        bel_subject = function_ast_to_objects(ast_subject, bel_obj)

    if ast_object:
        bel_object = function_ast_to_objects(ast_object, bel_obj)

    ast_obj = BELAst(bel_subject, bel_relation, bel_object, bel_obj.spec)

    return ast_obj


def function_ast_to_objects(fn_ast_dict, bel_obj):
    # needed and used

    # print(fn_ast_dict)
    spec = bel_obj.spec  # bel specification

    func_name = fn_ast_dict.get('function', None)
    potential_bel_stmt = fn_ast_dict.get('bel_statement', None)

    if func_name is None and potential_bel_stmt is not None:  # this is a nested BEL statement
        tmp_fn_obj = ast_dict_to_objects(potential_bel_stmt, bel_obj)
    else:
        tmp_fn_obj = Function(func_name, spec)
        tmp_fn_obj_args = fn_ast_dict.get('function_args', None)

        # for each argument in tmp_fn_obj_args, add it to our function object using add_args_to_compute_obj()
        add_args_to_compute_obj(bel_obj, tmp_fn_obj, tmp_fn_obj_args)

    return tmp_fn_obj


def add_args_to_compute_obj(our_bel_obj, our_obj, our_obj_args):
    # needed and used
    tmp_all_args_objs = []

    for argument in our_obj_args:

        fn_args = []
        tmp_arg_obj = None

        if 'function' in argument:
            fn = argument.get('function', None)
            fn_parent = our_obj
            fn_args = argument.get('function_args', [])

            tmp_arg_obj = Function(fn, our_bel_obj.spec, parent_function=fn_parent)

        elif 'modifier' in argument:
            fn = argument.get('modifier', None)
            fn_parent = our_obj
            fn_args = argument.get('modifier_args', [])

            tmp_arg_obj = Function(fn, our_bel_obj.spec, parent_function=fn_parent)

        elif 'ns_arg' in argument:
            ns = argument['ns_arg']['ns']
            nsv = argument['ns_arg']['ns_value']
            ns_parent = our_obj

            tmp_arg_obj = NSArg(ns, nsv, ns_parent)

        elif 'str_arg' in argument:
            sv = argument.get('str_arg', None)
            sv_parent = our_obj

            tmp_arg_obj = StrArg(sv, sv_parent)

        else:
            continue

        if fn_args:
            add_args_to_compute_obj(our_bel_obj, tmp_arg_obj, fn_args)

        if tmp_arg_obj is not None:
            our_obj.add_argument(tmp_arg_obj)
            tmp_all_args_objs.append(tmp_arg_obj)

    # nested loop to add siblings to each arg. exclude the arg itself as its own sibling by ignoring if index match.
    for idx, arg_obj in enumerate(tmp_all_args_objs):
        for sibling_idx, sibling_arg_obj in enumerate(tmp_all_args_objs):

            if idx == sibling_idx:  # skip adding self as sibling
                continue
            else:
                arg_obj.add_sibling(sibling_arg_obj)

    return
