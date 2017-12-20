#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Usage: python yaml_to_ebnf.py <version> <path to output .ebnf file>

Use this script to convert the user defined YAML file to two other files:
    - an EBNF file used by Tatsu to compile into a parser (syntax)
"""

import click
import tatsu
import glob
import os

root_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))


@click.command()
@click.option('--parser_fn', help='Specify resulting BEL Parser filename')
@click.option('--ebnf_fn', help='Specify EBNF input filename')
def main(ebnf_fn, parser_fn):
    """Create BEL Parser file from EBNF file

    If you do not specify any options, then this will process all of the BEL EBNF
    files in bel_lang/versions into EBNF files
    """

    files = glob.glob(f'{root_dir}/bel_lang/versions/bel_v*ebnf')
    for fn in files:
        parser_fn = fn.replace('bel_v', 'parser_v').replace('ebnf', 'py')
        with open(fn, 'r') as f:
            grammar = f.read()

        print('Creating Parser:', parser_fn)
        parser = tatsu.to_python_sourcecode(grammar, filename=parser_fn)
        with open(parser_fn, 'wt') as f:
            f.write(parser)



if __name__ == '__main__':
    main()
