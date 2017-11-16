import pprint
import click
import os
import yaml
import json

from bel_lang.bel import BEL

import logging

logging.basicConfig(level=logging.INFO)
logging.getLogger("urllib3").setLevel(logging.WARNING)

log = logging.getLogger(__name__)


def first_true(iterable, default=False, pred=None):
    """Returns the first true value in the iterable.

    If no true value is found, returns *default*

    If *pred* is not None, returns the first item
    for which pred(item) is true.

    """
    # first_true([a,b,c], x) --> a or b or c or x
    # first_true([a,b], x, f) --> a if f(a) else b if f(b) else x
    return next(filter(pred, iterable), default)


def get_config(fn):
    """Get config from file"""

    try:
        with open(os.path.expanduser(fn), 'r') as f:
            config = yaml.load(f)
        return config
    except Exception:
        return {}


class Context(object):
    def __init__(self):
        self.config = {}
        for fn in ['./belbio_conf.yaml', './.belbio_conf', '~/.belbio_conf', ]:
            if os.path.isfile(os.path.expanduser(fn)):
                self.config = get_config(fn)
                break


pass_context = click.make_pass_decorator(Context, ensure=True)


@click.group()
def bel():
    """BEL Statement commands

    Uses first file found to load in default configuration:
        ./belbio_conf.yaml
        ./.belbio_conf
        ~/.belbio_conf
    """
    pass


@bel.command(name='validate')
@click.option('--version', help='BEL language version')
@click.option('--api', help='API Endpoint to use for BEL Entity validation')
@click.option('--config', help="BEL Pipeline configuration file - overrides default configuration files")
@click.argument('statement')
@pass_context
def validate(ctx, statement, version, api, config):
    """Parse statement and validate """

    # Configuration - will return the first truthy result in list else the default option
    config = first_true([get_config(config), ctx.config], {})
    api = first_true([api, config.get('api', None)], None)
    version = first_true([version, config.get('bel_version', None)], None)

    print('------------------------------')
    print('BEL version: {}'.format(version))
    print('API Endpoint: {}'.format(api))
    print('------------------------------')

    bo = BEL(version=version, endpoint=api)
    bo.parse(statement)

    if bo.ast is None:
        print(bo.original_bel_stmt)
        print(bo.parse_visualize_error)
        print(bo.validation_messages)
    else:
        print(bo.ast.to_components())
        if bo.validation_messages:
            print(bo.validation_messages)
        else:
            print("No problems found")
    return


@bel.command()
@click.option('--namespace_targets', help='Target namespaces for canonicalizing BEL, e.g. {"HGNC": ["EG", "SP"], "CHEMBL": ["CHEBI"]}')
@click.option('--version', help='BEL language version')
@click.option('--api', help='API Endpoint to use for BEL Entity validation')
@click.option('--config', help="BEL Pipeline configuration file - overrides default configuration files")
@click.argument('statement')
@pass_context
def canonicalize(ctx, statement, namespace_targets, version, api, config):
    """Canonicalize statement

    Target namespaces can be provided in the following manner:

        belstmt canonicalize "<BELStmt>" --namespace_targets '{"HGNC": ["EG", "SP"], "CHEMBL": ["CHEBI"]}'
            the value of target_namespaces must be JSON and embedded in single quotes
            reserving double quotes for the dictionary elements
    """

    # Configuration - will return the first truthy result in list else the default option
    if namespace_targets:
        namespace_targets = json.loads(namespace_targets)
    config = first_true([get_config(config), ctx.config], {})
    namespace_targets = first_true([namespace_targets, config.get('canonical')], None)
    api = first_true([api, config.get('api', None)], None)
    version = first_true([version, config.get('bel_version', None)], None)

    print('------------------------------')
    print('BEL version: {}'.format(version))
    print('API Endpoint: {}'.format(api))
    print('------------------------------')

    bo = BEL(version=version, endpoint=api)
    bo.parse(statement).canonicalize(namespace_targets=namespace_targets)

    if bo.ast is None:
        print(bo.original_bel_stmt)
        print(bo.parse_visualize_error)
        print(bo.validation_messages)
    else:
        print('ORIGINAL ', bo.original_bel_stmt)
        print('CANONICAL', bo.ast)
        if bo.validation_messages:
            print(bo.validation_messages)
        else:
            print("No problems found")
    return


