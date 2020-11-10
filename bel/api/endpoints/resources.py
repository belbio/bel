"""resources endpoints"""

# Standard Library
from typing import List, Optional

# Third Party
# Third Party Imports
import fastapi
from fastapi import APIRouter, Body, Depends, File, HTTPException, Query, UploadFile
from loguru import logger

# Local
import bel.resources.manage

# Local Imports
import bel.terms.terms
from bel.schemas.terms import Term, TermCompletionResponse

router = APIRouter()


@router.post("/resources/update")
def post_update_resources(
    url: str = None,
    urls: List[str] = Body([], description="List of URLs of BEL Resources to add or update"),
    force: bool = False,
    email: str = None,
):
    """Update bel resources

    Reads the arangodb bel.bel_config.configuration.update_bel_resources object
    to figure out what bel resource urls to process if url or urls not included.

    Will ignore _urls_ if _url_ query parameter is provided.
    """

    if url:
        urls = [url]

    urls = [url for url in urls if url != "string"]

    bel.resources.manage.update_resources(urls=urls, force=force, email=email)


@router.delete("/resources/{source}")
def delete_resource(
    source: str = Query(
        ...,
        description="The source is the metadata namespace value, e.g. HGNC, GO, DO, etc for namespaces or the ortholog metadata source name, e.g. Orthologs_EntrezGene",
    ),
    resource_type: str = Query(
        "namespace", description="Type of resource to be deleted: namespace or ortholog"
    ),
):
    """Delete resource (namespace, ortholog, etc)

    The source value is the metadata namespace value, e.g. HGNC, GO, DO, etc for namespaces or the ortholog metadata source name, e.g. Orthologs_EntrezGene
    """

    bel.resources.manage.delete_resource(source, resource_type=resource_type)
