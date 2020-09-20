"""orthologs endpoints"""

# Standard Library
from typing import List

# Third Party Imports
import fastapi
from fastapi import APIRouter, Depends, File, Query, UploadFile
from loguru import logger

# Local Imports
import bel.terms.orthologs

router = APIRouter()


@router.get("/orthologs/{gene_id}")
@router.get("/orthologs/{gene_id}/{species}")
def get_orthologs(gene_id: str, species: str = ""):

    species = [item for item in species.split(",") if item]

    orthologs = bel.terms.orthologs(gene_id, species)

    return {"orthologs": orthologs}


@router.post("/orthologs/import_file", include_in_schema=False)
def import_orthologs(
    email: str = Query("", description="Notification email"), orthologs_file: UploadFile = File(...)
):
    """Import orthologs

    Add an email if you would like to be notified when the ortholog upload is completed.
    """

    return "Not implemented"
