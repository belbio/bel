"""bel endpoints"""

# Standard Library
from typing import List, Optional

# Third Party Imports
import fastapi
from fastapi import APIRouter, Depends, Query
from loguru import logger

# Local Imports
import bel.belspec.crud

router = APIRouter()


@router.get("/versions")
def get_bel_versions():
    """Get supported BEL versions"""

    return bel.belspec.crud.get_belspec_versions()


# TODO
@router.get("/canonicalize/{belstr}")
def get_bel_canonicalize(belstr: str, version: str = "latest"):
    """Get Canonicalized Assertion"""

    # bel_obj = BEL(version=version, api_url=api_url)

    # canon_belstr = (
    #     bel_obj.parse(belstr).canonicalize(namespace_targets=namespace_targets).to_string()
    # )

    # # TODO figure out how to handle naked namespace:val better
    # if not canon_belstr:
    #     canon_belstr = bel.terms.terms.canonicalize(belstr)

    # return {"canonicalized": canon_belstr, "original": belstr}
    pass


# TODO
@router.get("/decanonicalize/{belstr}")
def get_bel_decanonicalize(belstr: str, version: str = "latest"):
    """Get De-canonicalized Assertion"""

    # api_url = config["bel_api"]["servers"]["api_url"]
    # bel_obj = BEL(version=version, api_url=api_url)

    # decanon_belstr = bel_obj.parse(belstr).decanonicalize().to_string()

    # return {"decanonicalized": decanon_belstr, "original": belstr}
    pass


# @router.get("/bel/migrate12/{belstr}", tags=["BEL"])
# def get_bel_migration12(belstr: str):
#     """Migrate BEL 1 assertion to BEL latest"""

#     belstr = bel.lang.migrate_1_2.migrate(belstr)

#     return {"bel": belstr}
