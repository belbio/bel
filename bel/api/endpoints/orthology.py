"""orthologs endpoints"""

# Standard Library
from typing import List

# Third Party
import fastapi
from fastapi import APIRouter, Depends, File, Query, UploadFile
from loguru import logger

# Local
import bel.terms.orthologs

router = APIRouter()


@router.get("/orthologs/{gene_id}")
@router.get("/orthologs/{gene_id}/{species}")
def get_orthologs(gene_id: str, species: str = ""):

    species = [item for item in species.split(",") if item]

    orthologs = bel.terms.orthologs.get_orthologs(gene_id, species)

    return {"orthologs": orthologs}
