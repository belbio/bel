"""nanopub endpoints"""
# Standard Library
from typing import List

# Third Party
# Local Imports
import bel.nanopub.validate

# Third Party Imports
import fastapi
from bel.schemas.nanopubs import NanopubR
from fastapi import APIRouter, Depends, HTTPException
from loguru import logger

router = APIRouter()


@router.post("/nanopubs/validation", response_class=NanopubR)
def nanopub_validation(nanopub: NanopubR, validation_level: str = "complete"):
    """Validate Nanopub

    Validation caches the BEL Assertion and Annnotation validations to speed up overall validation

    validation_level:   complete - fill in any missing assertion/annotation validations
                        force - redo all validations
                        cached - only return cached/pre-generated validations
    """

    # Had issues with Falcon framework with bad request bodies - non-UTF8 content
    # data = data.decode(encoding="utf-8")
    # data = data.replace("\u00a0", " ")  # get rid of non-breaking spaces
    # data = json.loads(data)

    if not nanopub:
        raise HTTPException(400, detail=f"No nanopub provided")

    nanopub = bel.nanopub.validate.validate(nanopub, validation_level=validation_level)

    return nanopub