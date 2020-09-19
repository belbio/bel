"""terms endpoints"""

# Standard Library
from typing import List

# Third Party
# Local Imports
import bel.terms.terms

# Third Party Imports
import fastapi
from bel.schemas.terms import Term, TermCompletionResponse
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from loguru import logger

router = APIRouter()


@router.get("/terms/types")
def get_term_types():
    """Get Term"""

    return bel.terms.terms.term_types()


# TODO add response_model=TermCompletionResponse to improve API docs
@router.get("/terms/completions/{completion_str}")
def get_term_completions(
    completion_str: str = Query(..., description="String to use for completion"),
    size: int = Query(21, description="Number of completions to return"),
    entity_types: str = Query(
        "",
        description="Entity types for completion request, concatenated using a comma",
    ),
    annotation_types: str = Query(
        "",
        description="Annotation types for completion request, concatenated using a comma, e.g. Tissue,Cell",
    ),
    species: str = Query(
        "",
        description="Species list for completion request, concatenated using a comma, e.g. TAX:9606,TAX:10090",
    ),
    namespaces: str = Query(
        "",
        description="Namespaces list for completion request, concatenated using a comma, e.g. HGNC,EG",
    ),
):
    """Get Term Completions"""

    entity_types = [item for item in entity_types.split(",") if item]
    annotation_types = [item for item in annotation_types.split(",") if item]
    species = [item for item in species.split(",") if item]
    namespaces = [item for item in namespaces.split(",") if item]

    completions = bel.terms.terms.get_term_completions(
        completion_str, size, entity_types, annotation_types, species, namespaces
    )

    return {"completion_text": completion_str, "completions": completions}


@router.get("/terms/{term_id}", response_model=List[Term])
def get_terms(term_id: str):
    """Get Term"""

    terms = bel.terms.terms.get_terms(term_id)

    if not terms:
        raise HTTPException(status_code=404, detail=f"Term {term_id} not found")

    return terms


@router.get("/terms/{term_id}/equivalents")
def get_term_equivalents(term_id: str):
    """Get Term Equivalents"""

    equivalents = bel.terms.terms.get_equivalents(term_id)

    if not equivalents:
        raise HTTPException(status_code=404, detail=f"Term {term_id} not found")

    return equivalents


@router.get("/terms/{term_id}/canonicalized")
def get_term_canonicalization(term_id: str):
    """Canonicalize term"""

    canonical_id = bel.terms.terms.get_normalized_terms(term_id)["canonical"]
    return {"term_id": canonical_id}


@router.get("/terms/{term_id}/decanonicalized")
def get_term_decanonicalization(term_id: str):
    """De-canonicalize term"""

    decanonical_id = bel.terms.terms.get_normalized_terms(term_id)["decanonical"]
    return {"term_id": decanonical_id}


@router.get("/terms/{term_key}/normalized")
def get_term_normalization(term_key: str):
    """Normalize term"""

    results = bel.terms.terms.get_normalized_terms(term_key)
    return results
