"""pubmed endpoints"""

# Third Party Imports
import fastapi
from loguru import logger
from fastapi import APIRouter, Depends, Query, HTTPException

# Local Imports
import bel.nanopub.pubmed


router = APIRouter()


@router.get("/pubmed/{pmid}")
def get_pubmed_info(
    pmid: str,
    pubmed_only: bool = Query(
        False, description="If true, only return Pubmed without Pubtator results"
    ),
):
    """Get Pubmed Info"""

    pubmed = bel.nanopub.pubmed.get_pubmed_for_beleditor(pmid, pubmed_only=pubmed_only)

    if pubmed is None:
        raise HTTPException(status_code=404, detail=f"No Pubmed response for {pmid}")

    return pubmed
