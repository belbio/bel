#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Usage:  program.py <customer>

"""

# Standard Library
import copy
import datetime
import itertools
import json
import os.path
import urllib

# Third Party Imports
import httpx
import structlog

# Local Imports
import bel.db.arangodb as arangodb
import bel.edge.edges
import bel.nanopub.files as files
import bel.utils as utils

log = structlog.getLogger(__name__)


client = arangodb.get_client()
edgestore_db = arangodb.get_edgestore_handle(client)

edges_coll_name = arangodb.edgestore_edges_name
nodes_coll_name = arangodb.edgestore_nodes_name


def get_edges_for_nanopub(nanopub_id):
    query = f"""
        FOR edge IN edges
            FILTER edge.nanopub_id == "{nanopub_id}"
            LIMIT 1
            RETURN edge
    """
    try:
        result = [edge for edge in edgestore_db.aql.execute(query)]
        return result[0]
    except Exception:
        return None


def process_nanopub(
    nanopub_url, orthologize_targets: list = [], overwrite: bool = False, token: str = None
):

    log.debug(
        "Process nanopub parameters",
        nanopub_url=nanopub_url,
        orthologize_targets=orthologize_targets,
        overwrite=overwrite,
    )
    log.info("Processing nanopub", nanopub_url=nanopub_url)

    url_comps = urllib.parse.urlparse(nanopub_url)
    nanopub_id = os.path.basename(url_comps.path)
    # domain = url_comps.netloc

    start_time = datetime.datetime.now()

    # collect nanopub
    headers = {}
    if token:
        headers = {"Authorization": f"Bearer {token}"}

    r = httpx.get(nanopub_url, headers=headers)

    nanopub = r.json()

    end_time1 = datetime.datetime.now()
    delta_ms = f"{(end_time1 - start_time).total_seconds() * 1000:.1f}"
    log.debug("Timing - Get nanopub", delta_ms=delta_ms, nanopub=nanopub)

    assertions = []
    for assertion in nanopub["nanopub"].get("assertions", []):
        assertions.append(f"{assertion['subject']} {assertion['relation']} {assertion['object']}")

    if not nanopub:
        log.error(f"Could not GET nanopub: {nanopub_url}")

        return {
            "msg": f"Could not GET nanopub: {nanopub_url}",
            "edges_cnt": 0,
            "assertions_cnt": 0,
            "assertions": assertions,
            "success": False,
            "errors": [],
        }

    nanopub["source_url"] = nanopub_url

    # Is nanopub in edge newer than from queue? If so, skip
    if not overwrite:
        # collect one edge for nanopub from edgestore
        edge = get_edges_for_nanopub(nanopub_id)
        if edge:
            # check if edge nanopub is newer
            # log.info("Nanopub to Edge comparison", nanopub=nanopub, edge=edge)
            if edge["metadata"].get("gd_updateTS", None):
                if nanopub["nanopub"]["metadata"]["gd_updateTS"] <= edge["metadata"]["gd_updateTS"]:
                    log.info(
                        "Nanopub older than edge nanopub",
                        nanopub_dt=nanopub["nanopub"]["metadata"]["gd_updateTS"],
                        edge_dt=edge["metadata"]["gd_updateTS"],
                    )
                    return {"msg": "Nanopub older than edge nanopub", "success": True, "e": ""}

    end_time2 = datetime.datetime.now()
    delta_ms = f"{(end_time2 - end_time1).total_seconds() * 1000:.1f}"
    log.debug("Timing - Get edge to check nanopub", delta_ms=delta_ms)

    results = bel.edge.edges.nanopub_to_edges(nanopub, orthologize_targets=orthologize_targets)

    end_time3 = datetime.datetime.now()
    delta_ms = f"{(end_time3 - end_time2).total_seconds() * 1000:.1f}"

    if results["success"]:

        db_results = load_edges_into_db(nanopub_id, nanopub["source_url"], edges=results["edges"])

        # log.info("Convert nanopub to edges", db_results=db_results, results=results)

        end_time4 = datetime.datetime.now()
        delta_ms = f"{(end_time4 - end_time3).total_seconds() * 1000:.1f}"
        log.debug("Timing - Load edges into edgestore", delta_ms=delta_ms)

        delta_ms = f"{(end_time4 - start_time).total_seconds() * 1000:.1f}"
        log.debug("Timing - Process nanopub into edges", delta_ms=delta_ms)

        return {
            "msg": f"Loaded {len(results['edges'])} edges into edgestore",
            "edges_cnt": len(results["edges"]),
            "assertions_cnt": len(nanopub["nanopub"]["assertions"]),
            "assertions": assertions,
            "success": True,
            "errors": results["errors"],
        }

    else:
        log.error(f'Could not process nanopub {nanopub_id} into edges - error: {results["errors"]}')
        return {
            "msg": f'Could not process nanopub into edges - error: {results["errors"]}',
            "edges_cnt": 0,
            "assertions_cnt": len(nanopub["nanopub"]["assertions"]),
            "assertions": assertions,
            "success": False,
            "errors": results["errors"],
        }


def load_edges_into_db(
    nanopub_id: str,
    nanopub_url: str,
    edges: list = [],
    edges_coll_name: str = edges_coll_name,
    nodes_coll_name: str = nodes_coll_name,
):
    """Load edges into Edgestore"""

    start_time = datetime.datetime.now()

    # Clean out edges for nanopub in edgestore
    query = f"""
        FOR edge IN {edges_coll_name}
            FILTER edge.nanopub_id == "{nanopub_id}"
            REMOVE edge IN edges
    """

    try:
        edgestore_db.aql.execute(query)
    except Exception as e:
        log.debug(f"Could not remove nanopub-related edges: {query}  msg: {e}")

    end_time1 = datetime.datetime.now()
    delta_ms = f"{(end_time1 - start_time).total_seconds() * 1000:.1f}"
    log.debug("Timing - Delete edges for nanopub", delta_ms=delta_ms)

    # Collect edges and nodes to load into arangodb
    node_list, edge_list = [], []
    for doc in edge_iterator(edges=edges):
        if doc:  # Apparently needed to realize the doc variable
            if doc[0] == "nodes":
                node_list.append(doc[1])
            else:
                edge_list.append(doc[1])
        else:
            log.error("Cannot process edges from iterator - bad doc", doc=doc)

    end_time2 = datetime.datetime.now()
    delta_ms = f"{(end_time2 - end_time1).total_seconds() * 1000:.1f}"

    # log.info("Edge list to load into db", edge_list=edge_list)

    log.debug("Timing - Collect edges and nodes", delta_ms=delta_ms)

    try:
        results = edgestore_db.collection(edges_coll_name).import_bulk(
            edge_list, on_duplicate="replace", halt_on_error=False
        )

    except Exception as e:
        log.exception(f"Could not load edges  msg: {e}")

    end_time3 = datetime.datetime.now()
    delta_ms = f"{(end_time3 - end_time2).total_seconds() * 1000:.1f}"
    log.debug("Timing - Load edges into edgestore", delta_ms=delta_ms)

    try:
        results = edgestore_db.collection(nodes_coll_name).import_bulk(
            node_list, on_duplicate="replace", halt_on_error=False
        )
    except Exception as e:
        log.exception(f"Could not load nodes  msg: {e}")

    end_time4 = datetime.datetime.now()
    delta_ms = f"{(end_time4 - end_time3).total_seconds() * 1000:.1f}"
    log.debug("Timing - Load nodes into edgestore", delta_ms=delta_ms)


def edge_iterator(edges=[], edges_fn=None):
    """Yield documents from edge for loading into ArangoDB"""

    for edge in itertools.chain(edges, files.read_edges(edges_fn)):

        subj = copy.deepcopy(edge["edge"]["subject"])
        subj_id = str(utils._create_hash_from_doc(subj))
        subj["_key"] = subj_id
        obj = copy.deepcopy(edge["edge"]["object"])

        obj_id = str(utils._create_hash_from_doc(obj))
        obj["_key"] = obj_id
        relation = copy.deepcopy(edge["edge"]["relation"])

        relation["_from"] = f"nodes/{subj_id}"
        relation["_to"] = f"nodes/{obj_id}"

        # Create edge _key
        relation_hash = copy.deepcopy(relation)
        relation_hash.pop("edge_dt", None)
        relation_hash.pop("edge_hash", None)
        relation_hash.pop("nanopub_dt", None)
        relation_hash.pop("nanopub_url", None)
        relation_hash.pop("subject_canon", None)
        relation_hash.pop("object_canon", None)
        relation_hash.pop("public_flag", None)
        relation_hash.pop("metadata", None)

        relation_id = str(utils._create_hash_from_doc(relation_hash))
        relation["_key"] = relation_id

        if edge.get("nanopub_id", None):
            if "metadata" not in relation:
                relation["metadata"] = {}
            relation["metadata"]["nanopub_id"] = edge["nanopub_id"]

        yield ("nodes", subj)
        yield ("nodes", obj)
        yield ("edges", relation)


def main():
    pass


if __name__ == "__main__":
    main()
