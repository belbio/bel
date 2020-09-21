#!/usr/bin/env python3.6
# -*- coding: utf-8 -*-

"""
Process belscripts content into nanopubs_bel-1.0.0 format for use in BEL.bio

BEL Script format documented here:

    https://wiki.openbel.org/display/BFD/BEL+Script+V2.0+Format

Notes:
    * Don't check that document and definition sections are at top of doc
    *
"""

# Standard Library
import collections
import copy
import csv
import gzip
import json
import re
import sys

# Third Party
import yaml
from loguru import logger

# citation fields are document type, a document name, a document reference ID, and an optional publication date, authors list and comment field

nanopub_type = {"name": "BEL", "version": "2.0.0"}


def convert_csv_str_to_list(csv_str: str) -> list:
    """Convert CSV str to list"""

    csv_str = re.sub("^\s*{", "", csv_str)
    csv_str = re.sub("}\s*$", "", csv_str)
    r = csv.reader([csv_str])
    row = list(r)[0]
    new = []
    for col in row:
        col = re.sub('^\s*"?\s*', "", col)
        col = re.sub('\s*"?\s*$', "", col)
        new.append(col)

    return new


def process_citation(citation_str: str) -> dict:
    """Parse BEL Script Citation string into nanopub_bel citation object"""

    citation_obj = {}

    citation_list = convert_csv_str_to_list(citation_str)
    (citation_type, name, doc_id, pub_date, authors, comment, *extra) = citation_list + [None] * 7
    # print(f'citation_type: {citation_type}, name: {name}, doc_id: {doc_id}, pub_date: {pub_date}, authors: {authors}, comment: {comment}')

    authors_list = []
    if authors:
        authors_list = authors.split("|")
        citation_obj["authors"] = authors_list

    if name and re.match("http?://", name):
        citation_obj["uri"] = name

    elif citation_type and citation_type.upper() == "PUBMED":
        citation_obj["database"] = {"name": "PubMed", "id": doc_id}
        if name:
            citation_obj["reference"] = name
    elif name:
        citation_obj["reference"] = name

    else:
        citation_obj["reference"] = "No reference found"

    if pub_date:
        citation_obj["date_published"] = pub_date

    if comment:
        citation_obj["comment"] = comment

    return citation_obj


def yield_metadata(nanopubs_metadata):
    """Yield nanopub metadata collected from BEL Script"""

    return {"metadata": copy.deepcopy(nanopubs_metadata)}


def split_bel_stmt(stmt: str, line_num) -> tuple:
    """Split bel statement into subject, relation, object tuple"""

    m = re.match(f"^(.*?\))\s+([a-zA-Z=\->\|:]+)\s+([\w(]+.*?)$", stmt, flags=0)
    if m:
        return (m.group(1), m.group(2), m.group(3))
    else:
        logger.info(
            f"Could not parse bel statement into components at line number: {line_num} assertion: {stmt}"
        )
        return (stmt, None, None)


def yield_nanopub(assertions, annotations, line_num):
    """Yield nanopub object"""

    if not assertions:
        return {}

    anno = copy.deepcopy(annotations)

    evidence = anno.pop("evidence", None)
    stmt_group = anno.pop("statement_group", None)
    citation = anno.pop("citation", None)

    anno_list = []
    for anno_type in anno:
        if isinstance(anno[anno_type], (list, tuple)):
            for val in anno[anno_type]:
                anno_list.append({"type": anno_type, "label": val})
        else:
            anno_list.append({"type": anno_type, "label": anno[anno_type]})

    assertions_list = []
    for assertion in assertions:
        (subj, rel, obj) = split_bel_stmt(assertion, line_num)
        assertions_list.append({"subject": subj, "relation": rel, "object": obj})

    nanopub = {
        "schema_uri": "https://raw.githubusercontent.com/belbio/schemas/master/schemas/nanopub_bel-1.0.0.yaml",
        "type": copy.deepcopy(nanopub_type),
        "annotations": copy.deepcopy(anno_list),
        "citation": copy.deepcopy(citation),
        "assertions": copy.deepcopy(assertions_list),
        "evidence": evidence,
        "metadata": {"statement_group": stmt_group},
    }

    return {"nanopub": copy.deepcopy(nanopub)}


def process_documentline(line, nanopubs_metadata):
    """Process SET DOCUMENT line in BEL script"""

    matches = re.match('SET DOCUMENT\s+(\w+)\s+=\s+"?(.*?)"?$', line)
    key = matches.group(1)
    val = matches.group(2)
    nanopubs_metadata[key] = val

    return nanopubs_metadata


def process_definition(line, nanopubs_metadata):
    """Process DEFINE line in BEL script"""

    matches = re.match('DEFINE\s+(\w+)\s+(\w+)\s+AS\s+URL\s+"(.*?)"\s*$', line)
    if matches:
        def_type = matches.group(1).lower()
        if def_type == "namespace":
            def_type = "namespaces"
        elif def_type == "annotation":
            def_type == "annotations"

        key = matches.group(2)
        val = matches.group(3)

        if def_type in nanopubs_metadata:
            nanopubs_metadata[def_type][key] = val
        else:
            nanopubs_metadata[def_type] = {key: val}

    matches = re.match("DEFINE\s+(\w+)\s+(\w+)\s+AS\s+LIST\s+{(.*?)}\s*$", line)
    if matches:
        def_type = matches.group(1).lower()
        if def_type == "namespace":
            def_type = "namespaces"
        elif def_type == "annotation":
            def_type == "annotations"

        key = matches.group(2)
        val = matches.group(3)
        vals = convert_csv_str_to_list(val)

        if def_type in nanopubs_metadata:
            nanopubs_metadata[def_type][key] = vals
        else:
            nanopubs_metadata[def_type] = {key: vals}

    return nanopubs_metadata


