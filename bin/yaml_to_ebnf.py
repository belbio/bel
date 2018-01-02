#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Usage: python yaml_to_ebnf.py <version> <path to output .ebnf file>

Use this script to convert the user defined YAML file to two other files:
    - an EBNF file used by Tatsu to compile into a parser (syntax)
"""

import datetime
import logging
import glob
import os.path
import click
from bel.lang.bel_specification import get_specification
from jinja2 import Environment, FileSystemLoader

log = logging.getLogger(__name__)

root_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
tmpl_fn = 'bel.ebnf.j2'


def render_ebnf(tmpl_fn, bel_version, created_time, bel_spec):

    specs = get_specification(bel_version)

    tmpl_dir = os.path.dirname(tmpl_fn)
    tmpl_basename = os.path.basename(tmpl_fn)

    bel_major_version = bel_version.split('.')[0]

    env = Environment(loader=FileSystemLoader(tmpl_dir))  # create environment for template
    template = env.get_template(tmpl_basename)  # get the template

    # replace template placeholders with appropriate variables
    ebnf = template.render(functions=sorted(specs['function_list'], key=len, reverse=True),
                           m_functions=sorted(specs['modifier_list'], key=len, reverse=True),
                           relations=sorted(specs['relation_list'], key=len, reverse=True),
                           bel_version=bel_version,
                           bel_major_version=bel_major_version,
                           created_time=created_time)

    return ebnf


def get_version(belspec_fn: str) -> str:
    """Recover version number from belspec_fn"""

    version = os.path.basename(belspec_fn).replace('bel_v', '').replace('.yaml', '').replace('_', '.')
    return version


def save_ebnf(ebnf_fn, ebnf):
    with open(ebnf_fn, 'w') as f:
        f.write(ebnf)


@click.command()
@click.option('--belspec_fn', help='BEL Language Specification filename')
@click.option('--ebnf_fn', help='Specify EBNF filename')
@click.option('--ebnf_tmpl_fn', default="./bel/lang/versions/bel.ebnf.j2", help='EBNF template filename')
def main(belspec_fn, ebnf_fn, ebnf_tmpl_fn):
    """Create EBNF files from BEL Specification yaml files and template

    If you do not specify any options, then this will process all of the BEL Specification
    files in bel/lang/versions into EBNF files
    """
    created_time = datetime.datetime.now().strftime('%B %d, %Y - %I:%M:%S%p')

    if belspec_fn:
        bel_version = get_version(belspec_fn)
        if not ebnf_fn:
            ebnf_fn = belspec_fn.replace('yaml', 'ebnf')
            print(f'EBNF output file name is: {ebnf_fn}')

        ebnf = render_ebnf(ebnf_tmpl_fn, bel_version, created_time, belspec_fn)
        print(ebnf_fn)
        save_ebnf(ebnf_fn, ebnf)

    else:
        files = glob.glob(f'{root_dir}/bel/lang/versions/bel_v*yaml')
        for fn in files:
            bel_version = get_version(fn)
            bel_spec = get_specification(bel_version)
            ebnf = render_ebnf(tmpl_fn, bel_version, created_time, bel_spec)
            ebnf_fn = fn.replace('yaml', 'ebnf')
            save_ebnf(ebnf_fn, ebnf)


if __name__ == '__main__':
    main()
