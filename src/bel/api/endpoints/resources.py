"""resources endpoints"""

# Standard Library
from typing import List, Optional

# Third Party Imports
import fastapi
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from loguru import logger

# Local Imports
import bel.terms.terms
from bel.schemas.terms import Term, TermCompletionResponse
import bel.resources.manage

router = APIRouter()


@router.get("/resources/update")
def update_resources(url: str = None, force: bool = False, email: str = None):
    """Update bel resources

    Reads the arangodb bel.bel_config.configuration.update_bel_resources object
    to figure out what bel resource urls to process
    """

    bel.resources.manage.update_resources(url=url, force=force, email=email)


# @router.post("/resources/terms/import_file")
# def import_terms(
#     email: str = Query("", description="Notification email"), terms_file: Optional[UploadFile] = File(None), terms_url: Optional[str] = None
# ):
#     """Import terms
    
#     Add an email if you would like to be notified when the terms upload is completed.
#     """

#     return "Not implemented"


# @router.post("/resources/orthologs/import_file")
# def import_orthologs(
#     email: str = Query("", description="Notification email"), orthologs_file: Optional[UploadFile] = File(None), orthologs_url: Optional[str] = ""
# ):
#     """Import orthologs
    
#     Add an email if you would like to be notified when the ortholog upload is completed.
#     """

#     return "Not implemented"
