#!/usr/bin/env python
# -*- coding: utf-8 -*-


# Standard Library
import copy
import json
import re
import sys
import traceback
from typing import Any, List, Mapping, Optional, Tuple, Union

# Third Party
# Third Party Imports
import yaml
from loguru import logger
from pydantic import BaseModel, Field

# Local
# Local Imports
import bel.core.settings as settings
import bel.db.arangodb
import bel.terms.orthologs
import bel.terms.terms
from bel.belspec.crud import get_enhanced_belspec
from bel.core.utils import html_wrap_span, http_client, url_path_param_quoting
from bel.schemas.bel import (
    AssertionStr,
    BelEntity,
    FunctionSpan,
    Key,
    NsArgSpan,
    NsVal,
    Pair,
    Span,
    ValidationError,
)
from bel.schemas.constants import strarg_validation_lists


#########################
# Unknown string        #
#########################
class String(object):
    """Used for unknown strings"""

    def __init__(self, value: str, span: Span = None):

        self.value = value
        self.span = span
        self.type: str = "String"
        self.parent = None

    def update(self, value):
        self.value = value
        self.span = None

    def __str__(self):
        return self.value

    __repr__ = __str__

    def to_string(self, fmt: str = "medium") -> str:

        return str(self)


###################
# Relation object #
###################
class Relation(object):
    def __init__(self, name, version: str = "latest", span: Span = None):

        self.version = version
        self.belspec = get_enhanced_belspec(self.version)

        self.name = self.belspec["relations"]["to_long"].get(name, name)
        self.name_short = self.belspec["relations"]["to_short"].get(name, name)

        self.span = span

        self.type = "Relation"

    def to_string(self, fmt: str = "medium"):
        if fmt == "short":
            return self.name_short
        else:
            return self.name

    def __str__(self):
        return self.name

    __repr__ = __str__


