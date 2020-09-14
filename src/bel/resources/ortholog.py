# Standard Library
import gzip
import json
from typing import IO, Mapping
import copy

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

from collections import defaultdict


def remove_old_db_entries(source, version: str = "", force: bool = False):
    """Remove older ortholog data entries"""

    if force or version == "":
        filter_version = ""
    else:
        filter_version = f'FILTER doc.version != "{version}"'

    # Clean up old entries
    remove_old_ortholog_edges = f"""
        FOR doc in {ortholog_edges_name}
            FILTER doc.source == "{source}"
            {filter_version}
            REMOVE doc IN {ortholog_edges_name}
    """
    remove_old_ortholog_nodes = f"""
        FOR doc in {ortholog_nodes_name}
            FILTER doc.source == "{source}"
            {filter_version}
            REMOVE doc IN {ortholog_nodes_name}
    """
    arangodb.aql_query(resources_db, remove_old_ortholog_edges)
    arangodb.aql_query(resources_db, remove_old_ortholog_nodes)


def load_orthologs(fo: IO, metadata: dict, force: bool = False):
    """Load orthologs into ArangoDB

    Args:
        fo: file obj - orthologs file
        metadata: dict containing the metadata for orthologs
    """

    result = {"success": True, "messages": []}

    statistics = {"entities_count": 0, "orthologous_pairs": defaultdict(lambda: defaultdict(int))}

    version = metadata["version"]
    source = metadata["name"]

    metadata_key = metadata["name"]
    prior_metadata = resources_metadata_coll.get(metadata_key)

    try:
        prior_version = prior_metadata.get("version", "")
        prior_entity_count = prior_metadata["statistics"].get("entities_count", 0)

    except Exception:
        prior_entity_count = 0
        prior_version = ""

    if prior_version == version or not force:
        msg = f"NOTE: This orthology dataset {source} at version {version} is already loaded and the 'force' option was not used"
        result["messages"].append(msg)
        return result

    arangodb.batch_load_docs(
        resources_db, orthologs_iterator(fo, version, statistics), on_duplicate="update"
    )

    logger.info(
        f"Loaded orthologs, source: {source}  count: {statistics['entities_count']}", source=source
    )

    if prior_entity_count > statistics["entities_count"]:
        logger.error(
            f"Error: This orthology dataset {source} at version {version} has fewer orthologs than previously loaded orthology dataset. Skipped removing old ortholog entries"
        )

        result["success"] = False
        msg = f"Error: This orthology dataset {source} at version {version} has fewer orthologs than previously loaded orthology dataset. Skipped removing old ortholog entries"
        result["messages"].append(msg)
        return result

    remove_old_db_entries(source, version=version)

    # Add metadata to resource metadata collection
    metadata["_key"] = arangodb.arango_id_to_key(source)

    # Using side effect to get statistics from orthologs_iterator on purpose
    metadata["statistics"] = copy.deepcopy(statistics)

    resources_metadata_coll.insert(metadata, overwrite=True)

    result["messages"].append(f'Loaded {statistics["entities_count"]} ortholog sets into arangodb')
    return result


def orthologs_iterator(fo, version, statistics: Mapping):
    """Ortholog node and edge iterator

    NOTE: the statistics dict works as a side effect since it is passed as a reference!!!
    """

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

            statistics["entities_count"] += 1
            statistics["orthologous_pairs"][subject_species_key][object_species_key] += 1
            statistics["orthologous_pairs"][object_species_key][subject_species_key] += 1

            yield (arangodb.ortholog_edges_name, arango_edge)


def delete_ortholog_resource(source):
    """Remove ortholog resource

    Remove Arangodb terms and equivalences and remove Elasticsearch terms index
    """

    remove_old_db_entries(source, force=True)
