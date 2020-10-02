# Standard Library
import re
import time
from typing import Any, List, Mapping, Optional, Union

# Third Party
import cachetools

# Third Party Imports
import elasticsearch
from loguru import logger

# Local
# Local Imports
import bel.core.settings as settings
from bel.core.utils import asyncify, split_key_label
from bel.db.arangodb import arango_id_to_key, resources_db, terms_coll_name
from bel.db.elasticsearch import es
from bel.resources.namespace import get_namespace_metadata
from bel.schemas.terms import Term

Key = str  # namespace:id


@cachetools.cached(cachetools.TTLCache(maxsize=512, ttl=600))
def get_terms(term_key: Key) -> List[Term]:
    """Get term(s) using term_key - given term_key may match multiple term records

    Term Key can match the main key, alt_keys or obsolete_keys
    """

    namespaces_metadata = get_namespace_metadata()

    (namespace, id, label) = split_key_label(term_key)

    # Virtual namespace term
    if (
        namespace in namespaces_metadata
        and namespaces_metadata[namespace].namespace_type != "complete"
    ):
        metadata = namespaces_metadata[namespace]
        return [
            Term(
                key=term_key,
                namespace=namespace,
                id=id,
                entity_types=metadata.entity_types,
                annotation_types=metadata.annotation_types,
                species_key=metadata.species_key,
            )
        ]

    term_key = term_key.replace("'", "\\'")
    query = f"""
        FOR term in {terms_coll_name}
            FILTER term.key == '{term_key}'  OR '{term_key}' in term.alt_keys OR '{term_key}' in term.obsolete_keys
            RETURN term
    """

    # logger.debug("Get terms query", query=query)

    results = list(resources_db.aql.execute(query))

    results = [Term(**term) for term in results]

    return results


def get_term(term_key: Key) -> Optional[Term]:
    """Expect one term to match term_key

    Term Key can match the main key, alt_keys or obsolete_keys
    """

    # time1 = time.perf_counter()
    terms = get_terms(term_key)
    # time2 = time.perf_counter()

    # duration = f"{time2 - time1:.5f}"
    # logger.debug(f"Get terms timing {duration} for {term_key}", term_key=term_key, duration=duration)

    # Filter out any terms resulting from obsolete ids if more than 1 term
    if len(terms) > 1:
        check_terms = [term for term in terms if term_key not in term.obsolete_keys]
        if len(check_terms) > 0:
            terms = check_terms

    if len(terms) == 1:
        return terms[0]

    elif len(terms) > 1:
        logger.warning(
            f"Too many primary Keys returned. Given term_key: {term_key} matches these terms: {[term.key for term in terms]}"
        )
        return terms[0]

    else:
        return None


def get_equivalents(term_key: str) -> Mapping[str, List[Mapping[str, Any]]]:
    """Get equivalents given term key

    Args:
        term_key: namespace:id - may be a primary, alt_key, or obsolete_key

    Returns:
        Mapping[str, List[Mapping[str, Any]]]: e.g. {"equivalents": [{'term_key': 'HGNC:5', 'namespace': 'HGNC', 'primary': False}]}
    """

    try:

        term = get_term(term_key)

        term_dbkey = arango_id_to_key(term.key)

        # logger.debug("Term", term=term, term_dbkey=term_dbkey)

        query = f"""
        FOR vertex, edge IN 1..5
            ANY 'equivalence_nodes/{term_dbkey}' equivalence_edges
            OPTIONS {{bfs: true, uniqueVertices : 'global'}}
            RETURN DISTINCT {{
                term_key: vertex.key,
                namespace: vertex.namespace,
                primary: vertex.primary
            }}
        """

        docs = list(resources_db.aql.execute(query))

        logger.debug("Get equivalents query", query=query, equivalents=docs)

        return {"equivalents": docs}

    except Exception as e:

        logger.exception(f"Problem getting term equivalents for {term_key} msg: {e}")
        return {"equivalents": [], "errors": [f"Unexpected error {e}"]}


@cachetools.cached(cachetools.TTLCache(maxsize=1024, ttl=600))
def get_cached_equivalents(term_key: Key) -> Mapping[str, List[Mapping[str, Any]]]:

    return get_equivalents(term_key)


