# Standard Library
import gzip
import json
import logging
import logging.config
import re
import sys

# Third Party Imports
import click
import timy
import yaml

# Local Imports
import bel.Config
import bel.db.arangodb
import bel.db.elasticsearch
import bel.edge.edges
import bel.nanopub.belscripts
import bel.nanopub.files as bnf
import bel.nanopub.nanopubs as bnn
import bel.utils as utils
from bel.Config import config
from bel.lang.belobj import BEL

if config.get("logging", False):
    logging.config.dictConfig(config.get("logging"))
log = logging.getLogger(__name__)


# Add -h to help options for commands
CONTEXT_SETTINGS = dict(help_option_names=["-h", "--help"])


class Context(object):
    def __init__(self):
        self.config = config


pass_context = click.make_pass_decorator(Context, ensure=True)


@click.group(context_settings=CONTEXT_SETTINGS)
def belc():
    """ BEL commands

    Uses first file found to load in default configuration:

        ./belbio_conf.yaml
        ./.belbio_conf
        ~/.belbio_conf
    """
    pass


@belc.group()
def nanopub():
    """Nanopub specific commands"""

    pass


@nanopub.command(name="validate", context_settings=CONTEXT_SETTINGS)
@click.option(
    "--output_fn",
    type=click.File("wt"),
    default="-",
    help="BEL Edges JSON output filename - defaults to STDOUT",
)
@click.option("--api", help="BEL.bio API endpoint")
@click.option(
    "--config_fn", help="BEL Pipeline configuration file - overrides default configuration files"
)
@click.argument("input_fn")
@pass_context
def nanopub_validate(ctx, input_fn, output_fn, api, config_fn):
    """Validate nanopubs"""

    if config_fn:
        config = bel.db.Config.merge_config(ctx.config, override_config_fn=config_fn)
    else:
        config = ctx.config

    api = utils.first_true([api, config["bel_api"]["servers"].get("api_url", None)], None)

    print(f"Running validate nanopubs using {api}")

    # if target:
    #     with open(target, 'w') as h:
    #         h.write(content)
    # else:
    #     sys.stdout.write(content)


@nanopub.command(name="belscript", context_settings=CONTEXT_SETTINGS)
@click.option("--input_fn", "-i", default="-")
@click.option("--output_fn", "-o", default="-")
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

        (out_fh, yaml_flag, jsonl_flag, json_flag) = bel.nanopub.files.create_nanopubs_fh(output_fn)
        if yaml_flag or json_flag:
            docs = []

        # input file
        if re.search("gz$", input_fn):
            f = gzip.open(input_fn, "rt")
        else:
            f = open(input_fn, "rt")

        # process belscript
        for doc in bel.nanopub.belscripts.parse_belscript(f):
            if yaml_flag or json_flag:
                docs.append(doc)
            elif jsonl_flag:
                out_fh.write("{}\n".format(json.dumps(doc)))

        if yaml_flag:
            yaml.dump(docs, out_fh)

        elif json_flag:
            json.dump(docs, out_fh, indent=4)

    finally:
        f.close()
        out_fh.close()


