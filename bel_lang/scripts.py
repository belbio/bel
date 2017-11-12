import pprint

import click

from .bel import *


@click.group()
def bel():
    pass


@bel.command(name='parse')
@click.option('--v', default=2.0, help='BEL language version; defaults to 2.0')
@click.option('--s', is_flag=True, help='Enable strict parsing')
@click.argument('statement')
def cli_parse(statement, v, s):
    print('------------------------------')
    print('BEL version: {}'.format(v))
    print('Strict parsing: {}'.format(s))
    print('------------------------------')

    p_obj = parse(statement, version=v, strict=s)
    ast = p_obj.ast

    if ast is None:
        print(p_obj.error)
        print(p_obj.err_visual)
    else:
        pprint.pprint(ast)

    return


@bel.command(name='create')
@click.option('--c', default=1, help='Number of statements to create; defaults to 1')
@click.option('--m', default=3, help='Max number of args for each function; defaults to 3')
@click.option('--v', default=2.0, help='BEL language version; defaults to 2.0')
def cli_create(c, m, v):
    print('------------------------------')
    print('Statements to create: {}'.format(c))
    print('Max args per function: {}'.format(m))
    print('BEL version: {}'.format(v))
    print('------------------------------')

    stmts = create(c, m, v)
    for s in stmts:
        print('{}\n'.format(s.string_form))

    return


@bel.command(name='components')
@click.option('--v', default=2.0, help='BEL language version; defaults to 2.0')
@click.argument('statement')
def cli_components(statement, v):
    print('------------------------------')
    print('BEL version: {}'.format(v))
    print('------------------------------')

    c = stmt_components(statement, version=v)

    print('Subject: {}'.format(c['subject']))
    print('Relationship: {}'.format(c['relation']))
    print('Object: {}'.format(c['object']))

    return


@bel.command(name='validate')
@click.option('--v', default=2.0, help='BEL language version; defaults to 2.0')
@click.option('--s', is_flag=True, help='Enable strict parsing')
@click.argument('statement')
def cli_validate(statement, v, s):
    print('------------------------------')
    print('BEL version: {}'.format(v))
    print('Strict parsing: {}'.format(s))
    print('------------------------------')

    validated = validate(statement, version=v, strict=s)

    print('Valid: {}'.format(True if validated.valid else False))

    return
