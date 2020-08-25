# Third Party Imports
# Standard Library
import enum
from typing import Any, List, Mapping, Optional, Union

from pydantic import BaseModel, Field


# BEL Specification Schema ###########################################################
class FunctionTypes(str, enum.Enum):
    primary = "primary"
    modifier = "modifier"


class ArgumentTypes(str, enum.Enum):

    Function = "Function"
    NSArg = "NSArg"
    StrArg = "StrArg"
    Modifier = "Modifier"
    StrArgNSArg = "StrArgNSArg"


class RelationCategories(str, enum.Enum):

    causal = "causal"
    direct = "direct"
    membership = "membership"
    computed = "computed"
    genomic = "genomic"
    correlative = "correlative"
    equivalence = "equivalence"
    process = "process"
    deprecated = "deprecated"


class FunctionInfo(BaseModel):
    name: str
    type: FunctionTypes
    abbreviation: str
    categories: List[str]
    description: str
    primary_function: Optional[List[str]]


class FunctionSignatureArgument(BaseModel):
    type: ArgumentTypes
    position: Optional[int]
    values: List[str] = Field(
        ...,
        description="List of BEL functions, NSArg entity types or StrArg regex's that are allowed here",
    )
    optional: bool = False
    multiple: bool = False


class FunctionSignatureArguments(BaseModel):
    arguments: List[FunctionSignatureArgument]


class FunctionSignature(BaseModel):
    func_type: FunctionTypes
    name: str
    signatures: List[FunctionSignatureArguments]


class FunctionSpec(BaseModel):
    argument_types: Mapping[str, Any]
    entity_types: List[str]
    info: Mapping[str, FunctionInfo]
    signatures: Mapping[str, FunctionSignature]


class RelationInfo(BaseModel):
    name: str
    abbreviation: str
    categories: List[RelationCategories]


class RelationSpec(BaseModel):
    info: Mapping[str, RelationInfo]


class DefaultNamespaceValue(BaseModel):
    name: str
    abbreviation: str


class DefaultNamespace(BaseModel):
    info: List[DefaultNamespaceValue]


class BelSpec(BaseModel):

    version: str
    notes: Mapping[str, Any]
    functions: FunctionSpec
    relations: RelationSpec
    namespaces: Mapping[str, DefaultNamespace]

    class Config:
        extra = "allow"


# Enhanced BEL Specification Schema ###########################################################


class EnhancedFunctionSignatureArguments(BaseModel):
    arguments: List[FunctionSignatureArgument]
    req_args: List[List[str]]
    pos_args: List[List[str]]
    mult_args: List[List[str]]
    argument_summary: str
    argument_help_listing: List[str]


class EnhancedFunctionSignature(BaseModel):
    func_type: FunctionTypes
    name: str
    signatures: List[EnhancedFunctionSignatureArguments]


class EnhancedFunctionSpec(FunctionSpec):
    signatures: Mapping[str, EnhancedFunctionSignature]
    list: List[str] = Field(..., description="List of all function names")
    list_long: List[str] = Field(..., description="List of all long function names")
    list_short: List[str] = Field(..., description="List of all short function names")
    primary_list_long: List[str] = Field(..., description="List of all long primary function names")
    primary_list_short: List[str] = Field(
        ..., description="List of all short primary function names"
    )
    modifier_list_long: List[str] = Field(
        ..., description="List of all long modifier function names"
    )
    modifier_list_short: List[str] = Field(
        ..., description="List of all short modifier function names"
    )
    to_short: Mapping[str, str] = Field(
        ..., description="Mapping from short to long function names"
    )
    to_long: Mapping[str, str] = Field(..., description="Mapping from long to short function names")


class EnhancedRelationSpec(RelationSpec):
    list: List[str] = Field(..., description="List of all relation names")
    list_long: List[str] = Field(..., description="List of all long relation names")
    list_short: List[str] = Field(..., description="List of all short relation names")
    to_short: Mapping[str, str] = Field(
        ..., description="Mapping from short to long relation names"
    )
    to_long: Mapping[str, str] = Field(..., description="Mapping from long to short relation names")


class EnhancedDefaultNamespace(DefaultNamespace):
    list: List[str] = Field(..., description="List of all namespace names")
    list_long: List[str] = Field(..., description="List of all long namespace names")
    list_short: List[str] = Field(..., description="List of all abbreviated namespace names")
    to_short: Mapping[str, str] = Field(
        ..., description="Mapping from abbreviations to long namespace names"
    )
    to_long: Mapping[str, str] = Field(
        ..., description="Mapping from long to abbreviations relanamespacetion names"
    )


class EnhancedBelSpec(BelSpec):

    version: str
    notes: dict
    functions: EnhancedFunctionSpec
    relations: EnhancedRelationSpec
    namespaces: EnhancedDefaultNamespace


# Additional Schemas ###########################################################


class BelSpecVersions(BaseModel):
    latest: str
    default: str
    versions: List[str]
