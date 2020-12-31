# Standard Library
import enum
from typing import Any, List, Mapping, Optional, Union

# Third Party
import pydantic
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
    metadata: Optional[dict]

    class Config:
        extra = "forbid"


class Nanopub(BaseModel):
    """Nanopub model"""

    nanopub: NanopubBody

    class Config:
        extra = "forbid"


class Nanopub(BaseModel):
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