###################
# Function object #
###################
class Function(object):
    def __init__(self, name, version: str = "latest", parent=None, span: FunctionSpan = None):

        self.version = version
        self.belspec = get_enhanced_belspec(self.version)
        self.name = self.belspec["functions"]["to_long"].get(name, name)
        self.function_signature = self.belspec["functions"]["signatures"][self.name]
        self.name_short = self.belspec["functions"]["to_short"].get(name, name)
        if self.name in self.belspec["functions"]["info"]:
            self.function_type = self.belspec["functions"]["info"][self.name]["type"]
        else:
            self.function_type = ""

        self.type = "Function"

        self.parent = parent

        self.span = span

        self.sort_tuple: Tuple = ()

        self.position_dependent = False
        self.args = []
        self.siblings = []

    def update(self, name: str):
        """Update function"""

        self.name = self.belspec["functions"]["to_long"].get(name, name)
        self.name_short = self.belspec["functions"]["to_short"].get(name, name)
        self.function_signature = self.belspec["functions"]["signatures"][self.name]
        self.span = None
        if self.name in self.belspec["functions"]["info"]:
            self.function_type = self.belspec["functions"]["info"][self.name]["type"]
        else:
            self.function_type = ""

    def is_primary(self):
        if self.function_type == "Primary":
            return True
        return False

    def is_modifier(self):
        if self.function_type == "Modifier":
            return True
        return False

    def add_argument(self, arg):
        self.args.append(arg)

    def add_sibling(self, sibling):
        self.siblings.append(sibling)

    def change_parent(self, parent):
        self.parent = parent

    def change_function_type(self, function_type):
        self.function_type = function_type

    def canonicalize(
        self,
        canonical_targets: Mapping[str, List[str]] = settings.BEL_CANONICALIZE,
        decanonical_targets: Mapping[str, List[str]] = settings.BEL_DECANONICALIZE,
    ):
        if isinstance(self, NSArg):
            self.canonicalize(
                canonical_targets=canonical_targets, decanonical_targets=decanonical_targets
            )

        elif hasattr(self, "args"):
            for arg in self.args:
                if isinstance(self, (NSArg, Function)):
                    arg.canonicalize(
                        canonical_targets=canonical_targets, decanonical_targets=decanonical_targets
                    )

        sort_function_args(self)

        return self

    def decanonicalize(
        self,
        canonical_targets: Mapping[str, List[str]] = settings.BEL_CANONICALIZE,
        decanonical_targets: Mapping[str, List[str]] = settings.BEL_DECANONICALIZE,
    ):
        if isinstance(self, NSArg):
            self.decanonicalize(
                canonical_targets=canonical_targets, decanonical_targets=decanonical_targets
            )

        elif hasattr(self, "args"):
            for arg in self.args:
                if isinstance(self, (NSArg, Function)):
                    arg.decanonicalize(
                        canonical_targets=canonical_targets, decanonical_targets=decanonical_targets
                    )

        return self

    def orthologize(self, species_key):
        """Orthologize Assertion

        Check if fully orthologizable() before orthologizing, otherwise
        you may get a partially orthologized Assertion
        """

        if isinstance(self, NSArg):
            self.orthologize(species_key)

        if hasattr(self, "args"):
            for arg in self.args:
                arg.orthologize(species_key)

        return self

    def orthologizable(self, species_key: Key) -> Optional[bool]:
        """Is this Assertion fully orthologizable?

        Is it possible to orthologize every gene/protein/RNA NSArg to the target species?
        """

        true_response = None  # Are any of the NSArgs orthologizable?
        if hasattr(self, "args"):
            for arg in self.args:
                if arg and arg.type in ["NSArg", "Function"]:
                    response = arg.orthologizable(species_key)
                    if response is False:
                        return False
                    elif response is True:
                        true_response = True

        return true_response

    def get_species_keys(self, species_keys: List[str] = None):
        """Collect species associated with NSArgs

        Can have multiple species related to single Assertion
        """

        if species_keys is None:
            species_keys = []

        if hasattr(self, "args"):
            for arg in self.args:
                if arg and arg.type in ["NSArg", "Function"]:
                    species_keys = arg.get_species_keys(species_keys)

        return species_keys

    def get_orthologs(
        self, orthologs: List[dict] = None, orthologize_targets_keys: List[Key] = None
    ):
        """Collect orthologs associated with NSArgs"""

        if orthologs is None:
            orthologs = []

        if hasattr(self, "args"):
            for arg in self.args:
                if arg and arg.type in ["NSArg", "Function"]:
                    orthologs = arg.get_orthologs(orthologs, orthologize_targets_keys)

        return orthologs

    def validate(self, errors: List[ValidationError] = None):
        """Validate BEL Function"""

        if errors is None:
            errors = []

        # Collect term info for NSArgs before validation
        if hasattr(self, "args"):
            for arg in self.args:
                if arg and arg.type == "NSArg":
                    arg.entity.add_term()

        # Validate function (or top-level args)
        try:
            errors.extend(validate_function(self))
        except Exception as e:
            logger.error(f"Could not validate function {self.to_string()} -- error: {str(e)}")
            errors.append(
                ValidationError(
                    type="Assertion",
                    severity="Error",
                    msg=f"Could not validate function {self.to_string()} - unknown error",
                )
            )

        # Recursively validate args that are functions
        if hasattr(self, "args"):
            for arg in self.args:
                if arg and arg.type == "Function":
                    arg.validate(errors=errors)

        return errors

    def to_string(
        self,
        fmt: str = "medium",
        canonicalize: bool = False,
        decanonicalize: bool = False,
        orthologize: str = None,
    ) -> str:
        """Convert AST object to string

        Args:
            fmt (str): short, medium, long formatted BEL statements
                short = short function and short relation format
                medium = short function and long relation format
                long = long function and long relation format

        Returns:
            str: string version of BEL AST
        """

        arg_string = ", ".join([a.to_string(fmt=fmt) for a in self.args])

        if fmt in ["short", "medium"]:
            function_name = self.name_short
        else:
            function_name = self.name

        return "{}({})".format(function_name, arg_string)

    def __str__(self):
        arg_string = ", ".join([a.to_string() for a in self.args])
        return "{}({})".format(self.name, arg_string)

    __repr__ = __str__

    def print_tree(self, indent=0):

        for arg in self.args:
            if arg.type == "Function":
                spacer = "\t" * indent
                print(f"{spacer}Function: {str(arg)}")
                arg.print_tree(indent + 1)
            else:
                print("\t" * (indent + 1) + arg.print_tree())

    def subcomponents(self, subcomponents):
        """Generate subcomponents of the BEL subject or object

        Args:
            AST
            subcomponents:  Pass an empty list to start a new subcomponents request

        Returns:
            List[str]: subcomponents of BEL subject or object
        """

        for arg in self.args:
            if arg.__class__.__name__ == "Function":
                subcomponents.append(arg.to_string())
                if arg.function_type == "primary":
                    arg.subcomponents(subcomponents)
            else:
                subcomponents.append(arg.to_string())

        return subcomponents


#####################
# Argument objects #
#####################
class Arg(object):
    def __init__(self, parent=None, span: Span = None):

        self.optional = False
        self.type = "Arg"

        self.parent = parent
        self.siblings = []

        # https://github.com/belbio/bel/issues/13

        # used for sorting arguments (position, modifier, modifier-specific sort parameter)
        #    position = position specific arguments
        # p(HGNC:AKT1, loc(X), pmod(Ph, 3), pmod(Ph, 4))
        # Arg: HGNC:AKT1 -> (1)
        # Arg: loc() -> (2, loc, "X")
        # Arg: pmod(Ph, 2) -> (2, pmod, 3)
        # Args are sorted via
        self.sort_tuple: Tuple = ()

        self.span: Span = span

    def add_sibling(self, sibling):

        self.siblings.append(sibling)

    def canonicalize(
        self,
        canonical_targets: Mapping[str, List[str]] = settings.BEL_CANONICALIZE,
        decanonical_targets: Mapping[str, List[str]] = settings.BEL_DECANONICALIZE,
    ):
        return self

    def decanonicalize(
        self,
        canonical_targets: Mapping[str, List[str]] = settings.BEL_CANONICALIZE,
        decanonical_targets: Mapping[str, List[str]] = settings.BEL_DECANONICALIZE,
    ):
        return self

    def orthologize(self, species_key: Key):
        return self


