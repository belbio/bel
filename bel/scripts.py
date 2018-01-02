import click
import json
import yaml
import gzip
import re

import bel.db

from bel.lang.bel import BEL

import bel.nanopub.nanopubs as bnn
import bel.nanopub.files as bnf
import bel.nanopub.utils as utils
import bel.nanopub.belscripts

import bel.Config
from bel.Config import config

import logging
import logging.config

logging.config.dictConfig(config['logging'])
log = logging.getLogger(__name__)


class Context(object):
    def __init__(self):
        self.config = config


pass_context = click.make_pass_decorator(Context, ensure=True)


@click.group()
def bel():
    """ BEL commands

    Uses first file found to load in default configuration:
        ./belbio_conf.yaml
        ./.belbio_conf
        ~/.belbio_conf
    """
    pass


@bel.group()
def nanopub():
    """Nanopub specific commands"""

    pass


@bel.command()
@click.argument('input_fn')
@click.option('--output_fn', default='-', help="BEL Edges output filename - defaults to STDOUT")
@click.option('--rules', help='Select specific rules to create BEL Edges, comma-delimited, e.g. "component_of,degradation", default is to run all rules. Special rule: "skip" does not compute edges at all - just processes primary edge')
@click.option('--species_id', help='Species ID format TAX:<tax_id_number>')
@click.option('--namespace_targets', help='Target namespaces for canonicalizing BEL, e.g. {"HGNC": ["EG", "SP"], "CHEMBL": ["CHEBI"]}')
@click.option('--version', help='BEL language version')
@click.option('--api', help='API Endpoint to use for BEL Entity validation')
@click.option('--config_fn', help="BEL Pipeline configuration file - overrides default configuration files")
@pass_context
def pipeline(ctx, input_fn, output_fn, rules, species_id, namespace_targets, version, api, config_fn):
    """BEL Pipeline - BEL Nanopubs into BEL Edges

    This will process BEL Nanopubs into BEL Edges by validating, orthologizing (if requested),
    canonicalizing, and then computing the BEL Edges based on the given rule_set.

    \b
    input_fn:
        If input fn has *.gz, will read as a gzip file
        If input fn has *.jsonl*, will parsed as a JSONLines file
        IF input fn has *.json*, will be parsed as a JSON file
        If input fn has *.yaml* or *.yml*,  will be parsed as a YAML file

    \b
    output_fn:
        If output fn has *.gz, will written as a gzip file
        If output fn has *.jsonl*, will written as a JSONLines file
        IF output fn has *.json*, will be written as a JSON file
        If output fn has *.yaml* or *.yml*,  will be written as a YAML file
        If output fn has *.jgf, will be written as JSON Graph Formatted file
    """

    if config_fn:
        config = bel.db.Config.merge_config(ctx.config, override_config_fn=config_fn)
    else:
        config = ctx.config

    # Configuration - will return the first truthy result in list else the default option
    if namespace_targets:
        namespace_targets = json.loads(namespace_targets)
    if rules:
        rules = rules.replace(' ', '').split(',')

    namespace_targets = utils.first_true([namespace_targets, config['bel']['lang'].get('canonical')], None)
    rules = utils.first_true([rules, config['bel']['nanopub'].get('pipeline_edge_rules', False)], False)
    api = utils.first_true([api, config['bel_api']['servers'].get('api_url', None)], None)
    version = utils.first_true([version, config['bel']['lang'].get('default_bel_version', None)], None)

    n = bnn.Nanopub()

    try:
        json_flag, jsonl_flag, yaml_flag, jgf_flag = False, False, False, False
        all_bel_edges = []
        if re.search('ya?ml', output_fn):
            yaml_flag = True
        elif 'jsonl' in output_fn:
            jsonl_flag = True
        elif 'json' in output_fn:
            json_flag = True
        elif 'jgf' in output_fn:
            jgf_flag = True

        if 'gz' in output_fn:
            fout = gzip.open(output_fn, 'wt')
        else:
            fout = open(output_fn, 'wt')

        for np in bnf.read_nanopubs(input_fn):
            # print('Nanopub:\n', json.dumps(np, indent=4))

            (bel_edges, validation_messages) = n.bel_edges(np, namespace_targets=namespace_targets, orthologize_target=species_id, rules=rules)

            # Skip if there was a validation error
            if [error for error in validation_messages if error[0] == 'ERROR']:
                continue

            if jsonl_flag:
                fout.write("{}\n".format(json.dumps(bel_edges)))
            else:
                all_bel_edges.extend(bel_edges)

            if validation_messages:
                log.warn(validation_messages)

        if yaml_flag:
            fout.write("{}\n".format(yaml.dumps(all_bel_edges)))
        elif json_flag:
            fout.write("{}\n".format(json.dumps(all_bel_edges)))
        elif jgf_flag:
            bnf.edges_to_jgf(output_fn, all_bel_edges)

    finally:
        fout.close()


