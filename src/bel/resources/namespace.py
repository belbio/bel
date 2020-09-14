# Standard Library
import copy
import gzip
import json
import time
from collections import defaultdict
from typing import IO, Optional

# Third Party Imports
import cachetools
from arango import ArangoError
from loguru import logger

# Local Imports
import bel.core.mail
import bel.core.settings as settings
import bel.db.elasticsearch as elasticsearch
from bel.db.arangodb import (
    arango_id_to_key,
    batch_load_docs,
    equiv_edges_name,
    equiv_nodes_name,
    resources_db,
    resources_metadata_coll,
    terms_coll,
    terms_coll_name,
)
from bel.db.elasticsearch import es
from bel.schemas.terms import Namespace

# key = ns:id
# main_key = preferred key, e.g. ns:<primary_id> not the alt_key or obsolete key or even an equivalence key which could be an alt_key
# alt_key = for HGNC the preferred key is HGNC:391 for the alt_key HGNC:AKT1 - where AKT1 is a secondary ID
# db_key = key converted to arangodb format


def remove_old_db_entries(namespace: str, version: str = "", force: bool = False):
    """Remove old database entries

    Args:
        namespace: preferred namespace prefix, e.g. HGNC or DO
        version: version of last namespace loaded - used to remove older entries from arangodb
        force: remove ALL namespace database entries
    """

    if force or version == "":
        filter_version = ""
    else:
        filter_version = f"""FILTER doc.version != "{version}" """

    # Clean up old entries
    remove_old_terms = f"""
        FOR doc in {terms_coll_name}
            FILTER doc.namespace == "{namespace}"
            {filter_version}
            REMOVE doc IN {terms_coll_name}
    """

    remove_old_equivalence_edges = f"""
        FOR doc in {equiv_edges_name}
            FILTER doc.source == "{namespace}"
            {filter_version}
            REMOVE doc IN {equiv_edges_name}
    """

    remove_old_equivalence_nodes = f"""
        FOR doc in {equiv_nodes_name}
            FILTER doc.source == "{namespace}"
            {filter_version}
            REMOVE doc IN {equiv_nodes_name}
    """

    resources_db.aql.execute(remove_old_terms)
    resources_db.aql.execute(remove_old_equivalence_edges)
    resources_db.aql.execute(remove_old_equivalence_nodes)


