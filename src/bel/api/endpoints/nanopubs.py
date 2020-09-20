"""nanopub endpoints"""
# Standard Library
from typing import List

# Third Party Imports
import fastapi
from fastapi import APIRouter, Depends, HTTPException
from loguru import logger

# Local Imports
import bel.nanopub.validate
from bel.schemas.nanopubs import NanopubR

router = APIRouter()


@router.post("/nanopubs/validation")
def nanopub_validation(
    nanopub: NanopubR, validation_level: str = "complete", error_level: str = "warning"
):
    """Validate Nanopub

    Validation caches the BEL Assertion and Annnotation validations to speed up overall validation

    validation_level:   complete - fill in any missing assertion/annotation validations
                        force - redo all validations
                        cached - only return cached/pre-generated validations

    error_level:    warning - warning and errors to be reported
                    error - only errors to be reported
    """

    # Had issues with Falcon framework with bad request bodies - non-UTF8 content
    # data = data.decode(encoding="utf-8")
    # data = data.replace("\u00a0", " ")  # get rid of non-breaking spaces
    # data = json.loads(data)

    if nanopub:
        if isinstance(nanopub, NanopubR):
            nanopub = nanopub.dict()

        # use error_level in POST body if exists over query param
        error_level = nanopub.get("error_level", error_level)

        try:
            nanopub = bel.nanopub.validate.validate(
                nanopub, error_level=error_level, validation_level=validation_level
            )
        except Exception as e:
            logger.exception("Could not validate nanopub", error=str(e))
            raise HTTPException(400, detail=f"Could not validate nanopub, error: {str(e)}")

        return nanopub

    raise HTTPException(400, detail=f"No nanopub provided, error: {str(e)}")
