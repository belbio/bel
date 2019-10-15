import gzip
import json
from typing import IO

import timy
from arango import ArangoError
from structlog import get_logger

import bel.db.arangodb as arangodb
import bel.utils
from bel.Config import config

log = get_logger()


def load_orthologs(fo: IO, metadata: dict):
    """Load orthologs into ArangoDB

    Args:
        fo: file obj - orthologs file
        metadata: dict containing the metadata for orthologs
    """

    version = metadata["metadata"]["version"]

    # LOAD ORTHOLOGS INTO ArangoDB
    with timy.Timer("Load Orthologs") as timer:

        arango_client = arangodb.get_client()
        if not arango_client:
            print("Cannot load orthologs without ArangoDB access")
            quit()
        belns_db = arangodb.get_belns_handle(arango_client)
        arangodb.batch_load_docs(belns_db, orthologs_iterator(fo, version), on_duplicate="update")

        log.info("Load orthologs", elapsed=timer.elapsed, source=metadata["metadata"]["source"])

        # Clean up old entries
        remove_old_ortholog_edges = f"""
            FOR edge in ortholog_edges
                FILTER edge.source == "{metadata["metadata"]["source"]}"
                FILTER edge.version != "{version}"
                REMOVE edge IN ortholog_edges
        """
        remove_old_ortholog_nodes = f"""
            FOR node in ortholog_nodes
                FILTER node.source == "{metadata["metadata"]["source"]}"
                FILTER node.version != "{version}"
                REMOVE node IN ortholog_nodes
        """
        arangodb.aql_query(belns_db, remove_old_ortholog_edges)
        arangodb.aql_query(belns_db, remove_old_ortholog_nodes)

    # Add metadata to resource metadata collection
    metadata["_key"] = f"Orthologs_{metadata['metadata']['source']}"
    try:
        belns_db.collection(arangodb.belns_metadata_name).insert(metadata)
    except ArangoError as ae:
        belns_db.collection(arangodb.belns_metadata_name).replace(metadata)


def orthologs_iterator(fo, version):
    """Ortholog node and edge iterator"""

    species_list = config["bel_resources"].get("species_list", [])

    fo.seek(0)
    with gzip.open(fo, "rt") as f:
        for line in f:
            edge = json.loads(line)
            if "metadata" in edge:
                source = edge["metadata"]["source"]
                continue

            if "ortholog" in edge:
                edge = edge["ortholog"]
                subj_tax_id = edge["subject"]["tax_id"]
                obj_tax_id = edge["object"]["tax_id"]

                # Skip if species not listed in species_list
                if species_list and subj_tax_id and subj_tax_id not in species_list:
                    continue
                if species_list and obj_tax_id and obj_tax_id not in species_list:
                    continue

                # Converted to ArangoDB legal chars for _key
                subj_key = arangodb.arango_id_to_key(edge["subject"]["id"])
                subj_id = edge["subject"]["id"]

                # Converted to ArangoDB legal chars for _key
                obj_key = arangodb.arango_id_to_key(edge["object"]["id"])
                obj_id = edge["object"]["id"]

                # Subject node
                yield (
                    arangodb.ortholog_nodes_name,
                    {
                        "_key": subj_key,
                        "name": subj_id,
                        "tax_id": edge["subject"]["tax_id"],
                        "source": source,
                        "version": version,
                    },
                )
                # Object node
                yield (
                    arangodb.ortholog_nodes_name,
                    {
                        "_key": obj_key,
                        "name": obj_id,
                        "tax_id": edge["object"]["tax_id"],
                        "source": source,
                        "version": version,
                    },
                )

                arango_edge = {
                    "_from": f"{arangodb.ortholog_nodes_name}/{subj_key}",
                    "_to": f"{arangodb.ortholog_nodes_name}/{obj_key}",
                    "_key": bel.utils._create_hash(f"{subj_id}>>{obj_id}"),
                    "type": "ortholog_to",
                    "source": source,
                    "version": version,
                }

                yield (arangodb.ortholog_edges_name, arango_edge)