class NSArg(Arg):
    """Parsed NSArg value"""

    def __init__(self, entity: BelEntity, parent=None, span: NsArgSpan = None):
        Arg.__init__(self, parent, span)

        self.entity = entity

        self.type = "NSArg"

    def canonicalize(
        self,
        canonical_targets: Mapping[str, List[str]] = settings.BEL_CANONICALIZE,
        decanonical_targets: Mapping[str, List[str]] = settings.BEL_DECANONICALIZE,
    ):
        self.entity.canonicalize(
            canonical_targets=settings.BEL_CANONICALIZE,
            decanonical_targets=settings.BEL_DECANONICALIZE,
        )

    def decanonicalize(
        self,
        canonical_targets: Mapping[str, List[str]] = settings.BEL_CANONICALIZE,
        decanonical_targets: Mapping[str, List[str]] = settings.BEL_DECANONICALIZE,
    ):
        self.entity.decanonicalize(
            canonical_targets=settings.BEL_CANONICALIZE,
            decanonical_targets=settings.BEL_DECANONICALIZE,
        )

    def orthologize(self, species_key: Key):
        """Orthologize the BEL Entity"""

        self.entity.orthologize(species_key)

    def orthologizable(self, species_key: Key):
        """Is this function arg fully orthologizable? - every gene/protein/RNA NSArg can be orthologized?"""

        return self.entity.orthologizable(species_key)

    def get_species_keys(self, species_keys: List[str]):
        """Get species from NSArg"""

        if self.entity.species_key is not None:
            species_keys.append(self.entity.species_key)

        return species_keys

    def get_orthologs(self, orthologs: List[dict], orthologize_targets_keys: List[Key] = None):
        """Get orthologs from NSArg"""

        if orthologize_targets_keys is None:
            orthologize_targets_keys = settings.BEL_ORTHOLOGIZE_TARGETS

        if self.entity.species_key and not self.entity.orthologs:
            self.entity.collect_orthologs(species_keys=orthologize_targets_keys)

        if self.entity.orthologs:
            orthologs.append(self.entity.orthologs)

        return orthologs

    def update(self, entity: BelEntity):
        """Update to new BEL Entity"""

        self.entity = entity
        self.span = None

    def to_string(self, fmt: str = "medium") -> str:

        return str(self.entity)

    def print_tree(self, fmt: str = "medium") -> str:

        return f"NSArg: {str(self.entity)} canonical: {self.canonical} decanonical: {self.decanonical} orthologs: {self.orthologs} orig_species: {self.orthology_species}"

    def __str__(self):
        return str(self.entity)

    __repr__ = __str__


class StrArg(Arg):
    def __init__(self, value, span: Span = None, parent=None):
        Arg.__init__(self, parent, span)
        self.value = value
        self.type = "StrArg"

    def update(self, value: str):
        """Update to new BEL Entity"""

        self.value = value
        self.span = None

    def to_string(self, fmt: str = "medium") -> str:
        """Convert AST object to string

        Args:
            fmt (str): short, medium, long formatted BEL statements
                short = short function and short relation format
                medium = short function and long relation format
                long = long function and long relation format

        Returns:
            str: string version of BEL AST
        """
        return "{}".format(self.value)

    def print_tree(self, fmt: str = "medium") -> str:
        return "StrArg: {}".format(self.value)

    def __str__(self):
        return "StrArg: {}".format(self.value)

    __repr__ = __str__


class ParseInfo:
    """BEL Assertion Parse Information

    Matching quotes need to be gathered first
    """

    def __init__(self, assertion: AssertionStr = None, version: str = "latest"):

        self.assertion = assertion
        self.version = version

        self.matched_quotes: List[Pair] = []
        self.matched_parens: List[Pair] = []
        self.commas: List[int] = []
        self.relations: List[Span] = []
        self.functions: List[FunctionSpan] = []
        self.nsargs: List[NsArgSpan]

        self.errors: List[ValidationError] = []

        if self.assertion:
            self.get_parse_info(assertion=self.assertion)

    def get_parse_info(self, assertion: str = "", version: str = "latest"):
        # Local
        from bel.lang.parse import parse_info

        if assertion:
            self.assertion = assertion

        # Pass just the entire assertion string to parse_info
        result = parse_info(self.assertion.entire, version=self.version)

        self.matched_quotes = result["matched_quotes"]
        self.matched_parens = result["matched_parens"]
        self.commas = result["commas"]
        self.components = result["components"]
        self.errors = result["errors"]

    def __str__(self):

        components_str = ""
        for c in self.components:
            components_str += f"{str(c)}\n"

        return f"""ParseInfo(
            assertion: {self.assertion},
            matched_quotes: {self.matched_quotes},
            matched_parens: {self.matched_parens},
            commas: {self.commas},
            components: {components_str},
            version: {self.version},
            errors: {self.errors},
        )
        """

    __repr__ = __str__


