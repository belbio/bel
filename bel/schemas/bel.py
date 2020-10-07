# Standard Library
import copy
import enum
import json
import re
from typing import Any, List, Mapping, Optional, Tuple, Union

# Third Party
# Third Party Imports
from loguru import logger
from pydantic import BaseModel, Field, root_validator

# Local
# Local Imports
import bel.core.settings as settings
import bel.db.arangodb
import bel.terms.orthologs
import bel.terms.terms
from bel.core.utils import namespace_quoting, split_key_label
from bel.resources.namespace import get_namespace_metadata
from bel.schemas.constants import AnnotationTypesEnum, EntityTypesEnum
from bel.schemas.terms import Term

Key = str  # Type alias for NsVal Key values
NamespacePattern = r"[\w\.]+"  # Regex for Entity Namespace


class SpanTypesEnum(str, enum.Enum):

    function = "function"
    function_name = "function_name"
    function_args = "function_args"
    relation = "relation"
    ns_arg = "ns_arg"
    namespace = "namespace"
    ns_id = "ns_id"
    ns_label = "ns_label"
    string_arg = "string_arg"
    string = "string"
    start_paren = "start_paren"
    end_paren = "end_paren"


class Span(BaseModel):
    """Used for collecting string spans

    The spans are collect by the index of the first char of the span and the non-inclusive
    end of the last span character.

    For example:
        'cat' with a span of [0, 2] results in 'ca'

    You can use -1 as the span end for 1 beyond the last character of the string.
    """

    start: int = Field(..., title="Span Start")
    end: int = Field(..., title="Span End")

    span_str: str = ""

    type: Optional[SpanTypesEnum]


class NsArgSpan(Span):
    """Namespace Arg Span"""

    namespace: Span
    id: Span
    label: Optional[Span]


class FunctionSpan(Span):

    name: Span  # function name span
    args: Optional[Span]  # parentheses span


class Pair(BaseModel):
    """Paired characters

    Used for collecting matched quotes and parentheses
    """

    start: Union[int, None] = Field(..., description="index of first in paired chars")
    end: Union[int, None] = Field(..., description="Index of second of paired chars")


class ErrorLevelEnum(str, enum.Enum):

    Good = "Good"
    Error = "Error"
    Warning = "Warning"
    Processing = "Processing"


class ValidationErrorType(str, enum.Enum):

    Nanopub = "Nanopub"
    Assertion = "Assertion"
    Annotation = "Annotation"


class ValidationError(BaseModel):
    type: ValidationErrorType
    severity: ErrorLevelEnum
    label: str = Field(
        "",
        description="Label used in search - combination of type and severity, e.g. Assertion-Warning",
    )
    msg: str
    visual: Optional[str] = Field(
        None,
        description="Visualization of the location of the error in the Assertion string or Annotation using html span tags",
    )
    visual_pairs: Optional[List[Tuple[int, int]]] = Field(
        None,
        description="Used when the Assertion string isn't available. You can then post-process these pairs to create the visual field.",
    )
    index: int = Field(
        0,
        description="Index to sort validation errors - e.g. for multiple errors in Assertions - start at the beginning of the string.",
    )

    @root_validator(pre=True)
    def set_label(cls, values):
        label, type_, severity = (values.get("label"), values.get("type"), values.get("severity"))

        if not label:
            label = f"{type_}-{severity}"
            values["label"] = label.strip()
        return values


class ValidationErrors(BaseModel):
    status: Optional[ErrorLevelEnum] = "Good"
    errors: Optional[List[ValidationError]]
    validation_target: Optional[str]


class AssertionStr(BaseModel):
    """Assertion string object - to handle either SRO format or simple string of full assertion"""

    entire: str = Field(
        "",
        description="Will be dynamically created from the SRO fields if null/empty when initialized.",
    )
    subject: str = ""
    relation: str = ""
    object: str = ""

    @root_validator(pre=True)
    def set_entire(cls, values):
        entire, subject, relation, object_ = (
            values.get("entire"),
            values.get("subject"),
            values.get("relation"),
            values.get("object"),
        )
        if subject is None:
            subject = ""
        if relation is None:
            relation = ""
        if object_ is None:
            object_ = ""

        if not entire:
            entire = f"{subject} {relation} {object_}"
            values["entire"] = entire.strip()

        return values


