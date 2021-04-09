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
import yaml
from loguru import logger
from pydantic import BaseModel, Field

# Local
import bel.core.settings as settings
import bel.db.arangodb
import bel.terms.orthologs
import bel.terms.terms
from bel.belspec.crud import check_version, get_enhanced_belspec
from bel.core.utils import (
    html_wrap_span,
    http_client,
    quote_string,
    url_path_param_quoting,
)
from bel.lang.ast_optimization import optimize_function
from bel.lang.ast_utils import args_to_string, sort_function_args
from bel.lang.ast_validation import validate_function
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

    def to_string(self, fmt: str = "medium", ignore_location: bool = False) -> str:

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

    def to_string(self, fmt: str = "medium", ignore_location: bool = False):
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

    def optimize(self):
        """Optimize Assertion

        Currently this only optimizes reactions if they match the following pattern
        """

        self = optimize_function(self)

        if self.type == "Function":
            for idx, arg in enumerate(self.args):
                if isinstance(arg, Function):
                    self.args[idx] = arg.optimize()

        return self

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

    def has_location(self) -> bool:
        """Does function have a location argument?"""

        for arg in self.args:
            if hasattr(arg, "name") and arg.name == "location":
                return True

        return False

    def get_location(self) -> Optional["Function"]:
        """Get location from function"""

        for arg in self.args:
            if hasattr(arg, "name") and arg.name == "location":
                return arg

        return None

    def add_location(self, loc_arg: Union[str, "Function"]) -> "Function":
        """Add location to function"""

        if self.name not in [
            "complexAbundance",
            "toLoc",
            "fromLoc",
            "abundance",
            "geneAbundance",
            "microRNAAbundance",
            "populationAbundance",
            "proteinAbundance",
            "rnaAbundance",
        ]:
            logger.warning(f"Cannot add location to {self.name}")
            return self

        if isinstance(loc_arg, str):
            loc_arg_str = loc_arg
            loc_arg = Function("location")
            loc_arg.args.append(loc_arg_str)
        elif not isinstance(loc_arg, Function):
            logger.warning(f"Location arg is not a string or Function {loc_arg}")
            return self

        for arg in self.args:
            if hasattr(arg, "name") and arg.name == "location":
                logger.info(
                    f"Function already has a location argument - only one is allowed: {self.to_string()}"
                )
                return self

        self.args.append(loc_arg)
        return self

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
            logger.exception(f"Could not validate function {self.to_string()} -- error: {str(e)}")
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

    def to_string(self, fmt: str = "medium", ignore_location: bool = False) -> str:
        """Convert AST object to string

        Args:
            fmt (str): short, medium, long formatted BEL statements
                short = short function and short relation format
                medium = short function and long relation format
                long = long function and long relation format

        Returns:
            str: string version of BEL AST
        """

        if ignore_location and self.name == "location":
            return ""

        args_string = args_to_string(self.args, fmt=fmt, ignore_location=ignore_location)

        if fmt in ["short", "medium"]:
            function_name = self.name_short
        else:
            function_name = self.name

        return "{}({})".format(function_name, args_string)

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

    def subcomponents(self, subcomponents=None):
        """Generate subcomponents of the BEL subject or object

        Args:
            AST
            subcomponents:  Pass an empty list to start a new subcomponents request

        Returns:
            List[str]: subcomponents of BEL subject or object
        """

        if subcomponents is None:
            subcomponents = []

        for arg in self.args:
            if arg.__class__.__name__ == "Function":
                subcomponents.append(arg.to_string())
                arg.subcomponents(subcomponents)
            else:
                subcomponents.append(arg.to_string())
                if hasattr(arg, "entity") and arg.entity.nsval.label:
                    subcomponents.append(f"{arg.entity.nsval.namespace}:{arg.entity.nsval.label}")

        return subcomponents


