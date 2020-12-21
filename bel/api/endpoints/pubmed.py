"""pubmed endpoints"""


# Third Party
import fastapi
from fastapi import APIRouter, Depends, Query
from loguru import logger

# Local
import bel.nanopub.pubmed
from bel.api.core.exceptions import HTTPException

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
        raise HTTPException(
            status_code=404, detail=f"No Pubmed response for {pmid}", user_flag=True
        )

    return pubmed
