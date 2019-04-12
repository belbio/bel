#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
ast_dict from Tatsu is converted to this Ast Class object and used for
validation and BEL transformation (e.g. canonicalization, orthologization, etc)
"""

from typing import Mapping, Any
import traceback
import sys

import bel.lang.bel_utils

import structlog
log = structlog.getLogger(__name__)


########################
# BEL statement AST #
########################
class BELAst(object):

    def __init__(self, bel_subject, bel_relation, bel_object, spec):
        self.bel_subject = bel_subject
        self.bel_relation = bel_relation
        self.bel_object = bel_object
        self.spec = spec  # bel specification dictionary
        self.type = 'BELAst'
        self.species = set()  # tuples of (species_id, species_label)
        self.collected_nsarg_norms = False
        self.collected_orthologs = False
        self.partially_orthologized = False
        self.args = [self.bel_subject, self.bel_object]

    def dump(self):
        return {
            'bel_subject': self.bel_subject.to_string(),
            'bel_relation': self.bel_relation,
            'bel_object': self.bel_object.to_string(),
            'type': self.type,
            'collected_nsarg_norms': self.collected_nsarg_norms,
            'collected_orthologs': self.collected_orthologs,
            'args': self.args,
            'spec': 'Not included',
        }

    def canonicalize(self):

        if not self.collected_nsarg_norms:
            log.error(f'Cannot canonicalize without running collected_nsarg_norms() on BEL object first {self.dump()}')
            log.info(self.dump)
            traceback.print_stack(file=sys.stdout)
            return self

        if self and isinstance(self, NSArg):
            self.canonicalize()

        if hasattr(self, 'args'):
            for arg in self.args:
                if arg:
                    arg.canonicalize()

        return self

    def decanonicalize(self):
        if not self.collected_nsarg_norms:
            log.error(f'Cannot decanonicalize without running collected_nsarg_norms() on BEL object first {self.dump()}')
            log.info(self.dump)
            traceback.print_stack(file=sys.stdout)
            return self

        if self and isinstance(self, NSArg):
            self.decanonicalize()

        if hasattr(self, 'args'):
            for arg in self.args:
                if arg:
                    arg.decanonicalize()

        return self

    def orthologize(self, species_id, belast=None):
        if not self.collected_orthologs:
            log.error(f'Cannot orthologize without running collect_orthologs() on BEL object first {self.dump()}')
            log.info(self.dump)
            traceback.print_stack(file=sys.stdout)
            return self

        if hasattr(self, 'args'):
            if belast is None:
                belast = self
            for arg in self.args:
                if arg:
                    arg.orthologize(species_id, belast)

        return self

    def to_string(self, ast_obj=None, fmt: str = 'medium') -> str:
        """Convert AST object to string

        Args:
            fmt (str): short, medium, long formatted BEL statements
                short = short function and short relation format
                medium = short function and long relation format
                long = long function and long relation format
            canonicalize

        Returns:
            str: string version of BEL AST
        """

        if not ast_obj:
            ast_obj = self

        bel_relation = None
        if self.bel_relation and fmt == 'short':
            bel_relation = self.spec['relations']['to_short'].get(self.bel_relation, self.bel_relation)
        elif self.bel_relation:
            bel_relation = self.spec['relations']['to_long'].get(self.bel_relation, self.bel_relation)

        if self.bel_subject and bel_relation and self.bel_object:
            if isinstance(self.bel_object, BELAst):
                return '{} {} ({})'.format(self.bel_subject.to_string(fmt=fmt), bel_relation, self.bel_object.to_string(fmt=fmt))
            else:
                return '{} {} {}'.format(self.bel_subject.to_string(fmt=fmt), bel_relation, self.bel_object.to_string(fmt=fmt))

        elif self.bel_subject:
            return '{}'.format(self.bel_subject.to_string(fmt=fmt))

        else:
            return ''

    def to_triple(self, ast_obj=None, fmt='medium'):
        """Convert AST object to BEL triple

        Args:
            fmt (str): short, medium, long formatted BEL statements
                short = short function and short relation format
                medium = short function and long relation format
                long = long function and long relation format

        Returns:
            dict: {'subject': <subject>, 'relation': <relations>, 'object': <object>}
        """

        if not ast_obj:
            ast_obj = self

        if self.bel_subject and self.bel_relation and self.bel_object:
            if self.bel_relation.startswith('has'):
                bel_relation = self.bel_relation
            elif fmt == 'short':
                bel_relation = self.spec['relations']['to_short'].get(self.bel_relation, None)
            else:
                bel_relation = self.spec['relations']['to_long'].get(self.bel_relation, None)

            bel_subject = self.bel_subject.to_string(fmt=fmt)

            if isinstance(self.bel_object, (BELAst)):
                bel_object = f'({self.bel_object.to_string(fmt=fmt)})'
            else:
                bel_object = self.bel_object.to_string(fmt=fmt)

            return {
                'subject': bel_subject,
                'relation': bel_relation,
                'object': bel_object,
            }

        elif self.bel_subject:
            return {'subject': self.bel_subject.to_string(fmt=fmt), }

        else:
            return None

    def __str__(self):
        return self.to_string(self)

    __repr__ = __str__

    def print_tree(self, ast_obj=None):
        """Convert AST object to tree view of BEL AST

        Returns:
            prints tree of BEL AST to STDOUT
        """

        if not ast_obj:
            ast_obj = self

        if hasattr(self, 'bel_subject'):
            print('Subject:')
            self.bel_subject.print_tree(self.bel_subject, indent=0)

        if hasattr(self, 'bel_relation'):
            print('Relation:', self.bel_relation)

        if hasattr(self, 'bel_object'):
            if self.bel_object.type == 'BELAst':
                if hasattr(self, 'bel_subject'):
                    print('Nested Subject:')
                    self.bel_object.bel_subject.print_tree(indent=0)

                if hasattr(self, 'bel_relation'):
                    print('Nested Relation:', self.bel_object.bel_relation)

                if hasattr(self, 'bel_object'):
                    print('Nested Object:')
                    self.bel_object.bel_object.print_tree(indent=0)
            else:
                print('Object:')
                self.bel_object.print_tree(self.bel_object, indent=0)

        return self

###################
# Function object #
###################


class Function(object):

    def __init__(self, name, spec, parent_function=None):

        self.name = spec['functions']['to_long'].get(name, name)
        self.name_short = spec['functions']['to_short'].get(name, name)
        if self.name in spec['functions']['info']:
            self.function_type = spec['functions']['info'][self.name]['type']
        else:
            self.function_type = ''

        self.type = 'Function'

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

    def change_parent_fn(self, parent_function):
        self.parent_function = parent_function

    def change_function_type(self, function_type):
        self.function_type = function_type

    def canonicalize(self):
        if isinstance(self, NSArg):
            self.canonicalize()

        if hasattr(self, 'args'):
            for arg in self.args:
                arg.canonicalize()

        return self

    def decanonicalize(self):
        if isinstance(self, NSArg):
            self.decanonicalize()

        if hasattr(self, 'args'):
            for arg in self.args:
                arg.decanonicalize()

        return self

    def orthologize(self, species_id, belast):
        if isinstance(self, NSArg):
            self.orthologize(species_id)

        if hasattr(self, 'args'):
            for arg in self.args:
                arg.orthologize(species_id, belast)

        return self

    def to_string(self, fmt: str = 'medium', canonicalize: bool = False, decanonicalize: bool = False, orthologize: str = None) -> str:
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

        if fmt in ['short', 'medium']:
            function_name = self.name_short
        else:
            function_name = self.name

        return '{}({})'.format(function_name, arg_string)

    def __str__(self):
        arg_string = ', '.join([a.to_string() for a in self.args])
        return '{}({})'.format(self.name, arg_string)

    __repr__ = __str__

    def print_tree(self, ast_obj=None, indent=0):
        if not ast_obj:
            ast_obj = self
        for arg in self.args:
            if arg.__class__.__name__ == 'Function':
                arg.print_tree(arg, indent + 1)
            else:
                print('\t' * (indent + 1) + arg.print_tree())

    def subcomponents(self, subcomponents):
        """Generate subcomponents of the BEL subject or object

        These subcomponents are used for matching parts of a BEL
        subject or Object in the Edgestore.

        Args:
            AST
            subcomponents:  Pass an empty list to start a new subcomponents request

        Returns:
            List[str]: subcomponents of BEL subject or object
        """

        for arg in self.args:
            if arg.__class__.__name__ == 'Function':
                subcomponents.append(arg.to_string())
                if arg.function_type == 'primary':
                    arg.subcomponents(subcomponents)
            else:
                subcomponents.append(arg.to_string())

        return subcomponents


#####################
# Argument objects #
#####################
class Arg(object):

    def __init__(self, parent_function):
        self.parent_function = parent_function
        self.siblings = []
        self.optional = False
        self.type = 'Arg'

    def add_sibling(self, sibling):
        self.siblings.append(sibling)

    def canonicalize(self):
        return self

    def decanonicalize(self):
        return self

    def orthologize(self, species_id, belast):
        return self


class NSArg(Arg):

    def __init__(self, namespace, value, parent_function=None, value_types=[]):
        Arg.__init__(self, parent_function)
        self.namespace = namespace
        self.value = self.normalize_nsarg_value(value)
        self.value_types = value_types
        self.type = 'NSArg'
        self.canonical = None
        self.decanonical = None
        self.species_id = None
        self.species_label = None
        self.orthologs = {}  # {'TAX:9606': {'species_label': 'human', 'canonical': 'EG:207', 'decanonical': 'HGNC:AKT1'}, 'TAX:10090': {'species_label': 'mouse', canonical': 'EG:11651', 'decanonical': 'MGI:Akt1'}, ...
        self.orthology_species = None
        self.orthologized = None  # True for orthologized - False -> unable to orthologize
        self.original = f'{namespace}:{value}'

        # What entity types can this be from the function signatures?
        #    this is used for statement autocompletion and entity validation
        self.entity_types = []

    def change_nsvalue(self, namespace, value):
        """Deprecated"""

        self.namespace = namespace
        self.value = value

    def update_nsval(self, *, nsval: str = None, ns: str = None, val: str = None) -> None:
        """Update Namespace and valueast.

        Args:
            nsval: e.g. HGNC:AKT1
            ns: namespace
            val: value of entity
        """

        if not (ns and val) and nsval:
            (ns, val) = nsval.split(':', 1)
        elif not (ns and val) and not nsval:
            log.error("Did not update NSArg - no ns:val or nsval provided")

        self.namespace = ns
        self.value = val

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

        return bel.lang.bel_utils.quoting_nsarg(nsarg_value)

    def canonicalize(self):
        if isinstance(self, NSArg):
            self.update_nsval(nsval=self.canonical)
        return self

    def decanonicalize(self):
        if isinstance(self, NSArg):
            self.update_nsval(nsval=self.decanonical)
        return self

    def orthologize(self, ortho_species_id, belast):
        """Decanonical ortholog name used"""

        if self.orthologs and ortho_species_id in self.orthologs and ortho_species_id != self.species_id:
            self.orthology_species = ortho_species_id
            self.canonical = self.orthologs[ortho_species_id]['canonical']
            self.decanonical = self.orthologs[ortho_species_id]['decanonical']
            self.update_nsval(nsval=self.decanonical)
            self.orthologized = True

        elif self.species_id and ortho_species_id not in self.orthologs:
            self.orthologized = False
            belast.partially_orthologized = True

        return self

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
        return f'{self.namespace}:{self.value}'

    def print_tree(self, fmt: str = 'medium') -> str:
        return f'NSArg: {self.namespace}:{self.value} canonical: {self.canonical} decanonical: {self.decanonical} orthologs: {self.orthologs} orig_species: {self.orthology_species}'

    def __str__(self):
        return f'{self.namespace}:{self.value}'

    __repr__ = __str__


class StrArg(Arg):

    def __init__(self, value, parent_function, value_types=[]):
        Arg.__init__(self, parent_function)
        self.value = value
        self.value_types = value_types
        self.type = 'StrArg'

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

    def print_tree(self, fmt: str = 'medium') -> str:
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