#####################
# Argument objects #
#####################
class Arg(object):
    def __init__(self, version: str = "latest", parent=None, span: Union[Span, NsArgSpan] = None):

        self.optional = False
        self.type = "Arg"
        self.version = version

        self.parent = parent
        self.siblings = []

        self.belspec = get_enhanced_belspec(self.version)

        # https://github.com/belbio/bel/issues/13

        # used for sorting arguments (position, modifier, modifier-specific sort parameter)
        #    position = position specific arguments
        # p(HGNC:AKT1, loc(X), pmod(Ph, 3), pmod(Ph, 4))
        # Arg: HGNC:AKT1 -> (1)
        # Arg: loc() -> (2, loc, "X")
        # Arg: pmod(Ph, 2) -> (2, pmod, 3)
        # Args are sorted via
        self.sort_tuple: Tuple = ()

        self.span: Optional[Span] = span

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
        Arg.__init__(self, parent)

        self.entity = entity
        self.span: NsArgSpan = span
        self.parent = parent
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

    def to_string(self, fmt: str = "medium", ignore_location: bool = False) -> str:

        return str(self.entity)

    def print_tree(self, fmt: str = "medium") -> str:

        return f"NSArg: {str(self.entity)} entity: {self.entity}"

    def __str__(self):
        return str(self.entity)

    __repr__ = __str__


class StrArg(Arg):
    def __init__(self, value, span: Span = None, parent=None):
        Arg.__init__(self, parent, span)
        self.value = value
        self.type = "StrArg"
        self.span: Span = span
        self.parent = parent

    def update(self, value: str):
        """Update to new BEL Entity"""

        self.value = value
        self.span = None

    def to_string(self, fmt: str = "medium", ignore_location: bool = False) -> str:
        """Convert AST object to string

        Args:
            fmt (str): short, medium, long formatted BEL statements
                short = short function and short relation format
                medium = short function and long relation format
                long = long function and long relation format

        Returns:
            str: string version of BEL AST
        """
        return f"{quote_string(self.value)}"

    def print_tree(self, fmt: str = "medium") -> str:
        return f"StrArg: {self.value}"

    def __str__(self):
        return f"StrArg: {self.value}"

    __repr__ = __str__


class ParseInfo:
    """BEL Assertion Parse Information

    Matching quotes need to be gathered first
    """

    def __init__(self, assertion: Optional[AssertionStr] = None, version: str = "latest"):

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

    def get_parse_info(self, assertion: AssertionStr = None, version: str = "latest"):
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
        self.version = check_version(version)
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

        return self.args_to_components()

    def args_to_components(self):
        """Convert AST args to subject, relation, object components"""

        # Subject only assertion
        #        if len(self.args) == 1 and self.args[0].type == "Function":
        if len(self.args) == 1:
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
                    msg=f"Could not parse Assertion - bad relation? {self.args[1]}",
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

    def optimize(self):
        """Optimize Assertion

        Currently this only optimizes reactions if they match the following pattern
        reactants(A, B) -> products(complex(A, B))  SHOULD BE complex(A, B)
        """

        if hasattr(self, "args"):
            for idx, arg in enumerate(self.args):
                if arg and arg.type == "Function":
                    self.args[idx] = arg.optimize()

        self.args_to_components()

        return self

    def subcomponents(self, subcomponents=None):
        """Generate subcomponents of the BEL subject or object

        Args:
            AST
            subcomponents:  Pass an empty list to start a new subcomponents request

        Returns:
            List[str]: subcomponents of BEL subject or object
        """

        if subcomponents is None:
            subcomponents = []

        for arg in self.args:
            if arg.__class__.__name__ == "Function":
                subcomponents.append(arg.to_string())
                arg.subcomponents(subcomponents)
            else:
                subcomponents.append(arg.to_string())
                if hasattr(arg, "entity") and arg.entity.nsval.label:
                    subcomponents.append(f"{arg.entity.nsval.namespace}:{arg.entity.nsval.label}")

        return subcomponents

    def to_string(self, fmt: str = "medium", ignore_location: bool = False) -> str:
        """Convert AST object to string

        Args:
            fmt (str): short, medium, long formatted BEL statements
                short = short function and short relation format
                medium = short function and long relation format
                long = long function and long relation format
            ignore_location: don't add location to output string

        Returns:
            str: string version of BEL AST
        """

        # TODO - add handling for nested BEL Assertions

        if self.subject and self.relation and self.object:
            if isinstance(self.object, BELAst):
                return "{} {} ({})".format(
                    self.subject.to_string(fmt=fmt, ignore_location=ignore_location),
                    self.relation.to_string(fmt=fmt),
                    self.object.to_string(fmt=fmt, ignore_location=ignore_location),
                )
            else:
                return "{} {} {}".format(
                    self.subject.to_string(fmt=fmt, ignore_location=ignore_location),
                    self.relation.to_string(fmt=fmt),
                    self.object.to_string(fmt=fmt, ignore_location=ignore_location),
                )

        elif self.subject:
            return "{}".format(self.subject.to_string(fmt=fmt, ignore_location=ignore_location))

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
