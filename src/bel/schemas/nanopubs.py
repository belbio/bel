# Standard Library
import enum
from typing import Any, List, Mapping, Optional, Union

# Third Party Imports
import pydantic
from pydantic import AnyUrl, BaseModel, Field


class NanopubType(BaseModel):
    name: str = "BEL"
    version: str = "latest"

    class Config:
        extra = "forbid"


class ValidationStatusEnum(str, enum.Enum):

    processing = "processing"
    good = "good"
    error = "error"
    warning = "warning"


class Validation(BaseModel):
    """Assertion and Annotation Validation results object"""

    status: ValidationStatusEnum = ValidationStatusEnum.processing
    errors: Optional[List[dict]]
    warnings: Optional[List[dict]]


class Annotation(BaseModel):
    type: Optional[str]
    label: Optional[str]
    id: Optional[str]
    validation: Optional[Validation]

    class Config:
        extra = "allow"


class Assertion(BaseModel):
    subject: str
    relation: Optional[str]
    object: Optional[str]
    validation: Optional[Validation]

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


class Metadata(BaseModel):

    collections: Optional[List[str]] = Field(
        [],
        title="Nanopub Collections",
        description="Collections of nanopubs to use for managing sets of nanopubs.",
    )
    gd_status: Optional[str]
    gd_createTS: Optional[str]
    gd_updateTS: Optional[str]
    gd_validation: Optional[List[dict]] = Field(
        [],
        title="Validation info",
        description="Validation messages - list of validation issues - if any",
    )
    gd_hash: Optional[str] = Field(
        "",
        title="Nanopub hash",
        description="non-crypto hash (xxHash64) to uniquely identify nanopub based on content",
    )

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
        extra = "forbid"


class NanopubR(BaseModel):
    """Nanopub Request/Response model"""

    source_url: Optional[str] = Field("", description="Source URL of Nanopub")

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


"""
Some of the attribute names are Python builtin functions or classes, for example id or type.
This situation seems not to bother when you use the names by attribute call, for example the calls obj.type or obj.id
work well; if you plan to use this structure to feed functions with parameter expansion, it will work as well,
but be aware that the parameter object will overload the builtin class or function.
Here is a sample of a nanopub record:
    nanopub_sample = {
        "type": {"name": "BEL", "version": "2.0.0"},
        "citation": {
            "authors": [
                "de Nigris, Filomena",
                "Lerman, Amir",
                "Ignarro, Louis J",
                "Williams-Ignarro, Sharon",
                "Sica, Vincenzo",
                "Baker, Andrew H",
                "Lerman, Lilach O",
                "Geng, Yong J",
                "Napoli, Claudio",
            ],
            "database": {"name": "PubMed", "id": "12928037"},
            "reference": "Trends in molecular medicine",
            "title": "Oxidation-sensitive mechanisms, vascular apoptosis and atherosclerosis.",
            "source_name": "Trends in molecular medicine",
            "date_published": "2003-08-01",
        },
        "assertions": [
            {
                "subject": "path(MESH:Atherosclerosis)",
                "relation": "positiveCorrelation",
                "object": 'bp(GO:"lipid oxidation")',
            },
            {
                "subject": "path(MESH:Atherosclerosis)",
                "relation": "positiveCorrelation",
                "object": 'bp(GO:"protein oxidation")',
            },
        ],
        "id": "127529922",
        "schema_uri": "https://raw.githubusercontent.com/belbio/Fields/master/Fields/nanopub_bel-1.1.0.yaml",
        "annotations": [
            {"type": "Disease", "label": "atherosclerosis", "id": "MESH:Atherosclerosis"},
            {"type": "Anatomy", "label": "artery", "id": "UBERON:artery"},
            {"type": "TextLocation", "label": "Review", "id": "Review"},
        ],
        "evidence": "Oxidation and nitration of macromolecules, such as proteins, DNA and lipids, are prominent in atherosclerotic arteries.",
        "metadata": {
            "gd:creator": "Selventa",
            "gd:published": False,
            "project": "selv_small_corpus",
        },
        "statement": [
            'path(MESH:Atherosclerosis) positiveCorrelation bp(GO:"lipid oxidation")',
            'path(MESH:Atherosclerosis) positiveCorrelation bp(GO:"protein oxidation")',
        ],
        "citationid": "PubMed12928037",
    }

"""
