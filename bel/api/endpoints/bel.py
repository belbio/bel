"""bel endpoints"""

# Standard Library
from typing import List, Optional

# Third Party
import fastapi
from fastapi import APIRouter, Body, Depends, Query
from loguru import logger

# Local
import bel.belspec.crud
import bel.lang.ast
import bel.nanopub.validate
from bel.schemas.bel import AssertionRequest, AssertionStr

router = APIRouter()


@router.get("/versions")
def get_bel_versions():
    """Get supported BEL versions"""

    return bel.belspec.crud.get_belspec_versions()


@router.get("/canonicalize/{bel_assertion}")
def get_bel_canonicalize(bel_assertion: str, version: str = "latest"):
    """Get Canonicalized Assertion"""

    assertion = AssertionStr(entire=bel_assertion)

    ast = bel.lang.ast.BELAst(assertion=assertion)

    canonicalized = ast.canonicalize().to_string()
    return {"canonicalized": canonicalized, "original": bel_assertion}


@router.get("/decanonicalize/{bel_assertion}")
def get_bel_decanonicalize(bel_assertion: str, version: str = "latest"):
    """Get De-canonicalized Assertion"""

    assertion = AssertionStr(entire=bel_assertion)

    ast = bel.lang.ast.BELAst(assertion=assertion)

    decanonicalized = ast.decanonicalize().to_string()

    return {"decanonicalized": decanonicalized, "original": bel_assertion}


# TODO
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

    return validated


@router.post("/optimize")
def optimize_assertion(
    assertion: AssertionStr,
    triple: bool = Query(
        False,
        description="Return Assertion as a Triple in a dictionary, default is to return Assertion as a single string",
    ),
):
    """Optimize BEL Assertion

    Transform BEL Assertion into more canonical BEL format

    Current transformations implemented:

    1. reactants(A, B) -> products(complex(A, B))  CONVERTED TO complex(A, B)
    1. reactants(A, loc(X)) -> products(A, loc(Y)) CONVERTED TO tloc(A, fromLoc(X), toLoc(Y))
    1. tloc(A, fromLoc(X), toLoc(extracellular region)) CONVERTED TO sec(A)
    1. tloc(A, fromLoc(X), toLoc(plasma membrane)) CONVERTED TO surf(A)

    """

    # BEL AST optimizations
    ast = bel.lang.ast.BELAst(assertion=assertion)
    ast.optimize()

    if triple:
        return ast.to_triple()

    return ast.to_string()