def load_terms(f: IO, metadata: dict, force: bool = False):
    """Load terms into Elasticsearch and ArangoDB

    Force will create a new index in Elasticsearch regardless of whether
    an index with the resource version already exists.

    Args:
        fp: file path - terminology file
        metadata: dict containing the metadata for terminology
        force:  force full update - e.g. remove and re-add elasticsearch index
                and delete arangodb namespace records before loading
    """

    result = {"success": True, "messages": []}

    statistics = {
        "entities_count": 0,
        "synonyms_count": 0,
        "entity_types": defaultdict(int),
        "annotation_types": defaultdict(int),
        "equivalenced_namespaces": defaultdict(int),
    }

    metadata_key = f"Namespace_{metadata['namespace']}"
    prior_metadata = resources_metadata_coll.get(metadata_key)

    try:
        prior_version = prior_metadata.get("version", "")
        prior_entity_count = prior_metadata["statistics"].get("entities_count", 0)
    except Exception:
        prior_entity_count = 0
        prior_version = ""

    namespace = metadata["namespace"]
    version = metadata["version"]

    ################################################################################
    # Elasticsearch index processing
    ################################################################################
    es_version = version.replace("T", "").replace("-", "").replace(":", "")
    index_prefix = f"{settings.TERMS_INDEX}_{namespace.lower()}"
    index_name = f"{index_prefix}_{es_version}"

    # Create index with mapping
    if prior_version != version or force:
        elasticsearch.create_terms_index(index_name)
    else:
        result["success"] = True
        result["messages"].append(
            f'NOTE: This namespace {namespace} at version {version} is already loaded and the "force" option was not used'
        )

        return result

    terms_iterator = terms_iterator_for_elasticsearch(f, index_name, statistics)
    elasticsearch.bulk_load_docs(terms_iterator)

    # Using side effect to get statistics from terms_iterator_for_elasticsearch on purpose
    metadata["statistics"] = copy.deepcopy(statistics)

    # Remove old namespace index
    index_names = elasticsearch.get_all_index_names()
    for name in index_names:
        if name != index_name and index_prefix in name:
            elasticsearch.delete_index(name)

    if not force and prior_entity_count > metadata["statistics"]["entities_count"]:
        logger.error(
            f'Problem loading namespace: {namespace}, previous entity count: {prior_entity_count}, current load entity count: {metadata["statistics"]["entities_count"]}'
        )

        result["success"] = False
        result["messages"].append(
            f'ERROR: Problem loading namespace: {namespace}, previous entity count: {prior_entity_count}, current load entity count: {metadata["statistics"]["entities_count"]}'
        )

        return result

    # Add terms alias to this index
    elasticsearch.add_index_alias(index_name, settings.TERMS_INDEX)

    ################################################################################
    # Arangodb collection loading
    ################################################################################
    if force:
        remove_old_db_entries(namespace, version=version, force=True)

    # LOAD Terms and equivalences INTO ArangoDB
    # Uses update on duplicate to allow primary on equivalence_nodes to not be overwritten
    batch_load_docs(resources_db, terms_iterator_for_arangodb(f, version), on_duplicate="update")

    # Add metadata to resource metadata collection
    metadata["_key"] = metadata_key

    resources_metadata_coll.insert(metadata, overwrite=True)

    if not force:
        remove_old_db_entries(namespace, version=version)

    logger.info(
        f'Loaded Namespace: {namespace} with {metadata["statistics"]["entities_count"]} terms into elasticsearch: {settings.TERMS_INDEX}.{index_name} and arangodb collection: {terms_coll_name}',
        namespace=metadata["namespace"],
    )

    result["messages"].append(
        f'Loaded Namespace: {namespace} with {metadata["statistics"]["entities_count"]} terms into elasticsearch: {settings.TERMS_INDEX}.{index_name} and arangodb collection: {terms_coll_name}'
    )
    return result


def terms_iterator_for_arangodb(f: IO, version: str):
    """Generator for loading namespace terms into arangodb"""

    species_list = settings.BEL_FILTER_SPECIES

    f.seek(0)

    for line in f:
        term = json.loads(line)
        # skip if not term record (e.g. is a metadata record)
        if "term" not in term:
            continue
        term = term["term"]
        term_key = term["key"]
        namespace = term["namespace"]

        species_id = term.get("species_id", None)
        # Skip if species not listed in species_list
        if species_list and species_id and species_id not in species_list:
            continue

        # Can't use original key formatted for Arangodb as some keys are longer than allowed (_key < 255 chars)
        term_db_key = arango_id_to_key(term_key)

        term["_key"] = term_db_key
        term["version"] = version
        # Add term record to terms collection
        yield (terms_coll_name, term)

        # Add primary ID node
        yield (
            equiv_nodes_name,
            {
                "_key": term_db_key,
                "key": term["key"],  # BEL Key - ns:id
                "primary": True,
                "namespace": namespace,
                "source": namespace,
                "version": version,
            },
        )

        # Create Alt ID nodes/equivalences (to support other database equivalences using non-preferred Namespace IDs)
        if "alt_keys" in term:
            for alt_key in term["alt_keys"]:
                # logger.info(f'Added {alt_id} equivalence')
                alt_db_key = arango_id_to_key(alt_key)

                yield (
                    equiv_nodes_name,
                    {
                        "_key": alt_db_key,
                        "key": alt_key,
                        "namespace": alt_key.split(":")[0],
                        "source": namespace,
                        "version": version,
                    },
                )

                # Ensure only one edge per pair
                if term_db_key < alt_db_key:
                    from_ = term_db_key
                    to_ = alt_db_key
                else:
                    from_ = alt_db_key
                    to_ = term_db_key

                # Add edges for alt_keys
                arango_edge = {
                    "_from": f"{equiv_nodes_name}/{from_}",
                    "_to": f"{equiv_nodes_name}/{to_}",
                    "_key": arango_id_to_key(f"{from_}>>{to_}"),
                    "type": "equivalent_to",
                    "source": namespace,
                    "version": version,
                }
                yield (equiv_edges_name, arango_edge)

        # Cross-Namespace equivalences
        if "equivalence_keys" in term:
            for eqv_key in term["equivalence_keys"]:
                eqv_db_key = arango_id_to_key(eqv_key)

                equiv_node = (
                    equiv_nodes_name,
                    {
                        "_key": eqv_db_key,
                        "key": eqv_key,
                        "namespace": eqv_key.split(":")[0],
                        "source": namespace,
                        "version": version,
                    },
                )

                yield equiv_node

                # Ensure only one edge per pair
                if term_db_key < eqv_db_key:
                    from_ = term_db_key
                    to_ = eqv_db_key
                else:
                    from_ = eqv_db_key
                    to_ = term_db_key

                equiv_edge = (
                    equiv_edges_name,
                    {
                        "_from": f"{equiv_nodes_name}/{from_}",
                        "_to": f"{equiv_nodes_name}/{to_}",
                        "_key": arango_id_to_key(f"{from_}>>{to_}"),
                        "type": "equivalent_to",
                        "source": namespace,
                        "version": version,
                    },
                )

                yield equiv_edge


