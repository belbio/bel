"""belspec endpoints"""

# Third Party Imports
import fastapi
from loguru import logger
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import PlainTextResponse

# Local Imports
import bel.belspec.crud
from bel.schemas.belspec import BelSpec, BelSpecVersions, EnhancedBelSpec

router = APIRouter()


# TODO Add response_model for api documentation -- response_model=BelSpec (from bel library schemas)
@router.get("/belspec")
def get_belspec_version(version: str = "latest"):
    """Get BEL Specification"""

    if version == "latest":
        version = bel.belspec.crud.get_latest_version()

    return bel.belspec.crud.get_enhanced_belspec(version)


# TODO Add response_model for api documentation -- response_model=EnhancedBelSpec (from bel library schemas)
@router.get("/belspec/enhanced")
def get_enhanced_belspec(version: str = "latest"):
    """Get Enhanced BEL Specification"""

    enhanced_belspec = bel.belspec.crud.get_enhanced_belspec(version)
    if not enhanced_belspec:
        raise HTTPException(
            status_code=404, detail=f"No enhanced bel specification for version {version}",
        )
    else:
        return enhanced_belspec


# TODO needs testing


@router.get("/belspec/ebnf", response_class=PlainTextResponse)
def get_ebnf(version: str = "latest"):
    """Get EBNF BEL Grammar file
    
    WARNING: This is not known to be actively used and is therefore not thoroughly tested/validated. 
             We are always happy to accept Pull Requests to improve the EBNF generated from BEL Specifications.

    EBNF stands for Extended Backus-Naur Form and is used to describe the grammar for BEL to aid in creating parsers.
    
    The BEL.bio BEL library and API depends on a custom character-based parser to allow maximum flexibility in parsing 
    and parsing error reporting/feedback to the library users.
    """

    return bel.belspec.crud.get_ebnf(version)


@router.get("/belspec/help")
def get_latest_belhelp(version: str = "latest"):
    """Get latest BEL help for BEL functions and relations"""
    version = bel.belspec.crud.get_latest_version()
    return bel.belspec.crud.get_belhelp(version)


@router.get("/belspec/help/{version}")
def get_belhelp(version: str = "latest"):
    """Get BEL Help for BEL functions and relations"""

    if version == "latest":
        version = bel.belspec.crud.get_latest_version()

    return bel.belspec.crud.get_belhelp(version)


@router.post("/belspec/help")
def post_belhelp(belhelp: dict):
    """Create or Update BEL Help"""

    bel.belspec.crud.update_belhelp(belhelp)


@router.delete("/belspec/help/{version}")
def delete_belhelp(version: str):
    """Delete BEL Help"""

    if version == "latest":
        version = bel.belspec.crud.get_latest_version()

    bel.belspec.crud.delete_belhelp(version)


@router.get("/belspec/versions", response_model=BelSpecVersions)
def get_belspec_versions():
    """Get list of all BEL Specification versions - but not the actual specifications"""
    versions = ["latest"] + bel.belspec.crud.get_belspec_versions()
    return versions


@router.post("/belspec")
def post_belspec(belspec: BelSpec):
    """Create or Update BEL Specification

    The enhanced BEL Specification will be created from this BEL Specification
    """

    bel.belspec.crud.update_belspec(belspec)

    return {"msg": "ok"}


@router.delete("/belspec/{version}")
def delete_belspec(version: str):

    if version == "latest":
        version = bel.belspec.crud.get_latest_version()

    bel.belspec.crud.delete_belspec(version)