class NsVal(object):
    """Namespaced value"""

    def __init__(self, key_label: str = "", namespace: str = "", id: str = "", label: str = ""):
        """Preferentially use key_label to extract namespace:id!Optional[label]"""

        if key_label:
            (namespace, id, label) = split_key_label(key_label)

        self.namespace: str = namespace
        self.id: str = namespace_quoting(id)

        self.label = ""
        if label:
            self.label: str = namespace_quoting(label)

        self.key: Key = f"{self.namespace}:{self.id}"  # used for dict keys and entity searches

        # Add key_label to NsVal
        self.update_key_label()

    def add_label(self):
        if not self.label:
            self.update_label()

        return self

    def update_label(self):
        term = bel.terms.terms.get_term(self.key)
        if term and term.label:
            self.label = namespace_quoting(term.label)

        return self

    def db_key(self):
        """Used for arangodb key"""

        return bel.db.arangodb.arango_id_to_key(self.key)

    def update_key_label(self):
        """Return key with label if available"""

        self.add_label()

        if self.label:
            self.key_label = f"{self.namespace}:{self.id}!{self.label}"
        else:
            self.key_label = f"{self.namespace}:{self.id}"

        return self.key_label

    def __str__(self):

        if self.label:
            return f"{self.namespace}:{self.id}!{self.label}"
        else:
            return f"{self.namespace}:{self.id}"

    __repr__ = __str__

    def __len__(self):
        return len(self.__str__())