def get_normalized_terms(
    term_key: Key,
    canonical_targets: Mapping[str, List[str]] = settings.BEL_CANONICALIZE,
    decanonical_targets: Mapping[str, List[str]] = settings.BEL_DECANONICALIZE,
    term: Optional[Term] = None,
) -> Mapping[str, str]:
    """Get canonical and decanonical form for term

    This is effectively cached as the get_term and get_cached_equivalents calls
    are cached.

    Inputs:
        term_key: <Namespace>:<ID>

    Returns: {"canonical": <>, "decanonical": <>, "original": <>}
    """

    # TODO - make sure that the results are consistent for terms like:
    #     HGNC:IFNA1 and HGNC:IFNA13 - get collapsed together due to their SP entry - https://www.uniprot.org/uniprot/P01562
    #     HGNC:DEFB4A and HGNC:DEFB4B - get collapsed together due to their SP entry - https://www.uniprot.org/uniprot/O15263
    #
    #     1. Sort each namespace and take first term_key
    #

    # Normalized term is the official term - e.g. HGNC:207 (normalized) vs HGNC:AKT1 (original but not normalized)
    normalized_term_key = term_key
    if not term:
        term = get_term(term_key)
        if term:
            normalized_term_key = term.key
    else:
        normalized_term_key = term.key

    label, entity_types, annotation_types = "", [], []
    if term:
        label = term.label
        entity_types = term.entity_types
        annotation_types = term.annotation_types

    if normalized_term_key:
        normalized = {
            "normalized": normalized_term_key,
            "original": term_key,
            "canonical": normalized_term_key,
            "decanonical": normalized_term_key,
            "label": label,
            "entity_types": entity_types,
            "annotation_types": annotation_types,
        }
    else:
        normalized = {
            "normalized": term_key,
            "original": term_key,
            "canonical": term_key,
            "decanonical": term_key,
            "label": label,
            "entity_types": entity_types,
            "annotation_types": annotation_types,
        }

    ns = term_key.split(":")[0]
    if not ns:
        logger.error(f"Term key is missing namespace {term_key}")
        return normalized

    if ns in canonical_targets or ns in decanonical_targets:
        equivalents = get_cached_equivalents(term_key)

    for target_ns in canonical_targets.get(ns, []):
        for equivalent in equivalents["equivalents"]:
            if equivalent["primary"] and target_ns == equivalent["namespace"]:
                normalized["canonical"] = equivalent["term_key"]
                break
        else:  # If break in inner loop, break outer loop
            continue
        break

    for target_ns in decanonical_targets.get(ns, []):
        for equivalent in equivalents["equivalents"]:
            if equivalent["primary"] and target_ns == equivalent["namespace"]:
                normalized["decanonical"] = equivalent["term_key"]
                break
        else:  # If break in inner loop, break outer loop
            continue
        break

    return normalized


@asyncify
def async_get_normalized_terms(
    term_key: Key,
    canonical_targets: Mapping[str, List[str]] = settings.BEL_CANONICALIZE,
    decanonical_targets: Mapping[str, List[str]] = settings.BEL_DECANONICALIZE,
    term: Optional[Term] = None,
) -> Mapping[str, str]:

    return get_normalized_terms(term_key, canonical_targets, decanonical_targets, term)