@nanopub.command(name="reformat", context_settings=CONTEXT_SETTINGS)
@click.option("--input_fn", "-i")
@click.option("--output_fn", "-o")
@pass_context
def reformat(ctx, input_fn, output_fn):
    """Reformat between JSON, YAML, JSONLines formats

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

        (out_fh, yaml_flag, jsonl_flag, json_flag) = bel.nanopub.files.create_nanopubs_fh(output_fn)
        if yaml_flag or json_flag:
            docs = []

        # input file
        if re.search("gz$", input_fn):
            f = gzip.open(input_fn, "rt")
        else:
            f = open(input_fn, "rt")

        for np in bnf.read_nanopubs(input_fn):
            if yaml_flag or json_flag:
                docs.append(np)
            elif jsonl_flag:
                out_fh.write("{}\n".format(json.dumps(np)))

        if yaml_flag:
            yaml.dump(docs, out_fh)

        elif json_flag:
            json.dump(docs, out_fh, indent=4)

    finally:
        f.close()
        out_fh.close()


@nanopub.command(name="stats", context_settings=CONTEXT_SETTINGS)
@click.argument("input_fn")
@pass_context
def nanopub_stats(ctx, input_fn):
    """Collect statistics on nanopub file

    input_fn can be json, jsonl or yaml and additionally gzipped
    """

    counts = {
        "nanopubs": 0,
        "assertions": {"total": 0, "subject_only": 0, "nested": 0, "relations": {}},
    }

    for np in bnf.read_nanopubs(input_fn):
        if "nanopub" in np:
            counts["nanopubs"] += 1
            counts["assertions"]["total"] += len(np["nanopub"]["assertions"])
            for assertion in np["nanopub"]["assertions"]:
                if assertion["relation"] is None:
                    counts["assertions"]["subject_only"] += 1
                else:
                    if re.match("\s*\(", assertion["object"]):
                        counts["assertions"]["nested"] += 1

                    if not assertion.get("relation") in counts["assertions"]["relations"]:
                        counts["assertions"]["relations"][assertion.get("relation")] = 1
                    else:
                        counts["assertions"]["relations"][assertion.get("relation")] += 1

    counts["assertions"]["relations"] = sorted(counts["assertions"]["relations"])

    print("DumpVar:\n", json.dumps(counts, indent=4))


@belc.group()
def stmt():
    """BEL Statement specific commands"""

    pass


@stmt.command(name="validate", context_settings=CONTEXT_SETTINGS)
@click.option("--version", help="BEL language version")
@click.option("--api", help="API Endpoint to use for BEL Entity validation")
@click.option(
    "--config_fn", help="BEL Pipeline configuration file - overrides default configuration files"
)
@click.argument("statement")
@pass_context
def stmt_validate(ctx, statement, version, api, config_fn):
    """Parse statement and validate """

    if config_fn:
        config = bel.db.Config.merge_config(ctx.config, override_config_fn=config_fn)
    else:
        config = ctx.config

    # Configuration - will return the first truthy result in list else the default option
    api = utils.first_true([api, config["bel_api"]["servers"].get("api_url", None)], None)
    version = utils.first_true(
        [version, config["bel"]["lang"].get("default_bel_version", None)], None
    )

    print("------------------------------")
    print("BEL version: {}".format(version))
    print("API Endpoint: {}".format(api))
    print("------------------------------")

    bo = BEL(version=version, endpoint=api)
    bo.parse(statement)

    if bo.ast is None:
        print(bo.original_bel_stmt)
        print(bo.parse_visualize_error)
        print(bo.validation_messages)
    else:
        print(bo.ast.to_triple())
        if bo.validation_messages:
            print(bo.validation_messages)
        else:
            print("No problems found")
    return


@stmt.command()
@click.option(
    "--namespace_targets",
    help='Target namespaces for canonicalizing BEL, e.g. {"HGNC": ["EG", "SP"], "CHEMBL": ["CHEBI"]}',
)
@click.option("--version", help="BEL language version")
@click.option("--api", help="API Endpoint to use for BEL Entity validation")
@click.option(
    "--config_fn", help="BEL Pipeline configuration file - overrides default configuration files"
)
@click.argument("statement")
@pass_context
def canonicalize(ctx, statement, namespace_targets, version, api, config_fn):
    """Canonicalize statement

    Target namespaces can be provided in the following manner:

        bel stmt canonicalize "<BELStmt>" --namespace_targets '{"HGNC": ["EG", "SP"], "CHEMBL": ["CHEBI"]}'
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

    namespace_targets = utils.first_true([namespace_targets, config.get("canonical")], None)
    api = utils.first_true([api, config.get("api", None)], None)
    version = utils.first_true([version, config.get("bel_version", None)], None)

    print("------------------------------")
    print("BEL version: {}".format(version))
    print("API Endpoint: {}".format(api))
    print("------------------------------")

    bo = BEL(version=version, endpoint=api)
    bo.parse(statement).canonicalize(namespace_targets=namespace_targets)

    if bo.ast is None:
        print(bo.original_bel_stmt)
        print(bo.parse_visualize_error)
        print(bo.validation_messages)
    else:
        print("ORIGINAL ", bo.original_bel_stmt)
        print("CANONICAL", bo.ast)
        if bo.validation_messages:
            print(bo.validation_messages)
        else:
            print("No problems found")
    return


