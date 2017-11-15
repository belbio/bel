#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Usage: python yaml_to_ebnf.py <version> <path to output .ebnf file>

Use this script to convert the user defined YAML file to two other files:
    - an EBNF file used by Tatsu to compile into a parser (syntax)
"""

import datetime
import logging
import sys
from itertools import chain

import yaml
from bel_lang.bel_specification import get_specification
from jinja2 import Environment, FileSystemLoader

log = logging.getLogger(__name__)

try:
    VERSION = sys.argv[1]  # take a version string as argument, e.g. '2.0.0'
    NAME_OF_OUTPUT_SYNTAX_FILE = sys.argv[2]  # where to output our .ebnf file
except IndexError:
    log.error('USAGE: python yaml_to_ebnf.py <version> <path to output .ebnf file>\n'
              'EXAMPLE: python yaml_to_ebnf.py "2.0.0" "test-output.ebnf"')
    sys.exit()

PATH_OF_EBNFTEMP_FILE = 'bel.ebnf.j2'
PATH_SPLIT = PATH_OF_EBNFTEMP_FILE.rsplit('\\', 1)
DIRECTORY_OF_EBNFTEMP_FILE = '.'  # directory of where our Jinja template is located; use period for same directory
NAME_OF_EBNFTEMP_FILE = PATH_SPLIT[0]  # name of Jinja template for the EBNF file


def main():

    specs = get_specification(VERSION)

    ############
    # METADATA #
    ############

    bel_version = VERSION  # e.g. version 2.1.5
    bel_major_version = VERSION.split('.')[0]  # e.g. version 2
    created_time = datetime.datetime.now().strftime('%B %d, %Y - %I:%M:%S%p')

    #####################
    # SYNTAX TEMPLATING #
    #####################

    env = Environment(loader=FileSystemLoader(DIRECTORY_OF_EBNFTEMP_FILE))  # create environment for template
    template = env.get_template(NAME_OF_EBNFTEMP_FILE)  # get the template

    # replace template placeholders with appropriate variables
    ebnf = template.render(functions=sorted(specs['function_list'], key=len, reverse=True),
                           m_functions=sorted(specs['modifier_list'], key=len, reverse=True),
                           relations=sorted(specs['relation_list'], key=len, reverse=True),
                           bel_version=bel_version,
                           bel_major_version=bel_major_version,
                           created_time=created_time)

    # make and then write ebnf file into a file defined in the global vars
    with open(NAME_OF_OUTPUT_SYNTAX_FILE, 'w') as ebnf_file:
        ebnf_file.write(ebnf)

    return


if __name__ == '__main__':
    main()