@nanopub.command(name="validate")
@click.option('--output_fn', type=click.File('wt'), default='-', help="BEL Edges JSON output filename - defaults to STDOUT")
@click.option('--api', help='BEL.bio API endpoint')
@click.option('--config_fn', help="BEL Pipeline configuration file - overrides default configuration files")
@click.argument('input_fn')
@pass_context
def nanopub_validate(ctx, input_fn, output_fn, api, config_fn):
    """Validate nanopubs"""

    if config_fn:
        config = bel.db.Config.merge_config(ctx.config, override_config_fn=config_fn)
    else:
        config = ctx.config

    api = utils.first_true([api, config['bel_api']['servers'].get('api_url', None)], None)

    print(f"Running validate nanopubs using {api}")

    # if target:
    #     with open(target, 'w') as h:
    #         h.write(content)
    # else:
    #     sys.stdout.write(content)


@nanopub.command(name="belscript")
@click.option('--output_fn', help="BEL Edges JSON output filename - defaults to STDOUT")
@click.argument('input_fn')
@pass_context
def convert_belscript(ctx, input_fn, output_fn):
    """Convert belscript to nanopubs_bel format

    This will convert the OpenBEL BELScript file format to
    nanopub_bel-1.0.0 format.

    \b
    input_fn:
        If input fn has *.gz, will read as a gzip file

    \b
    output_fn:
        If output fn has *.gz, will written as a gzip file
        If output fn has *.jsonl*, will written as a JSONLines file
        IF output fn has *.json*, will be written as a JSON file
        If output fn has *.yaml* or *.yml*,  will be written as a YAML file
    """

    try:
        # output file
        if re.search('gz$', output_fn):
            fout = gzip.open(output_fn, 'wt')
        else:
            fout = open(output_fn, 'wt')

        # set output flags
        json_flag, jsonl_flag, yaml_flag = False, False, False
        if re.search('ya?ml', output_fn):
            yaml_flag = True
            docs = []
        elif 'jsonl' in output_fn:
            jsonl_flag = True
        elif 'json' in output_fn:
            json_flag = True
            docs = []

        # input file
        if re.search('gz$', input_fn):
            f = gzip.open(input_fn, 'rt')
        else:
            f = open(input_fn, 'rt')

        # process belscript
        for doc in bel.nanopub.belscripts.parse_belscript(f):
            if yaml_flag or json_flag:
                docs.append(doc)
            elif jsonl_flag:
                fout.write("{}\n".format(json.dumps(doc)))

        if yaml_flag:
            fout.write("{}\n".format(yaml.dumps(docs)))
        elif json_flag:
            fout.write("{}\n".format(json.dumps(docs)))

    finally:
        f.close()
        fout.close()


@bel.group()
def stmt():
    """BEL Statement specific commands"""

    pass


@stmt.command(name='validate')
@click.option('--version', help='BEL language version')
@click.option('--api', help='API Endpoint to use for BEL Entity validation')
@click.option('--config_fn', help="BEL Pipeline configuration file - overrides default configuration files")
@click.argument('statement')
@pass_context
def stmt_validate(ctx, statement, version, api, config_fn):
    """Parse statement and validate """

    if config_fn:
        config = bel.db.Config.merge_config(ctx.config, override_config_fn=config_fn)
    else:
        config = ctx.config

    # Configuration - will return the first truthy result in list else the default option
    api = utils.first_true([api, config['bel_api']['servers'].get('api_url', None)], None)
    version = utils.first_true([version, config['bel']['lang'].get('default_bel_version', None)], None)

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


