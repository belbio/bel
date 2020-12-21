# Standard Library
import enum
from typing import Any, List, Mapping, Optional, Union

# Third Party
from pydantic import BaseModel, Field, HttpUrl

# Local
from bel.schemas.constants import AnnotationTypesEnum, EntityTypesEnum

Key = str  # Type alias for NsVal Key values

# key = ns:id
# main_key = preferred key, e.g. ns:<primary_id> not the alt_key or obsolete key or even an equivalence key which could be an alt_key
# alt_key = for HGNC the preferred key is HGNC:391 for the alt_key HGNC:AKT1 - where AKT1 is a secondary ID
# db_key = key converted to arangodb format


class Term(BaseModel):
    """Namespace term record - this must match the model in bel_resources"""

    key: str = Field("", description="Namespace:ID of term")
    namespace: str = ""
    id: str = ""
    label: str = ""

    name: str = ""
    description: str = ""
    synonyms: List[str] = []

    alt_keys: List[Key] = Field(
        [],
        description="Create Alt ID nodes/equivalence_keys (to support other database equivalences using non-preferred Namespace IDs)",
    )
    child_keys: List[Key] = []
    parent_keys: List[Key] = []
    obsolete_keys: List[Key] = []
    equivalence_keys: List[Key] = []

    species_key: Key = ""
    species_label: str = ""

    entity_types: List[EntityTypesEnum] = []
    annotation_types: List[AnnotationTypesEnum] = []


class TermCompletion(BaseModel):

    key: Key
    id: str
    name: str
    label: str
    description: str
    species_key: Key
    entity_types: List[EntityTypesEnum] = []
    annotation_types: List[AnnotationTypesEnum] = []
    matches: List[str] = []


class TermCompletionResponse(BaseModel):
    completion_text: str = Field(..., description="String used for term completions")
    completions: List[TermCompletion]


class Orthologs(BaseModel):
    """Ortholog equivalences - subject and object arbitrarily assigned by lexical ordering"""

    subject_key: Key
    subject_species_key: Key
    object_key: Key
    object_species_key: Key


# Needs to stay synced with bel_resources.schemas.main.Namespace
class Namespace(BaseModel):
    """Namespace Info"""

    name: str
    namespace: str = Field("", description="Namespace prefix - such as EG for EntrezGene")
    description: str = Field("", description="Namespace description")

    resource_type: str = "namespace"  # needed to distinguish BEL resource types
    namespace_type: str = Field(
        ...,
        description="[complete, virtual, identifiers_org] - complete type contains individual term records and is full-featured, virtual types only have [id_regex, species_key, annotation_types, entity_types] if available or if enabled - just the basic info from identifiers.org and defaults to all annotation and entity types",
    )

    version: Optional[str] = None

    source_name: str = Field("", description="Source name for namespace")
    source_url: Optional[HttpUrl] = Field(None, description="Source url for namespace")

    resource_download_url: Optional[HttpUrl] = Field(
        None, description="Download url for the resource as a *.jsonl.gz file"
    )

    entity_types: List[EntityTypesEnum] = []
    annotation_types: List[AnnotationTypesEnum] = []
    species_key: Key = Field("", description="Species key for this namespace")

    id_regex: str = Field(
        "", description="If identifiers_org=True, get id_regex from identifiers_org"
    )

    template_url: str = Field(
        "",
        description="Url template for terms - replace the {$id} with the namespace id for the term url",
    )
    example_url: Optional[HttpUrl] = None

    # Use url = https://registry.api.identifiers.org/restApi/namespaces/search/findByPrefix?prefix=<namespace>, e.g taxonomy or reactome
    identifiers_org: bool = Field(
        False,
        description="Identifiers.org namespace - if True - this is only a namespace definition without term records",
    )
    identifiers_org_namespace: Optional[str] = Field(None)