########################
# BEL statement AST #
########################
class BELAst(object):
    def __init__(
        self,
        assertion: AssertionStr = None,
        subject: Optional[Function] = None,
        relation: Optional[Relation] = None,
        object: Optional[Union[Function, "BELAst"]] = None,
        is_computed: bool = False,
        version: str = "latest",
    ):
        self.version = bel.belspec.crud.check_version(version)
        self.assertion = assertion

        self.subject, self.relation, self.object = subject, relation, object
        self.args = []

        if subject is not None:
            self.args = [subject, relation, object]

        if isinstance(self.relation, str):
            self.relation = Relation(self.relation, version=self.version)

        self.belspec = get_enhanced_belspec(version)

        self.type = "BELAst"

        # Computed edges are special in that we should only have one in the edgestore no matter the source
        self.is_computed = is_computed

        self.errors: List[ValidationError] = []

        if self.subject or self.relation or self.object:
            if self.relation and not self.object:
                msg = "Missing Assertion Object"
                self.errors.append(ValidationError(type="Assertion", severity="Error", msg=msg))
            elif self.object and (not self.subject or not self.relation):
                msg = "Missing Assertion Subject or Relation"
                self.errors.append(ValidationError(type="Assertion", severity="Error", msg=msg))

        elif assertion and assertion.subject or assertion.relation or assertion.object:
            if assertion.relation and not assertion.object:
                msg = "Missing Assertion Object"
                self.errors.append(ValidationError(type="Assertion", severity="Error", msg=msg))
            elif assertion.object and (not assertion.subject or not assertion.relation):
                msg = "Missing Assertion Subject or Relation"
                self.errors.append(ValidationError(type="Assertion", severity="Error", msg=msg))

        if not self.errors and self.assertion is not None and not self.args:
            self.parse()  # parse assertion into BEL AST

    def parse(self):
        """Assemble parsed component from Assertion string into AST"""

        self.parse_info = ParseInfo(self.assertion)

        self.errors.extend(self.parse_info.errors)

        function_stack = []

        parent_fn = None

        for span in self.parse_info.components:

            if span.type == "end_paren":
                if len(function_stack) > 0:
                    function_stack.pop()  # Pop parent_fn off stack

                    # Reset parent_fn
                    if len(function_stack) > 0:
                        parent_fn = function_stack[-1]
                    else:
                        parent_fn = None

            elif span.type == "start_paren":
                continue

            elif span.type == "relation":

                # Reset function_stack
                parent_fn = None
                function_stack = []

                relation = Relation(span.span_str, self.version, span=span)
                self.args.append(relation)

            elif span.type == "function":

                fn = Function(span.name.span_str, self.version, span=span)

                if parent_fn:
                    fn.parent = parent_fn
                    parent_fn.args.append(fn)
                else:
                    self.args.append(fn)

                function_stack.append(fn)  # add to function stack
                parent_fn = fn

            elif span.type == "ns_arg":

                if span.label:
                    nsval = NsVal(
                        namespace=span.namespace.span_str,
                        id=span.id.span_str,
                        label=span.label.span_str,
                    )
                else:
                    nsval = NsVal(namespace=span.namespace.span_str, id=span.id.span_str)

                entity = BelEntity(nsval=nsval)

                ns_arg = NSArg(entity, span=span)

                # Add parent Function
                if parent_fn:
                    ns_arg.parent = parent_fn
                    parent_fn.args.append(ns_arg)
                else:
                    ns_arg.parent = self
                    self.args.append(ns_arg)

            elif span.type == "string_arg":

                str_arg = StrArg(span.span_str, parent=parent_fn, span=span)
                if parent_fn:
                    str_arg.parent = parent_fn
                    parent_fn.args.append(str_arg)
                else:
                    str_arg.parent = self
                    self.args.append(str_arg)

            elif span.type == "string":
                string = String(span.span_str, span=span)

                if parent_fn:
                    string.parent = parent_fn
                    parent_fn.args.append(string)
                else:
                    string.parent = None
                    self.args.append(string)

            else:
                logger.error(f"Unknown span type {span}")

        # Subject only assertion
        if len(self.args) == 1 and self.args[0].type == "Function":
            self.subject = self.args[0]
        # Normal SRO BEL assertion
        elif (
            len(self.args) == 3
            and self.args[0].type == "Function"
            and self.args[1].type == "Relation"
            and self.args[2].type == "Function"
        ):
            self.subject = self.args[0]
            self.relation = self.args[1]
            self.object = self.args[2]
        # Nested BEL Assertion
        elif (
            len(self.args) == 5
            and self.args[0].type == "Function"
            and self.args[1].type == "Relation"
            and self.args[2].type == "Function"
            and self.args[3].type == "Relation"
            and self.args[4].type == "Function"
        ):
            self.subject = self.args[0]
            self.relation = self.args[1]
            self.object = BELAst(subject=self.args[2], relation=self.args[3], object=self.args[4])
        elif len(self.args) > 1 and self.args[1].type != "Relation":
            self.errors.append(
                ValidationError(
                    type="Assertion",
                    severity="Error",
                    msg=f"Could not parse Assertion - bad relation: {self.args[1]}",
                )
            )
        else:
            self.errors.append(
                ValidationError(
                    type="Assertion",
                    severity="Error",
                    msg=f"Could not parse Assertion - wrong number {len(self.args)} of components or type of assertion components is wrong {[arg.type for arg in self.args]}",
                )
            )

        return self

    def canonicalize(
        self,
        canonical_targets: Mapping[str, List[str]] = settings.BEL_CANONICALIZE,
        decanonical_targets: Mapping[str, List[str]] = settings.BEL_DECANONICALIZE,
    ):
        """Canonicalize BEL Assertion

        Must set both targets if not using defaults as the underlying normalization handles
        both canonical and decanonical forms in the same query
        """

        # Process AST top-level args or Function args
        if hasattr(self, "args"):
            for arg in self.args:
                if arg and arg.type in ["NSArg", "Function"]:
                    arg.canonicalize(
                        canonical_targets=settings.BEL_CANONICALIZE,
                        decanonical_targets=settings.BEL_DECANONICALIZE,
                    )

        elif self and self.type == "NSArg":
            self.canonicalize(
                canonical_targets=settings.BEL_CANONICALIZE,
                decanonical_targets=settings.BEL_DECANONICALIZE,
            )

        return self

    def decanonicalize(
        self,
        canonical_targets: Mapping[str, List[str]] = settings.BEL_CANONICALIZE,
        decanonical_targets: Mapping[str, List[str]] = settings.BEL_DECANONICALIZE,
    ):
        """Decanonicalize BEL Assertion

        Must set both targets if not using defaults as the underlying normalization handles
        both canonical and decanonical forms in the same query
        """

        # Process AST top-level args or Function args
        if hasattr(self, "args"):
            for arg in self.args:
                if arg and arg.type in ["NSArg", "Function"]:
                    arg.decanonicalize(
                        canonical_targets=settings.BEL_CANONICALIZE,
                        decanonical_targets=settings.BEL_DECANONICALIZE,
                    )

        elif self and self.type == "NSArg":
            self.decanonicalize(
                canonical_targets=settings.BEL_CANONICALIZE,
                decanonical_targets=settings.BEL_DECANONICALIZE,
            )

        return self

    def orthologize(self, species_key: Key):
        """Orthologize any orthologizable element

        Run orthologizable() method first to confirm that entire Assertion is
        orthologizable.
        """
        if hasattr(self, "args"):
            for arg in self.args:
                if arg and arg.type in ["NSArg", "Function"]:
                    arg.orthologize(species_key)

        return self

    def orthologizable(self, species_key: Key):
        """Is this Assertion fully orthologizable?

        This method will detect if the orthologization will result
        in a partially orthologized Assertion.
        """

        true_response = None
        if hasattr(self, "args"):
            for arg in self.args:
                if arg and arg.type in ["NSArg", "Function"]:
                    response = arg.orthologizable(species_key)
                    if response is False:
                        return False
                    elif response is True:
                        true_response = True

        return true_response

    def get_orthologs(
        self,
        orthologs: List[dict] = None,
        orthologize_targets_keys: List[Key] = None,
    ):
        """Collect orthologs associated with NSArgs

        simple_keys: provide canonical and decanonical values as keys (not key_labels) instead of NsVal objects
        """

        if orthologs is None:
            orthologs = []

        if hasattr(self, "args"):
            for arg in self.args:
                if arg and arg.type in ["NSArg", "Function"]:
                    orthologs = arg.get_orthologs(orthologs, orthologize_targets_keys)

        return orthologs

    def get_species_keys(self, species_keys: List[str] = None):
        """Collect species associated with NSArgs

        Can have multiple species related to single Assertion
        """

        if species_keys is None:
            species_keys = []

        if hasattr(self, "args"):
            for arg in self.args:
                if arg and arg.type in ["NSArg", "Function"]:
                    species_keys = arg.get_species_keys(species_keys)

        return list(set(species_keys))

    def validate(self):
        """Validate BEL Assertion"""

        # Process AST top-level args or Function args
        if hasattr(self, "args"):
            for arg in self.args:
                if arg and arg.type in ["Function"]:
                    self.errors.extend(arg.validate(errors=[]))

    def to_string(self, fmt: str = "medium") -> str:
        """Convert AST object to string

        Args:
            fmt (str): short, medium, long formatted BEL statements
                short = short function and short relation format
                medium = short function and long relation format
                long = long function and long relation format
            canonicalize

        Returns:
            str: string version of BEL AST
        """

        # TODO - add handling for nested BEL Assertions

        if self.subject and self.relation and self.object:
            if isinstance(self.object, BELAst):
                return "{} {} ({})".format(
                    self.subject.to_string(fmt=fmt),
                    self.relation.to_string(fmt=fmt),
                    self.object.to_string(fmt=fmt),
                )
            else:
                return "{} {} {}".format(
                    self.subject.to_string(fmt=fmt),
                    self.relation.to_string(fmt=fmt),
                    self.object.to_string(fmt=fmt),
                )

        elif self.subject:
            return "{}".format(self.subject.to_string(fmt=fmt))

        else:
            return ""

    def to_triple(self, fmt: str = "medium"):
        """Convert AST object to BEL triple

        Args:
            fmt (str): short, medium, long formatted BEL statements
                short = short function and short relation format
                medium = short function and long relation format
                long = long function and long relation format

        Returns:
            dict: {'subject': <subject>, 'relation': <relations>, 'object': <object>}
        """

        # TODO - add handling for nested BEL Assertions

        if self.subject and self.relation and self.object:

            subject = self.subject.to_string(fmt=fmt)
            relation = self.relation.to_string(fmt=fmt)
            object_ = self.object.to_string(fmt=fmt)

            return {"subject": subject, "relation": relation, "object": object_}

        elif self.subject:
            return {"subject": self.subject.to_string(fmt=fmt)}

        else:
            return None

    def __str__(self):
        return self.to_string()

    __repr__ = __str__

    def to_dict(self):
        """Convert to dict"""

        return {
            "assertion": self.assertion,
            # "subject": self.subject.to_string(),
            # "relation": self.relation.to_string(),
            # "object": self.object.to_string(),
            "type": self.type,
            "args": [str(arg) for arg in self.args],
            "version": self.version,
            "parse_info": str(self.parse_info),
        }

    def print_tree(self):
        """Convert BEL AST args to tree view of BEL AST

        Returns:
            prints tree of BEL AST to STDOUT
        """

        for arg in self.args:
            if arg.type == "Function":
                print("Function: ", arg)
                arg.print_tree(indent=1)

            elif arg.type == "Relation":
                print("Relation: ", arg)

            else:
                print(arg)

        return self