class BelEntity(object):
    """BEL Term - supports original NsVal ns:id!label plus (de)canonicalization and orthologs"""

    def __init__(self, term_key: Key = "", nsval: Optional[NsVal] = None):
        """Create BelEntity via a term_key or a NsVal object

        You cannot provide a term_key_label string (e.g. NS:ID:LABEL) as a term_key
        """

        self.term: Optional[Term] = None

        self.canonical: Optional[NsVal] = None
        self.decanonical: Optional[NsVal] = None

        self.species_key: Key = None
        self.entity_types = []

        self.orthologs: Mapping[Key, dict] = {}
        self.orthologized: bool = False
        self.orthologized_species_key: Optional[Key] = None

        # NOTE - self.nsval is overridden when orthologized

        if term_key:
            self.original_term_key = term_key
            self.term = bel.terms.terms.get_term(term_key)

            if self.term:
                self.species_key = self.term.species_key

            self.nsval: NsVal = NsVal(
                namespace=self.term.namespace, id=self.term.id, label=self.term.label
            )
            self.original_nsval = self.nsval
        elif nsval:
            self.nsval = nsval
            self.original_nsval = nsval
        else:
            self.nsval = None

        self.namespace_metadata = get_namespace_metadata().get(self.nsval.namespace, None)
        if self.namespace_metadata is not None and self.namespace_metadata.entity_types:
            self.entity_types = self.namespace_metadata.entity_types

        self.add_term()

    def add_term(self):
        """Add term info"""

        if self.namespace_metadata and self.namespace_metadata.namespace_type == "complete":
            self.term = bel.terms.terms.get_term(self.nsval.key)
            if self.term and self.nsval.key != self.term.key:
                self.nsval = NsVal(
                    namespace=self.term.namespace, id=self.term.id, label=self.term.label
                )
            if self.term and self.term.entity_types:
                self.entity_types = self.term.entity_types
            if self.term and self.term.species_key:
                self.species_key = self.term.species_key

        return self

    def add_species(self):
        """Add species if not already set"""

        if self.species_key:
            return self

        if not self.term:
            self.add_term()

        if self.term.species_key:
            self.species_key = self.term.species_key
        elif self.namespace_metadata.species_key:
            self.species_key = self.namespace_metadata.species_key

        return self

    def add_entity_types(self):
        """get entity_types to BEL Entity"""

        if self.entity_types:
            return self

        entity_types = []
        if self.term:
            entity_types = self.term.entity_types

        elif self.namespace_metadata and self.namespace_metadata.namespace_type == "complete":
            self.term = bel.terms.terms.get_term(self.nsval.key)
            if self.term:
                entity_types = self.term.entity_types

        elif self.namespace_metadata and self.namespace_metadata.entity_types:
            entity_types = self.namespace_metadata.entity_types

        self.entity_types = [et.name for et in entity_types]

        return self

    def get_entity_types(self):

        if not self.entity_types:
            self.add_entity_types()

        return self.entity_types

    def normalize(
        self,
        canonical_targets: Mapping[str, List[str]] = settings.BEL_CANONICALIZE,
        decanonical_targets: Mapping[str, List[str]] = settings.BEL_DECANONICALIZE,
    ):
        """Collect (de)canonical forms"""

        if self.canonical and self.decanonical:
            return self

        if self.namespace_metadata and self.namespace_metadata.namespace_type != "complete":
            self.canonical = self.nsval
            self.decanonical = self.nsval
            return self

        normalized = bel.terms.terms.get_normalized_terms(
            self.nsval.key,
            canonical_targets=canonical_targets,
            decanonical_targets=decanonical_targets,
            term=self.term,
        )

        if normalized["original"] != normalized["normalized"]:
            self.nsval = NsVal(key_label=normalized["normalized"])
            if self.original_nsval.label:
                self.nsval.label = self.original_nsval.label

        self.canonical = self.nsval
        if normalized["canonical"]:
            self.canonical = NsVal(key_label=normalized["canonical"])

        self.decanonical = self.nsval
        if normalized["decanonical"]:
            self.decanonical = NsVal(key_label=normalized["decanonical"])

        return self

    def canonicalize(
        self,
        canonical_targets: Mapping[str, List[str]] = settings.BEL_CANONICALIZE,
        decanonical_targets: Mapping[str, List[str]] = settings.BEL_DECANONICALIZE,
    ):
        """Canonicalize BEL Entity

        Must set both targets if not using defaults as the underlying normalization handles
        both canonical and decanonical forms in the same query
        """

        if self.orthologized:
            self.nsval = self.orthologs[self.orthologized_species_key]["canonical"]

        else:
            self.normalize(
                canonical_targets=settings.BEL_CANONICALIZE,
                decanonical_targets=settings.BEL_DECANONICALIZE,
            )
            self.nsval = self.canonical

        return self

    def decanonicalize(
        self,
        canonical_targets: Mapping[str, List[str]] = settings.BEL_CANONICALIZE,
        decanonical_targets: Mapping[str, List[str]] = settings.BEL_DECANONICALIZE,
    ):
        """Decanonicalize BEL Entity

        Must set both targets if not using defaults as the underlying normalization handles
        both canonical and decanonical forms in the same query
        """

        if self.orthologized:
            self.nsval = self.orthologs[self.orthologized_species_key]["decanonical"]
        else:
            self.normalize(
                canonical_targets=settings.BEL_CANONICALIZE,
                decanonical_targets=settings.BEL_DECANONICALIZE,
            )
            self.nsval = self.decanonical

        return self

    def collect_orthologs(self, species_keys: List[Key] = settings.BEL_ORTHOLOGIZE_TARGETS):
        """Get orthologs for BelEntity is orthologizable"""

        self.add_entity_types()
        self.normalize()
        self.add_species()

        # Do not run if no species or already exists
        if not self.species_key or self.orthologs:
            return self

        # Only collect orthologs if it's the right entity type
        self.add_entity_types()
        if not list(set(self.entity_types) & set(["Gene", "RNA", "Micro_RNA", "Protein", "all"])):
            return self

        orthologs = bel.terms.orthologs.get_orthologs(self.canonical.key)

        for ortholog_species_key in orthologs:

            ortholog_key = orthologs[ortholog_species_key]
            normalized = bel.terms.terms.get_normalized_terms(ortholog_key)

            ortholog_dict = {}

            if normalized["canonical"]:
                ortholog_dict["canonical"] = NsVal(key_label=normalized["canonical"])
            if normalized["decanonical"]:
                ortholog_dict["decanonical"] = NsVal(key_label=normalized["decanonical"])

            self.orthologs[ortholog_species_key] = copy.copy(ortholog_dict)

        return self

    def orthologize(self, species_key: Key):
        """Orthologize BEL entity - results in canonical form"""

        self.add_entity_types()
        self.normalize()
        self.add_species()

        # Do not run if no species or already exists
        if not self.species_key:
            return self

        # Only collect orthologs if it's the right entity type
        self.add_entity_types()
        if not list(set(self.entity_types) & set(["Gene", "RNA", "Micro_RNA", "Protein", "all"])):
            return self

        if not self.orthologs:
            self.collect_orthologs(species_keys=[species_key])

        if species_key not in self.orthologs:
            self.orthologized = False
            self.nsval = self.canonical
            return self

        self.orthologized = True
        self.orthologized_species_key = species_key
        self.nsval = self.orthologs[species_key]["canonical"]

        return self

    def orthologizable(self, species_key: Key) -> bool:
        """Is this BEL Entity/NSArg orthologizable?"""

        self.add_entity_types()
        self.normalize()
        self.add_species()

        # Only collect orthologs if it's the right entity type
        if not list(set(self.entity_types) & set(["Gene", "RNA", "Micro_RNA", "Protein", "all"])):
            return None

        # Do not run if no species or already exists
        if not self.species_key:
            return False

        if not self.orthologs:
            self.collect_orthologs()

        if species_key not in self.orthologs:
            return False

        return True

    def all(self):
        """Fully flesh out BEL Entity"""

        self.add_species()
        self.add_entity_types()
        self.normalize()
        self.collect_orthologs()

        return self

    def __str__(self):

        return str(self.nsval)

    __repr__ = __str__
