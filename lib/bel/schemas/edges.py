# Standard Library
from typing import List, Optional

# Third Party Imports
from pydantic import BaseModel, Schema


class Annotations(BaseModel):

    type: str
    label: str
    id: str


class Edge(BaseModel):
    """Edge database schema"""

    id: str  # converted to _key for storing in database

    subject: str
    subject_canon: str
    relation: str
    object: str
    object_canon: str

    species_id: str
    species_label: str

    nanopub_id: str
    nanopub_url: str
    nanopub_status: str
    citation: str
    species_id: str
    species_label: str
    annotations: List[Annotations]
    collections: List[str]

    edge_dt: str
    edge_hash: str
    edge_types: List[str]
    public_flag: bool
