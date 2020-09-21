# Standard Library
from typing import List, Mapping

# Third Party
# Local Imports
import bel.db.arangodb
import bel.terms.terms
import cachetools
from bel.db.arangodb import ortholog_edges_name, ortholog_nodes_name, resources_db

# Third Party Imports
from loguru import logger

Key = str


def get_orthologs(term_key: Key, species: List[Key] = []) -> Mapping[Key, Key]:
    """Get orthologs for given gene and species

    Args:
        term_key: gene, rna or protein term key for which to retrieve orthologs
        species: target species keys for ortholog - e.g. TAX:<number>

    Returns:
        Mapping[Key, Key]: {"TAX:9606": "EG:207"}
    """

    # Normalize first
    canonical_key = bel.terms.terms.get_normalized_terms(term_key)["canonical"]

    canonical_dbkey = bel.db.arangodb.arango_id_to_key(canonical_key)

    orthologs = {}

    query_filter = ""
    if species:
        query_filter = f"FILTER vertex.tax_id IN {species}"

    query = f"""
        LET start = (
            FOR vertex in {ortholog_nodes_name}
                FILTER vertex._key == "{canonical_dbkey}"
                RETURN {{ "key": vertex.key, "species_key": vertex.species_key }}
        )

        LET orthologs = (
            FOR vertex IN 1..3
                ANY "ortholog_nodes/{canonical_dbkey}" {ortholog_edges_name}
                OPTIONS {{ bfs: true, uniqueVertices : 'global' }}
                {query_filter}
                RETURN DISTINCT {{ "key": vertex.key, "species_key": vertex.species_key }}
        )

        RETURN {{ "orthologs": FLATTEN(UNION(start, orthologs)) }}
    """

    logger.debug("Orthologs query", query=query)

    results = list(resources_db.aql.execute(query, ttl=60, batch_size=20))[0]["orthologs"]

    for ortholog in results:
        orthologs[ortholog["species_key"]] = ortholog["key"]

    return orthologs