@stmt.command()
@click.option("--species", help="species ID format TAX:<tax_id_number>")
@click.option("--version", help="BEL language version")
@click.option("--api", help="API Endpoint to use for BEL Entity validation")
@click.option(
    "--config_fn", help="BEL Pipeline configuration file - overrides default configuration files"
)
@click.argument("statement")
@pass_context
def orthologize(ctx, statement, species, version, api, config_fn):
    """Orthologize statement

    species ID needs to be the NCBI Taxonomy ID in this format: TAX:<tax_id_number>
    You can use the following common names for species id: human, mouse, rat
      (basically whatever is supported at the api orthologs endpoint)
    """

    if config_fn:
        config = bel.db.Config.merge_config(ctx.config, override_config_fn=config_fn)
    else:
        config = ctx.config

    # Configuration - will return the first truthy result in list else the default option
    api_url = utils.first_true([api, config["bel_api"]["servers"].get("api_url", None)], None)
    version = utils.first_true(
        [version, config["bel"]["lang"].get("default_bel_version", None)], None
    )

    print("------------------------------")
    print("BEL version: {}".format(version))
    print("API Endpoint: {}".format(api))
    print("------------------------------")

    bo = BEL(version=version, endpoint=api_url)
    bo.parse(statement).orthologize(species)

    if bo.ast is None:
        print(bo.original_bel_stmt)
        print(bo.parse_visualize_error)
        print(bo.validation_messages)
    else:
        print("ORIGINAL     ", bo.original_bel_stmt)
        print("ORTHOLOGIZED ", bo.ast)
        if bo.validation_messages:
            print(bo.validation_messages)
        else:
            print("No problems found")
    return


@stmt.command()
@click.option(
    "--rules",
    help='Select specific rules to create BEL Edges, comma-delimited, e.g. "component_of,degradation", default is to run all rules',
)
@click.option("--species", help="Species ID format TAX:<tax_id_number>")
@click.option(
    "--namespace_targets",
    help='Target namespaces for canonicalizing BEL, e.g. {"HGNC": ["EG", "SP"], "CHEMBL": ["CHEBI"]}',
)
@click.option("--version", help="BEL language version")
@click.option("--api", help="API Endpoint to use for BEL Entity validation")
@click.option(
    "--config_fn", help="BEL Pipeline configuration file - overrides default configuration files"
)
@click.argument("statement")
@pass_context
def edges(ctx, statement, rules, species, namespace_targets, version, api, config_fn):
    """Create BEL Edges from BEL Statement"""

    if config_fn:
        config = bel.db.Config.merge_config(ctx.config, override_config_fn=config_fn)
    else:
        config = ctx.config

    # Configuration - will return the first truthy result in list else the default option
    if namespace_targets:
        namespace_targets = json.loads(namespace_targets)
    if rules:
        rules = rules.replace(" ", "").split(",")

    namespace_targets = utils.first_true(
        [namespace_targets, config["bel"]["lang"].get("canonical")], None
    )
    api_url = utils.first_true([api, config["bel_api"]["servers"].get("api_url", None)], None)
    version = utils.first_true(
        [version, config["bel"]["lang"].get("default_bel_version", None)], None
    )

    print("------------------------------")
    print("BEL version: {}".format(version))
    print("API Endpoint: {}".format(api))
    print("------------------------------")

    bo = BEL(version=version, endpoint=api_url)
    if species:
        edges = (
            bo.parse(statement)
            .orthologize(species)
            .canonicalize(namespace_targets=namespace_targets)
            .compute_edges(rules=rules)
        )
    else:
        edges = (
            bo.parse(statement)
            .canonicalize(namespace_targets=namespace_targets)
            .compute_edges(rules=rules)
        )

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


@belc.group()
def db():
    """Database specific commands"""
    pass


@db.command()
@click.option("--delete/--no-delete", default=False, help="Remove indexes and re-create them")
@click.option(
    "--index_name", default="terms_blue", help='Use this name for index. Default is "terms_blue"'
)
def elasticsearch(delete, index_name):
    """Setup Elasticsearch namespace indexes

    This will by default only create the indexes and run the namespace index mapping
    if the indexes don't exist.  The --delete option will force removal of the
    index if it exists.

    The index_name should be aliased to the index 'terms' when it's ready"""

    if delete:
        bel.db.elasticsearch.get_client(delete=True)
    else:
        bel.db.elasticsearch.get_client()


@db.command()
@click.argument("db_name", default="belns")
@click.option("--delete/--no-delete", default=False, help="Remove indexes and re-create them")
def arangodb(delete, db_name):
    """Setup ArangoDB database

    db_name: defaults to belns

    This will create the database, collections and indexes on the collection if it doesn't exist.

    The --delete option will force removal of the database if it exists."""

    if delete:
        arango_client = bel.db.arangodb.get_client()
        if not arango_client:
            print("Cannot setup database without ArangoDB access")
            quit()
        bel.db.arangodb.delete_database(arango_client, db_name)

    if db_name == "belns":
        bel.db.arangodb.get_belns_handle(client)