#########################################################################################################
# Helper functions ######################################################################################
#########################################################################################################


def match_signatures(args, signatures):
    """Which signature to use"""

    for signature in signatures:
        if (
            args[0].type == "Function"
            and args[0].function_type == signature["arguments"][0]["type"]
        ):
            return signature
        elif args[0].type == signature["arguments"][0]["type"]:
            return signature


def intersect(list1, list2) -> bool:
    """Do list1 and list2 intersect"""

    if len(set(list1).intersection(set(list2))) == 0:
        return False

    return True


def check_str_arg(value: str, check_values: List[str]) -> Optional[str]:
    """Check StrArg value"""

    regex_flag = False
    for check_value in check_values:
        if re.match("/", check_value):
            # TODO - figure out how to make this work
            # regex_flag = True
            # print("Check value", check_value)
            # match = re.match(r""+check_value, value)
            # if match:
            #     break
            regex_flag = True
            break

        elif (
            check_value in strarg_validation_lists and value in strarg_validation_lists[check_value]
        ):
            break

    else:
        if regex_flag:
            return f"String Argument {value} doesn't match required format: {repr(check_values)}"
        else:
            return f"String Argument {value} not found in {check_values} default BEL namespaces"

    return None


def validate_function(fn: Function, errors: List[ValidationError] = None) -> List[ValidationError]:
    """Validate function"""

    # logger.debug(f"Validating function name {fn.name}, len: {len(fn.args)}")

    if errors is None:
        errors = []

    # Check for completely missing arguments
    if len(fn.args) == 0:
        errors.append(
            ValidationError(
                type="Assertion",
                severity="Error",
                msg=f"No arguments in function: {fn.name}",
                visual_pairs=[(fn.span.start, fn.span.end)],
                index=fn.span.start,
            )
        )
        return errors

    signatures = fn.function_signature["signatures"]

    # Select signature from signatures
    if len(signatures) > 1:
        signature = match_signatures(fn.args, signatures)
    else:
        signature = signatures[0]

    if not signature:
        errors.append(
            ValidationError(
                type="Assertion",
                severity="Error",
                msg=f"Could not match function: {fn.name} arguments to BEL Specification",
                visual_pairs=[(fn.span.start, fn.span.end)],
                index=fn.span.start,
            )
        )
        return errors

    # 1 past the last positional element (including optional elements if they exist)
    post_positional = 0

    # First pass - check required positional arguments
    fn_max_args = len(fn.args) - 1
    for argument in signature["arguments"]:
        if argument["position"] is not None and argument["optional"] == False:
            position = argument["position"]

            # Arg type mis-match
            if position > fn_max_args:
                errors.append(
                    ValidationError(
                        type="Assertion",
                        severity="Error",
                        msg=f"Missing required argument - type: {argument['type']}",
                        visual_pairs=[(fn.span.start, fn.span.end)],
                        index=fn.span.start,
                    )
                )

            # elif (
            #     fn.args[position]
            #     and fn.args[position].type == "Function"
            #     and fn.args[position].function_type not in argument["type"]
            # ):
            #     errors.append(
            #         ValidationError(
            #             type="Assertion",
            #             severity="Error",
            #             msg=f"Incorrect function type '{fn.args[position].type}' at position: {position} for function: {fn.name}, should be one of {argument['type']}",
            #             visual_pairs=[(fn.args[position].span.start, fn.args[position].span.end)],
            #             index=fn.args[position].span.start,
            #         )
            #     )

            # Function name mis-match
            elif (
                fn.args[position]
                and fn.args[position].type == "Function"
                and not (fn.args[position].name in argument["values"])
            ):
                errors.append(
                    ValidationError(
                        type="Assertion",
                        severity="Error",
                        msg=f"Incorrect function for argument '{fn.args[position].name}' at position: {position} for function: {fn.name}",
                        visual_pairs=[(fn.args[position].span.start, fn.args[position].span.end)],
                        index=fn.args[position].span.start,
                    )
                )

            # Wrong [non-function] argument type
            elif (
                fn.args[position]
                and fn.args[position].type != "Function"
                and fn.args[position].type not in argument["type"]
            ):
                errors.append(
                    ValidationError(
                        type="Assertion",
                        severity="Error",
                        msg=f"Incorrect argument type '{fn.args[position].type}' at position: {position} for function: {fn.name}, should be one of {argument['type']}",
                        visual_pairs=[(fn.args[position].span.start, fn.args[position].span.end)],
                        index=fn.args[position].span.start,
                    )
                )

            post_positional = position + 1

    # Checking optional positional arguments - really just adjusting post_positional value
    for argument in signature["arguments"]:
        if argument["position"] is not None and argument["optional"] == True:
            position = argument["position"]

            if position > fn_max_args:
                break

            if argument["type"] == ["StrArgNSArg"]:
                argument["type"].extend(["NSArg", "StrArg"])

            if (  # Function match
                fn.args[position].type == "Function"
                and fn.args[position].name in argument["values"]
            ) or (  # NSArg/StrArg type match
                fn.args[position].type in ["NSArg", "StrArg"]
                and fn.args[position].type in argument["type"]
            ):
                post_positional = position + 1

    # Second pass optional, single arguments (e.g. loc(), ma())
    opt_args = signature["opt_args"]
    check_opt_args = {}
    problem_opt_args = set()
    for fn_arg in fn.args[post_positional:]:
        if fn_arg.type == "Function" and fn_arg.name in opt_args:
            if fn_arg.name in check_opt_args:
                problem_opt_args.add(fn_arg.name)
            else:
                check_opt_args[fn_arg.name] = 1

    problem_opt_args = list(problem_opt_args)
    if len(problem_opt_args) > 0:
        errors.append(
            ValidationError(
                type="Assertion",
                severity="Error",
                msg=f"Can only have at most one {problem_opt_args} in function arguments",
                visual_pairs=[(fn.span.start, fn.span.end)],
                index=fn.span.start,
            )
        )

    # Third pass - non-positional (primary/modifier) args that don't show up in opt_args or mult_args
    opt_and_mult_args = opt_args + signature["mult_args"]
    for fn_arg in fn.args[post_positional:]:
        if fn_arg.type == "Function" and fn_arg.name not in opt_and_mult_args:
            errors.append(
                ValidationError(
                    type="Assertion",
                    severity="Error",
                    msg=f"Function {fn_arg.name} is not allowed as an optional or multiple argument",
                    visual_pairs=[(fn.span.start, fn.span.end)],
                    index=fn.span.start,
                )
            )

        # This handles complex(NSArg, p(X)) validation and virtual namespaces
        elif (
            fn_arg.type == "NSArg"
            and fn_arg.entity.entity_types
            and not intersect(fn_arg.entity.entity_types, opt_and_mult_args)
        ):
            errors.append(
                ValidationError(
                    type="Assertion",
                    severity="Error",
                    msg=f"BEL Entity: {fn_arg.entity.nsval} with entity_types {fn_arg.entity.entity_types} are not allowed for function {fn_arg.parent.name} as an optional or multiple argument",
                    visual_pairs=[(fn.span.start, fn.span.end)],
                    index=fn.span.start,
                )
            )

        elif fn_arg.type == "NSArg" and (
            fn_arg.entity.entity_types is None or fn_arg.entity.entity_types == []
        ):
            errors.append(
                ValidationError(
                    type="Assertion",
                    severity="Warning",
                    msg=f"Unknown BEL Entity {fn_arg.entity.nsval.key_label} - cannot determine if this matches function signature",
                    visual_pairs=[(fn.span.start, fn.span.end)],
                    index=fn.span.start,
                )
            )

    # Fourth pass - positional NSArg entity_types checks
    for argument in signature["arguments"]:
        if argument["position"] is not None:
            position = argument["position"]

            if position > fn_max_args:
                break

            if (
                fn.args[position].type == "NSArg"
                and argument["type"] in ["NSArg", "StrArgNSArg"]
                and not fn.args[position].entity.namespace_metadata
            ):
                errors.append(
                    ValidationError(
                        type="Assertion",
                        severity="Warning",
                        msg=f"Unknown BEL Entity '{fn.args[position].entity.nsval.key_label}' for the {fn.name} function at position {fn.args[position].span.namespace.start}",
                        visual_pairs=[
                            (
                                fn.args[position].span.namespace.start,
                                fn.args[position].span.namespace.end,
                            )
                        ],
                        index=fn.args[position].span.namespace.start,
                    )
                )

            elif (
                fn.args[position].type == "NSArg"
                and argument["type"] in ["NSArg", "StrArgNSArg"]
                and not (
                    intersect(
                        fn.args[position].entity.get_entity_types(), argument["values"] + ["All"]
                    )
                )
            ):

                if fn.args[position].entity.term:
                    error_msg = f"Wrong entity type for BEL Entity at argument position {position} for function {fn.name} - expected {argument['values']}, actual: entity_types: {fn.args[position].entity.entity_types}"
                else:
                    error_msg = f"Unknown BEL Entity at argument position {position} for function {fn.name} - cannot determine if correct entity type."

                errors.append(
                    ValidationError(
                        type="Assertion",
                        severity="Warning",
                        msg=error_msg,
                        visual_pairs=[(fn.args[position].span.start, fn.args[position].span.end)],
                        index=fn.args[position].span.start,
                    )
                )

    # Fifth pass - positional StrArg checks
    for argument in signature["arguments"]:
        if argument["position"] is not None:
            position = argument["position"]

            if position > fn_max_args:
                break

            if fn.args[position].type == "StrArg" and argument["type"] in ["StrArg", "StrArgNSArg"]:
                str_error = check_str_arg(fn.args[position].value, argument["values"])

                if str_error is not None:
                    errors.append(
                        ValidationError(
                            type="Assertion",
                            severity="Error",
                            msg=str_error,
                            visual_pairs=[
                                (fn.args[position].span.start, fn.args[position].span.end)
                            ],
                            index=fn.args[position].span.start,
                        )
                    )
    # Sixth pass - non-positional StrArgs are errors
    for idx, arg in enumerate(fn.args):
        if arg.type == "StrArg" and signature["arguments"][idx]["position"] is None:
            errors.append(
                ValidationError(
                    type="Assertion",
                    severity="Error",
                    msg="String argument not allowed as an optional or multiple argument. Probably missing a namespace.",
                    visual_pairs=[(arg.span.start, arg.span.end)],
                    index=arg.span.start,
                )
            )

    # Check for obsolete namespaces
    for arg in fn.args:
        if (
            arg.type == "NSArg"
            and arg.entity.term
            and arg.entity.original_nsval.key in arg.entity.term.obsolete_keys
        ):
            errors.append(
                ValidationError(
                    type="Assertion",
                    severity="Warning",
                    msg=f"BEL Entity name is obsolete - please update to {arg.entity.term.key}!{arg.entity.term.label}",
                    visual_pairs=[(arg.span.start, arg.span.end)],
                    index=fn.args[position].span.start,
                )
            )

    # Modifier function with wrong parent function
    if (
        fn.function_signature["func_type"] == "Modifier"
        and fn.parent
        and fn.parent.name not in fn.function_signature["primary_function"]
    ):
        errors.append(
            ValidationError(
                type="Assertion",
                severity="Error",
                msg=f"Missing parent for modifier function or wrong parent function for {fn.name}",
                visual_pairs=[(fn.span.start, fn.span.end)],
                index=fn.span.start,
            )
        )

    return errors


