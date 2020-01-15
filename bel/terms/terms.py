import re
from typing import List, Mapping, Union

import bel.db.arangodb
import bel.db.elasticsearch
import structlog
from bel.Config import config

# import logging
# log = logging.getLogger(__name__)


log = structlog.getLogger()

es = bel.db.elasticsearch.get_client()

arangodb_client = bel.db.arangodb.get_client()


def get_terms(term_id):
    """Get term(s) using term_id - given term_id may match multiple term records

    Term ID has to match either the id, alt_ids or obsolete_ids
    """

    search_body = {
        "query": {
            "bool": {
                "should": [
                    {"term": {"id": term_id}},
                    {"term": {"alt_ids": term_id}},
                    {"term": {"obsolete_ids": term_id}},
                ]
            }
        }
    }

    result = es.search(index="terms", body=search_body)

    results = []
    for r in result["hits"]["hits"]:
        results.append(r["_source"])

    return results


def get_equivalents(term_id: str) -> List[Mapping[str, Union[str, bool]]]:
    """Get equivalents given ns:id


    Args:
        term_id (str): term id
    Returns:
        List[Mapping[str, Union[str, bool]]]: e.g. [{'term_id': 'HGNC:5', 'namespace': 'HGNC'}, 'primary': False]
    """
    if not arangodb_client:
        print("Cannot get equivalents without arangodb access")
        quit()

    belns_db = bel.db.arangodb.get_belns_handle(arangodb_client)

    try:
        errors = []
        terms = get_terms(term_id)
        if len(terms) == 0:
            return {"equivalents": [], "errors": errors}
        elif len(terms) > 1:
            errors.append(
                f'Too many primary IDs returned. Given term_id: {term_id} matches these term_ids: {[term["id"] for term in terms]}'
            )
            return {"equivalents": [], "errors": errors}
        else:
            term_id = terms[0]["id"]

        term_id_key = bel.db.arangodb.arango_id_to_key(term_id)

        equivalents = []
        query = f"""
        FOR vertex, edge IN 1..5
            ANY 'equivalence_nodes/{term_id_key}' equivalence_edges
            OPTIONS {{bfs: true, uniqueVertices : 'global'}}
            RETURN DISTINCT {{
                term_id: vertex.name,
                namespace: vertex.namespace,
                primary: vertex.primary
            }}
        """

        cursor = belns_db.aql.execute(query, count=True, batch_size=20)
        for doc in cursor:
            if doc.get("term_id", False):
                equivalents.append(doc)

        equivalents.append(
            {"term_id": term_id, "namespace": term_id.split(":")[0], "primary": True}
        )

        return {"equivalents": equivalents, "errors": errors}

    except Exception as e:
        log.error(f"Problem getting term equivalents for {term_id} msg: {e}")
        return {"equivalents": [], "errors": [f"Unexpected error {e}"]}


def get_normalized_term(term_id: str, equivalents: list, namespace_targets: dict) -> str:
    """Get normalized term"""

    if equivalents and len(equivalents) > 0:
        for start_ns in namespace_targets:
            if re.match(start_ns, term_id):
                for target_ns in namespace_targets[start_ns]:
                    for e in equivalents:
                        if e and target_ns in e["namespace"] and e["primary"]:
                            normalized_term = e["term_id"]
                            return normalized_term

    return term_id


def get_labels(term_ids: list) -> dict:
    """Get term labels given term ids

    This only takes the first term returned for a term_id so use the
    unique term_id for a term not an alternate id that might not be unique.
    """
    term_labels = {}
    for term_id in term_ids:
        term = get_terms(term_id)
        term_labels[term_id] = term[0].get("label", "")

    return term_labels


def get_normalized_terms(term_id: str) -> dict:
    """Get normalized terms - canonical/decanonical forms"""

    canonical = term_id
    decanonical = term_id

    canonical_namespace_targets = config["bel"]["lang"]["canonical"]
    decanonical_namespace_targets = config["bel"]["lang"]["decanonical"]
    results = get_equivalents(term_id)
    equivalents = results["equivalents"]

    # log.debug(f'Equivalents: {equivalents}')

    if equivalents:
        canonical = get_normalized_term(term_id, equivalents, canonical_namespace_targets)
        decanonical = get_normalized_term(canonical, equivalents, decanonical_namespace_targets)

    # log.debug(f'canonical: {canonical}, decanonical: {decanonical}, original: {term_id}')

    return {"canonical": canonical, "decanonical": decanonical, "original": term_id}
