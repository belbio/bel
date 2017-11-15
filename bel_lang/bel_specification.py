#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
This file contains functions to retrieve and return BEL object specifications.
"""

import collections
import glob
import math
import os
import copy
import sys
import yaml
from typing import Mapping, List, Any

import logging
log = logging.getLogger(__name__)

'''
Keys available in spec_dict:

- 'version_underscored'
- 'parser_path'
- 'jinja_template'
- 'relation_list'
- 'relation_to_short'
- 'relation_to_long'
- 'relations'
- 'function_list'
- 'function_to_short'
- 'function_to_long'
- 'functions'
- 'modifier_list'
- 'modifier_to_short'
- 'modifier_to_long'
- 'modifier_functions'
- 'function_signatures'
- 'default_namespaces'
'''


def get_specification(version) -> Mapping[str, Any]:

    spec_dict = {}

    bel_versions = get_bel_versions()
    if version not in bel_versions:
        log.error('Version \"{}\" is not available in bel_lang library package.'.format(version))
        log.error('Available versions:')
        log.error('\n'.join(['- {}'.format(v) for v in bel_versions]))
        sys.exit()

    # use this variable to find our parser file since periods aren't recommended in file names

    version_underscored = version.replace('.', '_')

    # get the current directory name, and use that to find the version's parser file location
    cur_dir_name = os.path.basename(os.path.dirname(os.path.realpath(__file__)))
    parser_path = '{}.versions.parser_v{}'.format(cur_dir_name, version_underscored)

    # try to load the version's YAML dictionary as well for functions like _create()
    # set this BEL instance's relations, signatures, term translations, etc.
    try:
        current_stored_dir = os.path.dirname(__file__)
        yaml_file_name = 'versions/bel_v{}.yaml'.format(version_underscored)
        yaml_file_path = '{}/{}'.format(current_stored_dir, yaml_file_name)
        spec_dict = yaml.load(open(yaml_file_path, 'r').read())

    except Exception as e:
        log.error('Warning: BEL Specification for Version {} YAML not found. Cannot proceed.'.format(version))
        sys.exit()

    # admin-related keys
    spec_dict['version_underscored'] = version_underscored
    spec_dict['parser_path'] = parser_path

    # keys related to creation of EBNF file inside yaml_to_ebnf
    spec_dict['jinja_template'] = 'bel.ebnf.j2'

    # add relation keys relation_list, relation_to_short, relation_to_long
    spec_dict = add_relations(spec_dict)
    # add function keys function_list, function_to_short, function_to_long
    spec_dict = add_functions(spec_dict)
    # add modifier keys modifier_list, modifier_to_short, modifier_to_long
    spec_dict = add_modifiers(spec_dict)

    spec_dict = enhance_function_signatures(spec_dict)

    spec_dict = enhance_default_namespaces(spec_dict)

    return spec_dict


def add_relations(spec_dict: Mapping[str, Any]) -> Mapping[str, Any]:
    """Add relation keys to spec_dict

    Args:
        spec_dict (Mapping[str, Any]): bel specification dictionary

    Returns:
        Mapping[str, Any]: bel specification dictionary with added relation keys
    """

    # TODO: PyCharm gives warning when instantiating the list and the two dicts below in spec_dict:
    # Class 'Mapping' does not define '__setitem__', so the '[]' operator cannot be used on its instances
    spec_dict['relation_list'] = []
    spec_dict['relation_to_short'] = {}
    spec_dict['relation_to_long'] = {}

    for relation_name in spec_dict['relations']:

        abbreviated_name = spec_dict['relations'][relation_name]['abbreviation']
        spec_dict['relation_list'].extend((relation_name, abbreviated_name))

        spec_dict['relation_to_short'][relation_name] = abbreviated_name
        spec_dict['relation_to_short'][abbreviated_name] = abbreviated_name

        spec_dict['relation_to_long'][abbreviated_name] = relation_name
        spec_dict['relation_to_long'][relation_name] = relation_name

    return spec_dict


def add_functions(spec_dict: Mapping[str, Any]) -> Mapping[str, Any]:
    """Add function keys to spec_dict

    Args:
        spec_dict (Mapping[str, Any]): bel specification dictionary

    Returns:
        Mapping[str, Any]: bel specification dictionary with added function keys
    """

    # TODO: PyCharm gives warning when instantiating the list and the two dicts below in spec_dict:
    # Class 'Mapping' does not define '__setitem__', so the '[]' operator cannot be used on its instances
    spec_dict['function_list'] = []
    spec_dict['function_to_short'] = {}
    spec_dict['function_to_long'] = {}

    for func_name in spec_dict['functions']:

        abbreviated_name = spec_dict['functions'][func_name]['abbreviation']

        spec_dict['function_list'].extend((func_name, abbreviated_name))

        spec_dict['function_to_short'][abbreviated_name] = abbreviated_name
        spec_dict['function_to_short'][func_name] = abbreviated_name

        spec_dict['function_to_long'][abbreviated_name] = func_name
        spec_dict['function_to_long'][func_name] = func_name

    return spec_dict


def add_modifiers(spec_dict: Mapping[str, Any]) -> Mapping[str, Any]:
    """Add modifier keys to spec_dict

    Args:
        spec_dict (Mapping[str, Any]): bel specification dictionary

    Returns:
        Mapping[str, Any]: bel specification dictionary with added modifier keys
    """

    # TODO: PyCharm gives warning when instantiating the list and the two dicts below in spec_dict:
    # Class 'Mapping' does not define '__setitem__', so the '[]' operator cannot be used on its instances
    spec_dict['modifier_list'] = []
    spec_dict['modifier_to_short'] = {}
    spec_dict['modifier_to_long'] = {}

    for modifier_name in spec_dict['modifier_functions']:

        abbreviated_name = spec_dict['modifier_functions'][modifier_name]['abbreviation']

        spec_dict['modifier_list'].extend((modifier_name, abbreviated_name))

        spec_dict['modifier_to_short'][abbreviated_name] = abbreviated_name
        spec_dict['modifier_to_short'][modifier_name] = abbreviated_name

        spec_dict['modifier_to_long'][abbreviated_name] = modifier_name
        spec_dict['modifier_to_long'][modifier_name] = modifier_name

    return spec_dict


def get_bel_versions() -> List[str]:
    """Get BEL Language versions supported

    Get the list of all BEL Language versions supported.

    Returns:
        List[str]: list of versions
    """

    files = glob.glob('{}/versions/bel_v*.yaml'.format(os.path.dirname(__file__)))
    versions = []
    for fn in files:
        yaml_dict = yaml.load(open(fn, 'r').read())
        versions.append(yaml_dict['version'])

    return versions


def enhance_function_signatures(spec_dict: Mapping[str, Any]) -> Mapping[str, Any]:
    """Enhance function signatures

    Add required and optional objects to signatures objects for semantic validation
    support.

    Args:
        spec_dict (Mapping[str, Any]): bel specification dictionary

    Returns:
        Mapping[str, Any]: return enhanced bel specification dict
    """

    for func in spec_dict['function_signatures']:
        for i, sig in enumerate(spec_dict['function_signatures'][func]['signatures']):
            args = sig['arguments']
            req_args = []
            pos_args = []
            opt_args = []
            mult_args = []
            for arg in args:
                if arg.get('multiple', False):
                    if arg['type'] in ['Function', 'Modifier']:
                        mult_args.extend(arg.get('values', []))
                    elif arg['type'] in ['StrArgNSArg', 'NSArg', 'StrArg']:
                        mult_args.append(arg['type'])
                elif arg.get('optional', False) and arg.get('position_dependent', False):
                    if arg['type'] in ['Function', 'Modifier']:
                        pos_args.append(arg.get('values', []))
                    elif arg['type'] in ['StrArgNSArg', 'NSArg', 'StrArg']:
                        pos_args.append(arg['type'])
                elif arg.get('optional', False):
                    if arg['type'] in ['Function', 'Modifier']:
                        opt_args.extend(arg.get('values', []))
                    elif arg['type'] in ['StrArgNSArg', 'NSArg', 'StrArg']:
                        opt_args.append(arg['type'])
                else:
                    if arg['type'] in ['Function', 'Modifier']:
                        req_args.append(arg.get('values', []))
                    elif arg['type'] in ['StrArgNSArg', 'NSArg', 'StrArg']:
                        req_args.append(arg['type'])

            spec_dict['function_signatures'][func]['signatures'][i]['req_args'] = copy.deepcopy(req_args)
            spec_dict['function_signatures'][func]['signatures'][i]['pos_args'] = copy.deepcopy(pos_args)
            spec_dict['function_signatures'][func]['signatures'][i]['opt_args'] = copy.deepcopy(opt_args)
            spec_dict['function_signatures'][func]['signatures'][i]['mult_args'] = copy.deepcopy(mult_args)

    return spec_dict


def enhance_default_namespaces(spec_dict: Mapping[str, Any]) -> Mapping[str, Any]:
    """Enhance the default namespaces dictionary

    Add names and abbreviations of each default_namespace type to a key of type
    (e.g. ProteinModification or Activity) so that one can check for existence
    of a

    Args:
        spec_dict (Mapping[str, Any]): bel specification dictionary

    Returns:
        Mapping[str, Any]: bel specification dictionary with added default namespace lists
    """

    new_ns = {}

    for ns in spec_dict['default_namespaces']:
        ns_type = spec_dict['default_namespaces'][ns]['type']
        values = spec_dict['default_namespaces'][ns]['values']
        new_ns[ns_type] = []
        for val in values:
            new_ns[ns_type].append(val['name'])
            new_ns[ns_type].append(val['abbreviation'])

    for ns_type in new_ns:
        spec_dict['default_namespaces'][ns_type] = copy.deepcopy(new_ns[ns_type])

    return spec_dict
