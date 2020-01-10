from typing import List

import structlog

import bel.db.arangodb
import bel.terms.terms

log = structlog.getLogger()

default_canonical_namespace = "EG"  # for genes, proteins

arangodb_client = bel.db.arangodb.get_client()


def get_orthologs(canonical_gene_id: str, species: list = []) -> List[dict]:
    """Get orthologs for given gene_id and species

    Canonicalize prior to ortholog query and decanonicalize
    the resulting ortholog

    Args:
        canonical_gene_id: canonical gene_id for which to retrieve ortholog
        species: target species for ortholog - tax id format TAX:<number>

    Returns:
        List[dict]: {'tax_id': <tax_id>, 'canonical': canonical_id, 'decanonical': decanonical_id}
    """

    gene_id_key = bel.db.arangodb.arango_id_to_key(canonical_gene_id)
    orthologs = {}

    if species:
        query_filter = f"FILTER vertex.tax_id IN {species}"

    query = f"""
        LET start = (
            FOR vertex in ortholog_nodes
                FILTER vertex._key == "{gene_id_key}"
                RETURN {{ "name": vertex.name, "tax_id": vertex.tax_id }}
        )

        LET orthologs = (
            FOR vertex IN 1..3
                ANY "ortholog_nodes/{gene_id_key}" ortholog_edges
                OPTIONS {{ bfs: true, uniqueVertices : 'global' }}
                {query_filter}
                RETURN DISTINCT {{ "name": vertex.name, "tax_id": vertex.tax_id }}
        )

        RETURN {{ 'orthologs': FLATTEN(UNION(start, orthologs)) }}
    """

    if not arangodb_client:
        print("Cannot get orthologs without ArangoDB access")
        quit()
    belns_db = bel.db.arangodb.get_belns_handle(arangodb_client)

    cursor = belns_db.aql.execute(query, batch_size=20)

    results = cursor.pop()
    for ortholog in results["orthologs"]:
        norms = bel.terms.terms.get_normalized_terms(ortholog["name"])
        orthologs[ortholog["tax_id"]] = {
            "canonical": norms["canonical"],
            "decanonical": norms["decanonical"],
        }

    return orthologs
