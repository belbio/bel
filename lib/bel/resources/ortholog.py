# Standard Library
import gzip
import json
from typing import IO

# Third Party Imports
from arango import ArangoError
from loguru import logger

# Local Imports
import bel.core.settings as settings
import bel.core.utils
import bel.db.arangodb as arangodb
from bel.db.arangodb import (
    resources_db,
    ortholog_edges_name,
    ortholog_nodes_name,
    resources_metadata_coll,
)

()


def load_orthologs(fo: IO, metadata: dict):
    """Load orthologs into ArangoDB

    Args:
        fo: file obj - orthologs file
        metadata: dict containing the metadata for orthologs
    """

    version = metadata["version"]
    source = metadata["name"]

    # LOAD ORTHOLOGS INTO ArangoDB

    arango_client = arangodb.get_client()
    if not arango_client:
        print("Cannot load orthologs without ArangoDB access")
        quit()

    arangodb.batch_load_docs(resources_db, orthologs_iterator(fo, version), on_duplicate="update")

    logger.info(
        "Load orthologs", source=source,
    )

    # Clean up old entries
    remove_old_ortholog_edges = f"""
        FOR edge in {ortholog_edges_name}
            FILTER edge.source == "{source}"
            FILTER edge.version != "{version}"
            REMOVE edge IN {ortholog_edges_name}
    """
    remove_old_ortholog_nodes = f"""
        FOR node in {ortholog_nodes_name}
            FILTER node.source == "{source}"
            FILTER node.version != "{version}"
            REMOVE node IN {ortholog_nodes_name}
    """
    arangodb.aql_query(resources_db, remove_old_ortholog_edges)
    arangodb.aql_query(resources_db, remove_old_ortholog_nodes)

    # Add metadata to resource metadata collection
    metadata["_key"] = arangodb.arango_id_to_key(source)
    resources_metadata_coll.insert(metadata, overwrite=True)


def orthologs_iterator(fo, version):
    """Ortholog node and edge iterator"""

    species_list = settings.BEL_FILTER_SPECIES

    fo.seek(0)

    for line in fo:
        edge = json.loads(line)
        if "metadata" in edge:
            source = edge["metadata"]["name"]
            continue

        if "ortholog" in edge:
            edge = edge["ortholog"]

            subject_key = edge["subject_key"]
            subject_species_key = edge["subject_species_key"]
            object_key = edge["object_key"]
            object_species_key = edge["object_species_key"]

            # Skip if any values are missing
            if any(
                [
                    not val
                    for val in [subject_key, subject_species_key, object_key, object_species_key]
                ]
            ):
                continue

            # Skip if species_key not listed in species_list
            if species_list and (
                subject_species_key not in species_list or object_species_key not in species_list
            ):
                continue

            # Simple lexical sorting (e.g. not numerical) to ensure 1 entry per pair
            if subject_key > object_key:
                subject_key, subject_species_key, object_key, object_species_key = (
                    object_key,
                    object_species_key,
                    subject_key,
                    subject_species_key,
                )

            # Convert to ArangoDB legal chars for arangodb _key
            subject_db_key = arangodb.arango_id_to_key(subject_key)
            object_db_key = arangodb.arango_id_to_key(object_key)

            # Subject node
            yield (
                ortholog_nodes_name,
                {
                    "_key": subject_db_key,
                    "key": subject_key,
                    "species_key": subject_species_key,
                    "source": source,
                    "version": version,
                },
            )
            # Object node
            yield (
                ortholog_nodes_name,
                {
                    "_key": object_db_key,
                    "key": object_key,
                    "species_key": object_species_key,
                    "source": source,
                    "version": version,
                },
            )

            arango_edge = {
                "_from": f"{ortholog_nodes_name}/{subject_db_key}",
                "_to": f"{ortholog_nodes_name}/{object_db_key}",
                "_key": bel.core.utils._create_hash(f"{subject_key}>>{object_key}"),
                "type": "ortholog_to",
                "source": source,
                "version": version,
            }

            yield (arangodb.ortholog_edges_name, arango_edge)