def terms_iterator_for_elasticsearch(f: IO, index_name: str, statistics: dict):
    """Add index_name to term documents for bulk load"""

    species_list = settings.BEL_FILTER_SPECIES

    f.seek(0)  # Seek back to beginning of file

    for line in f:
        term = json.loads(line)
        # skip if not term record (e.g. is a metadata record)
        if "term" not in term:
            continue
        term = term["term"]

        # Collect statistics
        statistics["entities_count"] += 1
        statistics["synonyms_count"] += len(term.get("synonyms", []))
        for entity_type in term.get("entity_types", []):
            statistics["entity_types"][entity_type] += 1
        for annotation_type in term.get("annotation_types", []):
            statistics["annotation_types"][annotation_type] += 1
        for equivalence in term.get("equivalence_keys", []):
            ns, id_ = equivalence.split(":", maxsplit=1)
            statistics["equivalenced_namespaces"][ns] += 1

        # Filter species if enabled in config
        species_key = term.get("species_key", "")
        if species_list and species_key and species_key not in species_list:
            continue

        all_term_keys = set()
        for term_key in [term["key"]] + term.get("alt_keys", []):
            all_term_keys.add(term_key)
            all_term_keys.add(lowercase_term_id(term_key))

        term["alt_keys"] = list(all_term_keys)

        term.pop("child_keys", "")
        term.pop("parent_keys", "")
        term.pop("equivalence_keys", "")

        record = {
            "_op_type": "index",
            "_index": index_name,
            "_type": "term",
            "_id": term["key"],
            "_source": copy.deepcopy(term),
        }

        yield record


def lowercase_term_id(term_key: str) -> str:
    """Lowercase the term value (not the namespace prefix)

    Args:
        term_id (str): term identifier with namespace prefix, e.g. MESH:Atherosclerosis

    Returns:
        str: lowercased, e.g. MESH:atherosclerosis
    """

    (ns, val) = term_key.split(":", maxsplit=1)
    term_key = f"{ns}:{val.lower()}"

    return term_key


@cachetools.cached(cachetools.TTLCache(maxsize=1, ttl=600))
def get_namespace_metadata():
    """Get namespace metadata"""

    namespaces = {}
    for namespace in resources_metadata_coll:
        if namespace.get("resource_type", None) != "namespace":
            continue

        namespace = Namespace(**namespace)
        namespaces[namespace.namespace] = namespace

    return namespaces


def delete_namespace(namespace):
    """Remove namespace resources

    Remove Arangodb terms and equivalences and remove Elasticsearch terms index
    """

    remove_old_db_entries(namespace, force=True)

    es.indices.delete(index=f"{settings.TERMS_INDEX}_{namespace.lower()}_*", ignore=[400, 404])
