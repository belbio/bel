#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""


"""

# Standard Library
import copy
import gzip
import json
import re
import sys
from typing import Any, Iterable, List, Mapping, Tuple

# Third Party
# Third Party Imports
import click
import yaml
from loguru import logger


def read_nanopubs(fn: str) -> Iterable[Mapping[str, Any]]:
    """Read file and generate nanopubs

    If filename has *.gz, will read as a gzip file
    If filename has *.jsonl*, will parsed as a JSONLines file
    IF filename has *.json*, will be parsed as a JSON file
    If filename has *.yaml* or *.yml*,  will be parsed as a YAML file

    Args:
        filename (str): filename to read nanopubs from

    Returns:
        Generator[Mapping[str, Any]]: generator of nanopubs in nanopub_bel JSON Schema format
    """

    jsonl_flag, json_flag, yaml_flag = False, False, False
    if fn == "-" or "jsonl" in fn:
        jsonl_flag = True
    elif "json" in fn:
        json_flag = True
    elif re.search("ya?ml", fn):
        yaml_flag = True
    else:
        logger.error("Do not recognize nanopub file format - neither json nor jsonl format.")
        return {}

    try:
        if re.search("gz$", fn):
            f = gzip.open(fn, "rt")
        else:
            try:
                f = click.open_file(fn, mode="rt")
            except Exception as e:
                logger.info(f"Can not open file {fn}  Error: {e}")
                quit()

        if jsonl_flag:
            for line in f:
                yield json.loads(line)
        elif json_flag:
            nanopubs = json.load(f)
            for nanopub in nanopubs:
                yield nanopub
        elif yaml_flag:
            nanopubs = yaml.load(f, Loader=yaml.SafeLoader)
            for nanopub in nanopubs:
                yield nanopub

    except Exception as e:
        logger.exception(f"Could not open file: {fn}")


def create_nanopubs_fh(output_fn: str):
    """Create Nanopubs output filehandle

    \b
    If output fn is '-' will write JSONlines to STDOUT
    If output fn has *.gz, will written as a gzip file
    If output fn has *.jsonl*, will written as a JSONLines file
    IF output fn has *.json*, will be written as a JSON file
    If output fn has *.yaml* or *.yml*,  will be written as a YAML file

    Args:
        output_fn: Name of output file

    Returns:
        (filehandle, yaml_flag, jsonl_flag, json_flag)
    """

    # output file
    # set output flags
    json_flag, jsonl_flag, yaml_flag = False, False, False
    if output_fn:
        if re.search("gz$", output_fn):
            out_fh = gzip.open(output_fn, "wt")
        else:
            out_fh = click.open_file(output_fn, mode="wt")

        if re.search("ya?ml", output_fn):
            yaml_flag = True
        elif "jsonl" in output_fn or "-" == output_fn:
            jsonl_flag = True
        elif "json" in output_fn:
            json_flag = True

    else:
        out_fh = sys.stdout

    return (out_fh, yaml_flag, jsonl_flag, json_flag)


def main():
    pass


if __name__ == "__main__":
    main()