def get_term_completions(
    completion_text: str,
    size: int = 10,
    entity_types: List[str] = None,
    annotation_types: List[str] = None,
    species_keys: List[Key] = None,
    namespaces: List[str] = None,
):
    """Get Term completions filtered by additional requirements

    Args:
        completion_text: text to complete to location NSArgs
        size: how many terms to return
        entity_types: list of entity_types used to filter completion results
        annotation_types: list of annotation types used to filter completion results
        species: list of species (TAX:nnnn) used to filter completions
        namespaces: list of namespaces to filter completions

    Returns:
        list of NSArgs
    """

    if entity_types is None or entity_types == [None]:
        entity_types = []
    if annotation_types is None or annotation_types == [None]:
        annotation_types = []
    if species_keys is None or species_keys == [None]:
        species_keys = []
    if namespaces is None or namespaces == [None]:
        namespaces = []

    # Split out Namespace from namespace value to use namespace for filter
    #     and value for completion text
    matches = re.match('([A-Z]+):"?(.*)', completion_text)
    if matches:
        namespaces = [matches.group(1)]
        completion_text = matches.group(2)

    filters = []

    # Entity filters
    if entity_types and isinstance(entity_types, str):
        entity_types = [entity_types]
        filters.append({"terms": {"entity_types": entity_types}})
    elif entity_types:
        filters.append({"terms": {"entity_types": entity_types}})

    # If the entity_type is Species - don't filter to the provided species
    if "Species" in entity_types:
        species_keys = []

    # Annotation type filters
    if annotation_types and isinstance(annotation_types, str):
        filters.append({"terms": {"annotation_types": [annotation_types]}})
    elif annotation_types:
        filters.append({"terms": {"annotation_types": annotation_types}})

    # Namespace filter
    if namespaces and isinstance(namespaces, str):
        filters.append({"terms": {"namespace": [namespaces]}})
    elif namespaces:
        filters.append({"terms": {"namespace": namespaces}})

    # Species filter
    grp = False
    if entity_types:
        grp = [et for et in entity_types if et in settings.species_entity_types]

    if grp and species_keys:
        if isinstance(species_keys, str):
            species_keys = [species_keys]

        # Allow non-species specific terms to be found
        filters.append(
            {
                "bool": {
                    "should": [
                        {"bool": {"must_not": {"exists": {"field": "species_key"}}}},
                        {"terms": {"species_key": species_keys}},
                    ]
                }
            }
        )

    # logger.debug(f"Term Filters {filters}")

    search_body = {
        "_source": [
            "key",
            "namespace",
            "id",
            "label",
            "name",
            "description",
            "species_key",
            "species_label",
            "entity_types",
            "annotation_types",
            "synonyms",
        ],
        "size": size,
        "query": {
            "bool": {
                "should": [
                    {"match": {"key": {"query": completion_text, "boost": 6, "_name": "key"}}},
                    {
                        "match": {
                            "namespace_value": {
                                "query": completion_text,
                                "boost": 8,
                                "_name": "namespace_value",
                            }
                        }
                    },
                    {"match": {"label": {"query": completion_text, "boost": 5, "_name": "label"}}},
                    {
                        "match": {
                            "synonyms": {"query": completion_text, "boost": 1, "_name": "synonyms"}
                        }
                    },
                ],
                "must": {
                    "match": {"autocomplete": {"query": completion_text, "_name": "autocomplete"}}
                },
                "filter": filters,
            }
        },
        "highlight": {"fields": {"autocomplete": {"type": "plain"}, "synonyms": {"type": "plain"}}},
    }

    # Boost namespaces
    if settings.BEL_BOOST_NAMESPACES:
        boost_namespaces = {"terms": {"namespace": settings.BEL_BOOST_NAMESPACES, "boost": 6}}
        search_body["query"]["bool"]["should"].append(boost_namespaces)

    results = es.search(
        index=settings.TERMS_INDEX, doc_type=settings.TERMS_DOCUMENT_TYPE, body=search_body
    )

    # highlight matches
    completions = []

    for result in results["hits"]["hits"]:
        species_key = result["_source"].get("species_key", None)
        species_label = result["_source"].get("species_label", None)
        species = {"key": species_key, "label": species_label}
        entity_types = result["_source"].get("entity_types", None)
        annotation_types = result["_source"].get("annotation_types", None)
        # Filter out duplicate matches
        matches = []
        matches_lower = []
        for match in result["highlight"]["autocomplete"]:
            if match.lower() in matches_lower:
                continue
            matches.append(match)
            matches_lower.append(match.lower())

        # Sorting parameters
        if matches[0].startswith("<em>"):
            startswith_sort = 0
        else:
            startswith_sort = 1
        sort_len = len(matches[0])

        completions.append(
            {
                "key": result["_source"]["key"],
                "name": result["_source"].get("name", "Missing Name"),
                "namespace": result["_source"].get("namespace", "Missing Namespace"),
                "id": result["_source"].get("id", "Missing ID"),
                "label": result["_source"].get("label", ""),
                "description": result["_source"].get("description", None),
                "species": species,
                "entity_types": entity_types,
                "annotation_types": annotation_types,
                "highlight": matches,
                "sort_tuple": (startswith_sort, sort_len),
            }
        )

    return completions