@stmt.command()
@click.option('--namespace_targets', help='Target namespaces for canonicalizing BEL, e.g. {"HGNC": ["EG", "SP"], "CHEMBL": ["CHEBI"]}')
@click.option('--version', help='BEL language version')
@click.option('--api', help='API Endpoint to use for BEL Entity validation')
@click.option('--config_fn', help="BEL Pipeline configuration file - overrides default configuration files")
@click.argument('statement')
@pass_context
def canonicalize(ctx, statement, namespace_targets, version, api, config_fn):
    """Canonicalize statement

    Target namespaces can be provided in the following manner:

        belstmt canonicalize "<BELStmt>" --namespace_targets '{"HGNC": ["EG", "SP"], "CHEMBL": ["CHEBI"]}'
            the value of target_namespaces must be JSON and embedded in single quotes
            reserving double quotes for the dictionary elements
    """

    if config_fn:
        config = bel.db.Config.merge_config(ctx.config, override_config_fn=config_fn)
    else:
        config = ctx.config

    # Configuration - will return the first truthy result in list else the default option
    if namespace_targets:
        namespace_targets = json.loads(namespace_targets)

    namespace_targets = utils.first_true([namespace_targets, config.get('canonical')], None)
    api = utils.first_true([api, config.get('api', None)], None)
    version = utils.first_true([version, config.get('bel_version', None)], None)

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


@stmt.command()
@click.option('--species_id', help='Species ID format TAX:<tax_id_number>')
@click.option('--version', help='BEL language version')
@click.option('--api', help='API Endpoint to use for BEL Entity validation')
@click.option('--config_fn', help="BEL Pipeline configuration file - overrides default configuration files")
@click.argument('statement')
@pass_context
def orthologize(ctx, statement, species_id, version, api, config_fn):
    """Canonicalize statement

    Species ID needs to be the NCBI Taxonomy ID in this format: TAX:<tax_id_number>
    You can use the following common names for species_id: human, mouse, rat
      (basically whatever is supported at the api orthologs endpoint)
    """

    if config_fn:
        config = bel.db.Config.merge_config(ctx.config, override_config_fn=config_fn)
    else:
        config = ctx.config

    # Configuration - will return the first truthy result in list else the default option
    api_url = utils.first_true([api, config['bel_api']['servers'].get('api_url', None)], None)
    version = utils.first_true([version, config['bel']['lang'].get('default_bel_version', None)], None)

    print('------------------------------')
    print('BEL version: {}'.format(version))
    print('API Endpoint: {}'.format(api))
    print('------------------------------')

    bo = BEL(version=version, endpoint=api_url)
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


@stmt.command()
@click.option('--rules', help='Select specific rules to create BEL Edges, comma-delimited, e.g. "component_of,degradation", default is to run all rules')
@click.option('--species_id', help='Species ID format TAX:<tax_id_number>')
@click.option('--namespace_targets', help='Target namespaces for canonicalizing BEL, e.g. {"HGNC": ["EG", "SP"], "CHEMBL": ["CHEBI"]}')
@click.option('--version', help='BEL language version')
@click.option('--api', help='API Endpoint to use for BEL Entity validation')
@click.option('--config_fn', help="BEL Pipeline configuration file - overrides default configuration files")
@click.argument('statement')
@pass_context
def edges(ctx, statement, rules, species_id, namespace_targets, version, api, config_fn):
    """Create BEL Edges"""

    if config_fn:
        config = bel.db.Config.merge_config(ctx.config, override_config_fn=config_fn)
    else:
        config = ctx.config

    # Configuration - will return the first truthy result in list else the default option
    if namespace_targets:
        namespace_targets = json.loads(namespace_targets)
    if rules:
        rules = rules.replace(' ', '').split(',')

    namespace_targets = utils.first_true([namespace_targets, config['bel']['lang'].get('canonical')], None)
    api_url = utils.first_true([api, config['bel_api']['servers'].get('api_url', None)], None)
    version = utils.first_true([version, config['bel']['lang'].get('default_bel_version', None)], None)

    print('------------------------------')
    print('BEL version: {}'.format(version))
    print('API Endpoint: {}'.format(api))
    print('------------------------------')

    bo = BEL(version=version, endpoint=api_url)
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


@bel.group()
def db():
    """Database specific commands"""
    pass


@bel.command()
@click.option('--clean/--no-clean', default=False, help="Remove indexes and re-create them")
@click.option('--index_name', default='terms_blue', help='Use this name for index. Default is "terms_blue"')
def elasticsearch(clean, index_name):
    """Setup Elasticsearch term indexes

    This will by default only create the indexes and run the term index mapping
    if the indexes don't exist.  The --clean option will force removal of the
    index if it exists.

    The index_name should be aliased to the index 'terms' when it's ready
    """

    es = bel.db.elasticsearch.get_client()

    bel.db.elasticsearch.create_terms_index(es, index_name)
