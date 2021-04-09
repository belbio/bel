# Standard Library
import enum
from typing import Any, List, Mapping, Optional, Union

# Third Party
import dateparser
import pydantic
from loguru import logger
from pydantic import AnyUrl, BaseModel, Field, HttpUrl, validator

# Local
from bel.schemas.bel import ValidationErrors


class NanopubType(BaseModel):
    name: str = "BEL"
    version: str = "latest"

    class Config:
        extra = "forbid"


class Annotation(BaseModel):
    type: Optional[str]
    label: Optional[str]
    id: Optional[str]
    validation: Optional[ValidationErrors]

    class Config:
        extra = "allow"


class Assertion(BaseModel):
    subject: str
    relation: Optional[str]
    object: Optional[str]
    validation: Optional[ValidationErrors]

    class Config:
        extra = "allow"


class CitationDatabase(BaseModel):
    name: str
    id: str

    class Config:
        extra = "forbid"


class Citation(BaseModel):
    id: Optional[str]
    authors: Optional[List[str]]
    database: Optional[CitationDatabase]
    reference: Optional[str]
    uri: Optional[str]
    title: Optional[str]
    source_name: Optional[str]
    date_published: Optional[str]

    @validator("date_published", check_fields=False)
    def format_date(cls, val):  # pylint: disable=no-self-argument
        """Reset group id to None. Groups cannot be nested inside a group."""

        if not val:
            return val

        original = val
        try:
            val = dateparser.parse(val, settings={"PREFER_DAY_OF_MONTH": "first"})
            val = val.strftime("%Y-%m-%d")
        except Exception as e:
            logger.error(
                f"Could not parse original date value: {original} for nanopub citation date_published"
            )
            val = "1900-01-01"
        return val

    class Config:
        extra = "allow"


class Metadata(BaseModel):

    collections: Optional[Union[str, List[str]]] = Field(
        [],
        title="Nanopub Collections",
        description="Collections of nanopubs to use for managing sets of nanopubs.",
    )
    gd_status: Optional[str]
    gd_createTS: Optional[str]
    gd_updateTS: Optional[str]
    gd_validation: Optional[ValidationErrors]
    gd_hash: Optional[str] = Field(
        "",
        title="Nanopub hash",
        description="non-crypto hash (xxHash64) to uniquely identify nanopub based on content",
    )

    # @validator("gd_validation")
    # def fix_gd_validation(cls, v):
    #     if not (isinstance(v, dict)):
    #         v = {}
    #     return v

    class Config:
        extra = "allow"


class NanopubBody(BaseModel):
    """Nanopub content"""

    type: NanopubType
    citation: Citation
    assertions: List[Assertion]
    id: Optional[str]
    schema_uri: Optional[
        AnyUrl
    ] = "https://raw.githubusercontent.com/belbio/Fields/master/Fields/nanopub_bel-1.1.0.yaml"
    annotations: Optional[List[Annotation]] = []
    evidence: Optional[str] = ""
    metadata: Optional[Metadata] = {}

    class Config:
        extra = "forbid"


class Nanopub(BaseModel):
    """Nanopub model"""

    nanopub: NanopubBody

    class Config:
        extra = "allow"


class NanopubR(BaseModel):
    """Nanopub Request/Response model"""

    source_url: Optional[str] = Field(None, description="Source URL of Nanopub")

    nanopub: NanopubBody

    class Config:
        extra = "allow"


class NanopubDB(Nanopub):
    """Nanopub Database Entry with additional top-level keys"""

    owners: List[str] = []
    groups: List[str] = []
    is_deleted: bool = False
    is_archived: bool = False
    is_public: bool = True

    class Config:
        extra = "allow"