##################################################################################################
# Stats ##########################################################################################
##################################################################################################
def namespace_term_counts():
    """Generate counts of each namespace in terms index

    This function is at least used in the /status endpoint to show how many
    terms are in each namespace and what namespaces are available.

    Returns:
        List[Mapping[str, int]]: array of namespace vs counts
    """

    size = 100

    search_body = {
        "aggs": {"namespace_term_counts": {"terms": {"field": "namespace", "size": size}}}
    }

    # Get term counts but raise error if elasticsearch is not available
    try:
        results = es.search(
            index=settings.TERMS_INDEX,
            doc_type=settings.TERMS_DOCUMENT_TYPE,
            body=search_body,
            size=0,
        )
        results = results["aggregations"]["namespace_term_counts"]["buckets"]
        return [{"namespace": r["key"], "count": r["doc_count"]} for r in results]
    except elasticsearch.ConnectionError as e:
        logger.exception("Elasticsearch connection error", error=str(e))
        return None


def term_types():
    """Collect Term Types and their counts

    Return aggregations of namespaces, entity types, and context types
    up to a 100 of each type (see size=<number> in query below)

    Returns:
        Mapping[str, Mapping[str, int]]: dict of dicts for term types
    """

    size = 100

    search_body = {
        "aggs": {
            "namespace_term_counts": {"terms": {"field": "namespace", "size": size}},
            "entity_type_counts": {"terms": {"field": "entity_types", "size": size}},
            "annotation_type_counts": {"terms": {"field": "annotation_types", "size": size}},
        }
    }

    results = es.search(
        index=settings.TERMS_INDEX, doc_type=settings.TERMS_DOCUMENT_TYPE, body=search_body, size=0
    )

    types = {"namespaces": {}, "entity_types": {}, "annotation_types": {}}

    aggs = {
        "namespace_term_counts": "namespaces",
        "entity_type_counts": "entity_types",
        "annotation_type_counts": "annotation_types",
    }
    for agg in aggs:
        for bucket in results["aggregations"][agg]["buckets"]:
            types[aggs[agg]][bucket["key"]] = bucket["doc_count"]

    return types


##################################################################################################
# Undeployed/Unfinished
##################################################################################################
# TODO - not deployed/fully implemented - to be used for /terms POST endpoint
def get_term_search(search_term, size, entity_types, annotation_types, species, namespaces):
    """Search for terms given search term"""

    if not size:
        size = 10

    filters = []
    if entity_types:
        filters.append({"terms": {"entity_types": entity_types}})
    if annotation_types:
        filters.append({"terms": {"annotation_types": annotation_types}})
    if species:
        filters.append({"terms": {"species": species}})
    if namespaces:
        filters.append({"terms": {"namespaces": namespaces}})

    search_body = {
        "size": size,
        "query": {
            "bool": {
                "minimum_should_match": 1,
                "should": [
                    {"match": {"id": {"query": "", "boost": 4}}},
                    {"match": {"namespace_value": {"query": "", "boost": 4}}},
                    {"match": {"name": {"query": "", "boost": 2}}},
                    {"match": {"synonyms": {"query": ""}}},
                    {"match": {"label": {"query": "", "boost": 4}}},
                    {"match": {"alt_keys": {"query": "", "boost": 2}}},
                    {"match": {"src_id": {"query": ""}}},
                ],
                "filter": filters,
            }
        },
        "highlight": {
            "fields": [
                {"id": {}},
                {"name": {}},
                {"label": {}},
                {"synonyms": {}},
                {"alt_keys": {}},
                {"src_id": {}},
            ]
        },
    }

    results = es.search(
        index=settings.TERMS_INDEX, doc_type=settings.TERMS_DOCUMENT_TYPE, body=search_body
    )

    search_results = []
    for result in results["hits"]["hits"]:
        search_results.append(result["_source"] + {"highlight": result["highlight"]})

    return search_results


def get_species_info(species_id):

    logger.debug(species_id)

    url_template = "https://www.ncbi.nlm.nih.gov/Taxonomy/Browser/wwwtax.cgi?mode=Info&lvl=3&lin=f&keep=1&srchmode=1&unlock&id=<src_id>"
    search_body = {
        "_source": ["src_id", "id", "name", "label", "taxonomy_rank"],
        "query": {"term": {"id": species_id}},
    }

    result = es.search(
        index=settings.TERMS_INDEX, doc_type=settings.TERMS_DOCUMENT_TYPE, body=search_body
    )
    src = result["hits"]["hits"][0]["_source"]
    url = re.sub("(<src_id>)", src["src_id"], url_template)
    src["url"] = url
    del src["src_id"]
    return src


def get_species_object(species_id):

    species = get_species_info(species_id)
    return {"id": species["id"], "label": species["label"]}