def sort_function_args(fn: Function):
    """Add sort tuple values to function arguments for canonicalization and sort function arguments"""

    signatures = fn.function_signature["signatures"]

    # Select signature from signatures
    if len(signatures) > 1:
        signature = match_signatures(fn.args, signatures)
    else:
        signature = signatures[0]

    fn_max_args = len(fn.args) - 1

    post_positional = 0
    for arg in signature["arguments"]:
        if arg["position"]:
            position = arg["position"]
            if position > fn_max_args:
                return None

            if arg["optional"] == False:
                fn.args[position].sort_tuple = (position,)
                post_positional = position + 1

            elif arg["optional"] == True:

                if arg["type"] == ["StrArgNSArg"]:
                    arg["type"].extend(["NSArg", "StrArg"])

                if (  # Function match
                    fn.args[position].type == "Function" and fn.args[position].name in arg["values"]
                ) or (  # NSArg/StrArg type match
                    fn.args[position].type in ["NSArg", "StrArg"]
                    and fn.args[position].type in arg["type"]
                ):
                    fn.args[position].sort_tuple = (position,)
                    post_positional = position + 1

    # non-positional elements
    primary_func_index = (
        post_positional + 1
    )  # Sort primary functions after non-function post-positional
    modifier_func_index = post_positional + 2  # Sort modifier functions after
    for fn_arg in fn.args[post_positional:]:
        if fn_arg.type == "StrArg":
            fn_arg.sort_tuple = (post_positional, "StrArg", fn_arg.value)

        elif fn_arg.type == "NSArg":
            fn_arg.sort_tuple = (post_positional, "NSArg", str(fn_arg.entity))

        # Sort by modifier function name, then position of modification and
        #     then by type of modification if available
        elif fn_arg.name == "proteinModification":
            pmod_args_len = len(fn_arg.args)

            if fn.args[0].type == "NSArg":
                modification_type_value = str(fn.args[0].entity)
            else:
                modification_type_value = fn_arg.args[0].value

            if pmod_args_len == 3:
                fn_arg.sort_tuple = (
                    modifier_func_index,
                    fn_arg.name,
                    fn_arg.args[2].value,
                    modification_type_value,
                )
            else:  # Add position of modification = -1
                fn_arg.sort_tuple = (
                    modifier_func_index,
                    fn_arg.name,
                    "-1",
                    modification_type_value,
                )

        elif fn_arg.name == "fragment":
            fn_arg.sort_tuple = (modifier_func_index, fn_arg.name, fn_arg.args[0])

        elif fn_arg.name == "variant":
            # TODO use https://github.com/biocommons/hgvs to sort by variant position
            fn_arg.sort_tuple = (modifier_func_index, fn_arg.name, str(fn_arg))

        elif fn_arg.function_type == "Modifier":
            fn_arg.sort_tuple = (modifier_func_index, fn_arg.name, str(fn_arg))

        elif fn_arg.type == "Function":
            fn_arg.sort_tuple = (primary_func_index, fn_arg.name, str(fn_arg))

        else:
            logger.error(f"Adding sort tuples - no sort_tuple added for {fn_arg}")

    fn.args = sorted(fn.args, key=lambda x: x.sort_tuple)