def process_unset(line, annotations):
    """Process UNSET lines in BEL Script"""

    matches = re.match('UNSET\s+"?(.*?)"?\s*$', line)
    if matches:
        val = matches.group(1)
        if val == "ALL" or val == "STATEMENT_GROUP":
            annotations = {}
        elif re.match("{", val):
            vals = convert_csv_str_to_list(val)
            for val in vals:
                annotations.pop(val, None)
        else:
            annotations.pop(val, None)

    else:
        logger.warn(f"Problem with UNSET line: {line}")

    return annotations


def process_set(line, annotations):
    """Convert annotations into nanopub_bel annotations format"""

    matches = re.match('SET\s+(\w+)\s*=\s*"?(.*?)"?\s*$', line)

    key = None
    if matches:
        key = matches.group(1)
        val = matches.group(2)

    if key == "STATEMENT_GROUP":
        annotations["statement_group"] = val
    elif key == "Citation":
        annotations["citation"] = process_citation(val)
    elif key.lower() == "support" or key.lower() == "evidence":
        annotations["evidence"] = val
    elif re.match("\s*{.*?}", val):
        vals = convert_csv_str_to_list(val)
        annotations[key] = vals
    else:
        annotations[key] = val

    return annotations


def set_single_line(lines):

    flag = False
    hold = ""

    for line in lines:
        if flag and re.match('.*"', line):
            line = hold + " " + line
            flag = False
            line = re.sub("\s+", " ", line)
            yield line
        elif flag:
            hold += " " + line.rstrip()

        elif re.match('SET\s*\w+\s*=\s*".*"', line):
            line = re.sub("\s+", " ", line)
            yield line
        elif re.match('SET\s*\w+\s*=\s*".*', line):
            hold = line.rstrip()
            flag = True
        else:
            line = re.sub("\s+", " ", line)
            yield line


def preprocess_belscript(lines):
    """ Convert any multi-line SET statements into single line SET statements"""

    set_flag = False
    for line in lines:
        if set_flag is False and re.match("SET", line):
            set_flag = True
            set_line = [line.rstrip()]
        # SET following SET
        elif set_flag and re.match("SET", line):
            yield f"{' '.join(set_line)}\n"
            set_line = [line.rstrip()]
        # Blank line following SET yields single line SET
        elif set_flag and re.match("\s+$", line):
            yield f"{' '.join(set_line)}\n"
            yield line
            set_flag = False

        # Append second, third, ... lines to SET
        elif set_flag:
            set_line.append(line.rstrip())
        else:
            yield line


def parse_belscript(lines):
    """Lines from the BELScript - can be an iterator or list

    yields Nanopubs in nanopubs_bel-1.0.0 format
    """

    nanopubs_metadata = {}
    annotations = {}
    assertions = []

    # # Turn a list into an iterator
    # if not isinstance(lines, collections.Iterator):
    #     lines = iter(lines)

    line_num = 0

    # for line in preprocess_belscript(lines):
    for line in set_single_line(lines):

        line_num += 1
        # Get rid of trailing comments
        line = re.sub("\/\/.*?$", "", line)

        line = line.rstrip()

        # Collapse continuation lines
        while re.search("\\\s*$", line):
            line = line.replace("\\", "") + next(lines)

        # Process lines #################################
        if re.match("\s*#", line) or re.match("\s*$", line):
            # Skip comments and empty lines
            continue
        elif re.match("SET DOCUMENT", line):
            nanopubs_metadata = process_documentline(line, nanopubs_metadata)
        elif re.match("DEFINE", line):
            nanopubs_metadata = process_definition(line, nanopubs_metadata)
        elif re.match("UNSET", line):

            # Process any assertions prior to changing annotations
            if assertions:
                yield yield_nanopub(assertions, annotations, line_num)
                assertions = []
            annotations = process_unset(line, annotations)

        elif re.match("SET", line):
            # Create nanopubs metadata prior to starting BEL Script statements section
            if nanopubs_metadata:
                yield yield_metadata(nanopubs_metadata)
                nanopubs_metadata = {}

            # Process any assertions prior to changing annotations
            if assertions:
                yield yield_nanopub(assertions, annotations, line_num)
                assertions = []

            annotations = process_set(line, annotations)

        else:
            assertions.append(line)

    # Catch any leftover bel statements
    yield_nanopub(assertions, annotations, line_num)


def main():

    with open("test.v2.bel", "r") as f:
        for doc in parse_belscript(f):
            print(json.dumps(doc, indent=4))

    quit()

    bel = 'proteinAbundance(HGNC:VHL) increases (proteinAbundance(HGNC:TNF) increases biologicalProcess(GOBP:"cell death"))'
    print(split_bel_stmt(bel))
    quit()

    citation_str = 'SET Citation = {"PubMed","Proc Natl Acad Sci U S A 1999 Feb 16 96(4) 1603-8","9990071","","",""}'
    print(process_citation(citation_str))
    quit()


if __name__ == "__main__":
    main()