@bel.command()
@click.option('--species_id', help='Species ID format TAX:<tax_id_number>')
@click.option('--version', help='BEL language version')
@click.option('--api', help='API Endpoint to use for BEL Entity validation')
@click.option('--config', help="BEL Pipeline configuration file - overrides default configuration files")
@click.argument('statement')
@pass_context
def orthologize(ctx, statement, species_id, version, api, config):
    """Canonicalize statement

    Species ID needs to be the NCBI Taxonomy ID in this format: TAX:<tax_id_number>
    You can use the following common names for species_id: human, mouse, rat
      (basically whatever is supported at the api orthologs endpoint)
    """

    # Configuration - will return the first truthy result in list else the default option
    config = first_true([get_config(config), ctx.config], {})
    api = first_true([api, config.get('api', None)], None)
    version = first_true([version, config.get('bel_version', None)], None)

    print('------------------------------')
    print('BEL version: {}'.format(version))
    print('API Endpoint: {}'.format(api))
    print('------------------------------')

    bo = BEL(version=version, endpoint=api)
    bo.parse(statement).orthologize(species_id)

    if bo.ast is None:
        print(bo.original_bel_stmt)
        print(bo.parse_visualize_error)
        print(bo.validation_messages)
    else:
        print('ORIGINAL     ', bo.original_bel_stmt)
        print('ORTHOLOGIZED ', bo.ast)
        if bo.validation_messages:
            print(bo.validation_messages)
        else:
            print("No problems found")
    return


@bel.command()
@click.option('--rules', help='Select specific rules to create BEL Edges, comma-delimited, e.g. "component_of,degradation", default is to run all rules')
@click.option('--species_id', help='Species ID format TAX:<tax_id_number>')
@click.option('--namespace_targets', help='Target namespaces for canonicalizing BEL, e.g. {"HGNC": ["EG", "SP"], "CHEMBL": ["CHEBI"]}')
@click.option('--version', help='BEL language version')
@click.option('--api', help='API Endpoint to use for BEL Entity validation')
@click.option('--config', help="BEL Pipeline configuration file - overrides default configuration files")
@click.argument('statement')
@pass_context
def edges(ctx, statement, rules, species_id, namespace_targets, version, api, config):
    """Create BEL Edges"""

    # Configuration - will return the first truthy result in list else the default option
    if namespace_targets:
        namespace_targets = json.loads(namespace_targets)
    if rules:
        rules = rules.replace(' ', '').split(',')
    config = first_true([get_config(config), ctx.config], {})
    namespace_targets = first_true([namespace_targets, config.get('canonical')], None)
    api = first_true([api, config.get('api', None)], None)
    version = first_true([version, config.get('bel_version', None)], None)

    print('------------------------------')
    print('BEL version: {}'.format(version))
    print('API Endpoint: {}'.format(api))
    print('------------------------------')

    bo = BEL(version=version, endpoint=api)
    if species_id:
        edges = bo.parse(statement).orthologize(species_id).canonicalize(namespace_targets=namespace_targets).compute_edges(rules=rules)
    else:
        edges = bo.parse(statement).canonicalize(namespace_targets=namespace_targets).compute_edges(rules=rules)

    if edges is None:
        print(bo.original_bel_stmt)
        print(bo.parse_visualize_error)
        print(bo.validation_messages)
    else:
        print(json.dumps(edges, indent=4))

        if bo.validation_messages:
            print(bo.validation_messages)
        else:
            print("No problems found")
    return

