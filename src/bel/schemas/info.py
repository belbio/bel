# Third Party Imports
# Standard Library
from typing import Optional, Union

# Third Party
from pydantic import BaseModel, Field


class Version(BaseModel):
    version: str


class Status(BaseModel):
    state: str
    belapi_version: str
    bel_version: str
    # settings: dict
    # elasticsearch_stats: dict
    fastapi_version: str
