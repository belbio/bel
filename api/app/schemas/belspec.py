# Third Party Imports
# Standard Library
import enum
from typing import Any, List, Mapping, Optional, Union

# Local Imports
from pydantic import BaseModel, Field


class BelSpecRequest(BaseModel):
    """BEL Spec Request Model"""

    belspec: dict = Field(None, description="BEL Specification")
    bel_help: dict = Field(None, description="BEL Help info for BEL functions and relations")


class BelSpecResponse(BelSpecRequest):
    """BEL Spec Response Model"""

    format: str = Field("json", description="")
    enhanced_belspec: dict = Field(
        None, description="Enhanced BEL Specification created from BEL Specification - "
    )


class BelSpecVersions(BaseModel):

    versions: List[str]
