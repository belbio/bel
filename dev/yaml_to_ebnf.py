#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Usage: python yaml_to_ebnf.py <path to .yaml file> <path to Jinja template> <path to output .ebnf file>

Use this script to convert the user defined YAML file to two other files:
    - an EBNF file used by Tatsu to compile into a parser (syntax)
"""

from jinja2 import Environment, FileSystemLoader
import datetime
import sys
import yaml
from itertools import chain

NAME_OF_YAML_FILE = sys.argv[1]  # take a YAML file as argument

PATH_OF_EBNFTEMP_FILE = sys.argv[2]  # get full path of where our Jinja template is
PATH_SPLIT = PATH_OF_EBNFTEMP_FILE.rsplit('\\', 1)
DIRECTORY_OF_EBNFTEMP_FILE = '.'  # directory of where our Jinja template is located; use period for same directory
NAME_OF_EBNFTEMP_FILE = PATH_SPLIT[0]  # name of Jinja template for the EBNF file
NAME_OF_OUTPUT_SYNTAX_FILE = sys.argv[3]  # where to output our .ebnf file


def main():

    # load a dictionary from the YAML file to make data access easier
    yaml_dict = yaml_to_dict(NAME_OF_YAML_FILE)

    ######################
    # METADATA FROM YAML #
    ######################

    bel_version = yaml_dict['version']  # e.g. version 2.1.5
    bel_major_version = yaml_dict['version'][0]  # e.g. version 2
    created_time = datetime.datetime.now().strftime('%B %d, %Y - %I:%M:%S%p')

    ###############################
    # PRIMARY FUNCTIONS FROM YAML #
    ###############################

    # get the function list
    fn_list = yaml_dict['functions']
    # gather all names and abbreviations from the list of function objects present in the dictionary
    list_funcs = set(chain.from_iterable((fn_list[fc]['name'], fn_list[fc]['abbreviation']) for fc in fn_list))
    # sort the list of functions by length in descending order
    functions = sorted(list(list_funcs), key=len, reverse=True)

    ################################
    # MODIFIER FUNCTIONS FROM YAML #
    ################################

    # get the modifier function list
    m_fn_list = yaml_dict['modifier_functions']
    # gather all names and abbreviations from the list of modifier function objects present in the dictionary
    list_m_funcs = set(chain.from_iterable((m_fn_list[mf]['name'], m_fn_list[mf]['abbreviation']) for mf in m_fn_list))
    # sort the list of functions by length in descending order
    m_functions = sorted(list(list_m_funcs), key=len, reverse=True)

    ###########################
    # RELATIONSHIPS FROM YAML #
    ###########################

    # get the relations list
    rl_list = yaml_dict['relations']
    # gather all names and abbreviations from the list of relation objects present in the dictionary
    list_relations = set(chain.from_iterable((rl_list[rl]['name'], rl_list[rl]['abbreviation']) for rl in rl_list))
    # sort the list of functions by length in descending order
    relations = sorted(list(list_relations), key=len, reverse=True)

    ##############################################
    # VALID MODIFIER FUNCTIONS FOR EACH FUNCTION #
    ##############################################

    # dictionary containing primary funcs as keys and sets of valid modifier funcs for that respective func as a value
    fns_valid_mods = {}

    for fn in fn_list:  # we need both the function name + it's abbreviation as keys in this dictionary
        fn_name = fn_list[fn]['name']
        fn_abbreviation = fn_list[fn]['abbreviation']
        fns_valid_mods[fn_name] = {'validModifiers': set()}
        fns_valid_mods[fn_abbreviation] = {'validModifiers': set()}

        for mod_fn in m_fn_list:
            for allowed_fn in m_fn_list[mod_fn]['primary_function']:
                if allowed_fn in [fn_name, fn_abbreviation]:
                    m_fn_name = m_fn_list[mod_fn]['name']  # name of modifier function that can be used with this primary func
                    m_fn_abbr = m_fn_list[mod_fn]['abbreviation']  # same as above but for the abbreviated name of this mod func

                    fns_valid_mods[fn_name]['validModifiers'].update([m_fn_name, m_fn_abbr])  # adds to fn name set
                    fns_valid_mods[fn_abbreviation]['validModifiers'].update([m_fn_name, m_fn_abbr])  # adds to fn abbr set

        fns_valid_mods[fn_name]['validModifiers'] = list(fns_valid_mods[fn_name]['validModifiers'])
        fns_valid_mods[fn_abbreviation]['validModifiers'] = list(fns_valid_mods[fn_abbreviation]['validModifiers'])

    #####################################
    # TEMPLATING STARTS IN THIS SECTION #
    #####################################

    #####################
    # SYNTAX TEMPLATING #
    #####################

    env = Environment(loader=FileSystemLoader(DIRECTORY_OF_EBNFTEMP_FILE))  # create environment for template
    template = env.get_template(NAME_OF_EBNFTEMP_FILE)  # get the template

    # replace template placeholders with appropriate variables
    ebnf = template.render(functions=functions,
                           m_functions=m_functions,
                           relations=relations,
                           bel_version=bel_version,
                           bel_major_version=bel_major_version,
                           created_time=created_time)

    # make and then write ebnf file into a file defined in the global vars
    with open(NAME_OF_OUTPUT_SYNTAX_FILE, 'w') as ebnf_file:
        ebnf_file.write(ebnf)

    return


def yaml_to_dict(NAME_OF_YAML_FILE):
    ''' Return a dictionary object from the YAML file that is given. '''
    yaml_file = open(NAME_OF_YAML_FILE, 'r').read()
    yaml_dict = yaml.load(yaml_file)

    return yaml_dict


if __name__ == '__main__':
    main()
