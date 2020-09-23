"""bel endpoints"""

# Standard Library
from typing import List, Optional

# Third Party
# Third Party Imports
import fastapi
from fastapi import APIRouter, Depends, Query

# Local Imports
from loguru import logger

# Local
import bel.belspec.crud
import bel.nanopub.validate
from bel.schemas.bel import AssertionStr

router = APIRouter()


@router.get("/versions")
def get_bel_versions():
    """Get supported BEL versions"""

    return bel.belspec.crud.get_belspec_versions()


# TODO
@router.get("/canonicalize/{bel_assertion}")
def get_bel_canonicalize(bel_assertion: str, version: str = "latest"):
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
@router.get("/decanonicalize/{bel_assertion}")
def get_bel_decanonicalize(bel_assertion: str, version: str = "latest"):
    """Get De-canonicalized Assertion"""

    # api_url = config["bel_api"]["servers"]["api_url"]
    # bel_obj = BEL(version=version, api_url=api_url)

    # decanon_belstr = bel_obj.parse(belstr).decanonicalize().to_string()

    # return {"decanonicalized": decanon_belstr, "original": belstr}
    pass


# @router.get("/bel/migrate12/{bel_assertion}", tags=["BEL"])
# def get_bel_migration12(bel_assertion: str):
#     """Migrate BEL 1 assertion to BEL latest"""

#     belstr = bel.lang.migrate_1_2.migrate(belstr)

#     return {"bel": belstr}


@router.get("/validate/{bel_assertion}")
def validate_assertion(bel_assertion: str):
    """Validate BEL Assertion"""

    validated = bel.nanopub.validate.validate_assertion(AssertionStr(entire=bel_assertion))

    logger.info(f"Validated: {validated}")

    return validated.json()
