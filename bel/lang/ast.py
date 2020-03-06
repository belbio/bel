#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
ast_dict from Tatsu is converted to this Ast Class object and used for
validation and BEL transformation (e.g. canonicalization, orthologization, etc)
"""

# Standard Library
import copy
import json
import logging
import re
import sys
import traceback
from typing import Any, List, Mapping

# Third Party Imports
import httpx
import structlog
import yaml

# Local Imports
import bel.terms.orthologs
import bel.terms.terms
from bel.Config import config
from bel.utils import url_path_param_quoting

log = structlog.getLogger(__name__)


########################
# BEL statement AST #
########################
class BELAst(object):
    def __init__(self, bel_subject, bel_relation, bel_object, spec):
        self.bel_subject = bel_subject
        self.bel_relation = bel_relation
        self.bel_object = bel_object
        self.spec = spec  # bel specification dictionary
        self.type = "BELAst"
        self.species = set()  # tuples of (species_id, species_label)
        self.collected_nsarg_norms = False
        self.collected_orthologs = False
        self.partially_orthologized = False
        self.args = [self.bel_subject, self.bel_object]

    def dump(self):
        return {
            "bel_subject": self.bel_subject.to_string(),
            "bel_relation": self.bel_relation,
            "bel_object": self.bel_object.to_string(),
            "type": self.type,
            "collected_nsarg_norms": self.collected_nsarg_norms,
            "collected_orthologs": self.collected_orthologs,
            "args": self.args,
            "spec": "Not included",
        }

    def canonicalize(self):

        if not self.collected_nsarg_norms:
            log.error(
                f"Cannot canonicalize without running collected_nsarg_norms() on BEL object first {self.dump()}"
            )
            log.info(self.dump)
            traceback.print_stack(file=sys.stdout)
            return self

        if self and isinstance(self, NSArg):
            self.canonicalize()

        if hasattr(self, "args"):
            for arg in self.args:
                if arg:
                    arg.canonicalize()

        return self

    def decanonicalize(self):
        if not self.collected_nsarg_norms:
            log.error(
                f"Cannot decanonicalize without running collected_nsarg_norms() on BEL object first {self.dump()}"
            )
            log.info(self.dump)
            traceback.print_stack(file=sys.stdout)
            return self

        if self and isinstance(self, NSArg):
            self.decanonicalize()

        if hasattr(self, "args"):
            for arg in self.args:
                if arg:
                    arg.decanonicalize()

        return self

    def orthologize(self, species_id, belast=None):
        if not self.collected_orthologs:
            log.error(
                f"Cannot orthologize without running collect_orthologs() on BEL object first {self.dump()}"
            )
            log.info(self.dump)
            traceback.print_stack(file=sys.stdout)
            return self

        if hasattr(self, "args"):
            if belast is None:
                belast = self
            for arg in self.args:
                if arg:
                    arg.orthologize(species_id, belast)

        return self

    def to_string(self, ast_obj=None, fmt: str = "medium") -> str:
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

        if not ast_obj:
            ast_obj = self

        bel_relation = None
        if self.bel_relation and fmt == "short":
            bel_relation = self.spec["relations"]["to_short"].get(
                self.bel_relation, self.bel_relation
            )
        elif self.bel_relation:
            bel_relation = self.spec["relations"]["to_long"].get(
                self.bel_relation, self.bel_relation
            )

        if self.bel_subject and bel_relation and self.bel_object:
            if isinstance(self.bel_object, BELAst):
                return "{} {} ({})".format(
                    self.bel_subject.to_string(fmt=fmt),
                    bel_relation,
                    self.bel_object.to_string(fmt=fmt),
                )
            else:
                return "{} {} {}".format(
                    self.bel_subject.to_string(fmt=fmt),
                    bel_relation,
                    self.bel_object.to_string(fmt=fmt),
                )

        elif self.bel_subject:
            return "{}".format(self.bel_subject.to_string(fmt=fmt))

        else:
            return ""

    def to_triple(self, ast_obj=None, fmt="medium"):
        """Convert AST object to BEL triple

        Args:
            fmt (str): short, medium, long formatted BEL statements
                short = short function and short relation format
                medium = short function and long relation format
                long = long function and long relation format

        Returns:
            dict: {'subject': <subject>, 'relation': <relations>, 'object': <object>}
        """

        if not ast_obj:
            ast_obj = self

        if self.bel_subject and self.bel_relation and self.bel_object:
            if self.bel_relation.startswith("has"):
                bel_relation = self.bel_relation
            elif fmt == "short":
                bel_relation = self.spec["relations"]["to_short"].get(self.bel_relation, None)
            else:
                bel_relation = self.spec["relations"]["to_long"].get(self.bel_relation, None)

            bel_subject = self.bel_subject.to_string(fmt=fmt)

            if isinstance(self.bel_object, (BELAst)):
                bel_object = f"({self.bel_object.to_string(fmt=fmt)})"
            else:
                bel_object = self.bel_object.to_string(fmt=fmt)

            return {"subject": bel_subject, "relation": bel_relation, "object": bel_object}

        elif self.bel_subject:
            return {"subject": self.bel_subject.to_string(fmt=fmt)}

        else:
            return None

    def __str__(self):
        return self.to_string(self)

    __repr__ = __str__

    def print_tree(self, ast_obj=None):
        """Convert AST object to tree view of BEL AST

        Returns:
            prints tree of BEL AST to STDOUT
        """

        if not ast_obj:
            ast_obj = self

        if hasattr(self, "bel_subject"):
            print("Subject:")
            self.bel_subject.print_tree(self.bel_subject, indent=0)

        if hasattr(self, "bel_relation"):
            print("Relation:", self.bel_relation)

        if hasattr(self, "bel_object"):
            if self.bel_object.type == "BELAst":
                if hasattr(self, "bel_subject"):
                    print("Nested Subject:")
                    self.bel_object.bel_subject.print_tree(indent=0)

                if hasattr(self, "bel_relation"):
                    print("Nested Relation:", self.bel_object.bel_relation)

                if hasattr(self, "bel_object"):
                    print("Nested Object:")
                    self.bel_object.bel_object.print_tree(indent=0)
            else:
                print("Object:")
                self.bel_object.print_tree(self.bel_object, indent=0)

        return self


###################
# Function object #
###################


class Function(object):
    def __init__(self, name, spec, parent_function=None):

        self.name = spec["functions"]["to_long"].get(name, name)
        self.name_short = spec["functions"]["to_short"].get(name, name)
        if self.name in spec["functions"]["info"]:
            self.function_type = spec["functions"]["info"][self.name]["type"]
        else:
            self.function_type = ""

        self.type = "Function"

        self.parent_function = parent_function
        self.spec = spec
        self.position_dependent = False
        self.args = []
        self.siblings = []

    def is_primary(self):
        if self.function_type == "primary":
            return True
        return False

    def is_modifier(self):
        if self.function_type == "modifier":
            return True
        return False

    def add_argument(self, arg):
        self.args.append(arg)

    def add_sibling(self, sibling):
        self.siblings.append(sibling)

    def change_parent_fn(self, parent_function):
        self.parent_function = parent_function

    def change_function_type(self, function_type):
        self.function_type = function_type

    def canonicalize(self):
        if isinstance(self, NSArg):
            self.canonicalize()

        if hasattr(self, "args"):
            for arg in self.args:
                arg.canonicalize()

        return self

    def decanonicalize(self):
        if isinstance(self, NSArg):
            self.decanonicalize()

        if hasattr(self, "args"):
            for arg in self.args:
                arg.decanonicalize()

        return self

    def orthologize(self, species_id, belast):
        if isinstance(self, NSArg):
            self.orthologize(species_id)

        if hasattr(self, "args"):
            for arg in self.args:
                arg.orthologize(species_id, belast)

        return self

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

    def print_tree(self, ast_obj=None, indent=0):
        if not ast_obj:
            ast_obj = self
        for arg in self.args:
            if arg.__class__.__name__ == "Function":
                arg.print_tree(arg, indent + 1)
            else:
                print("\t" * (indent + 1) + arg.print_tree())

    def subcomponents(self, subcomponents):
        """Generate subcomponents of the BEL subject or object

        These subcomponents are used for matching parts of a BEL
        subject or Object in the Edgestore.

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
    def __init__(self, parent_function):
        self.parent_function = parent_function
        self.siblings = []
        self.optional = False
        self.type = "Arg"

    def add_sibling(self, sibling):
        self.siblings.append(sibling)

    def canonicalize(self):
        return self

    def decanonicalize(self):
        return self

    def orthologize(self, species_id, belast):
        return self


class NSArg(Arg):
    def __init__(self, namespace, value, parent_function=None, value_types=[]):
        Arg.__init__(self, parent_function)
        self.namespace = namespace
        self.value = self.normalize_nsarg_value(value)
        self.value_types = value_types
        self.type = "NSArg"
        self.canonical = None
        self.decanonical = None
        self.species_id = None
        self.species_label = None
        self.orthologs = (
            {}
        )  # {'TAX:9606': {'species_label': 'human', 'canonical': 'EG:207', 'decanonical': 'HGNC:AKT1'}, 'TAX:10090': {'species_label': 'mouse', canonical': 'EG:11651', 'decanonical': 'MGI:Akt1'}, ...
        self.orthology_species = None
        self.orthologized = None  # True for orthologized - False -> unable to orthologize
        self.original = f"{namespace}:{value}"

        # What entity types can this be from the function signatures?
        #    this is used for statement autocompletion and entity validation
        self.entity_types = []

    def change_nsvalue(self, namespace, value):
        """Deprecated"""

        self.namespace = namespace
        self.value = value

    def update_nsval(self, *, nsval: str = None, ns: str = None, val: str = None) -> None:
        """Update Namespace and valueast.

        Args:
            nsval: e.g. HGNC:AKT1
            ns: namespace
            val: value of entity
        """

        if not (ns and val) and nsval:
            (ns, val) = nsval.split(":", 1)
        elif not (ns and val) and not nsval:
            log.error("Did not update NSArg - no ns:val or nsval provided")

        self.namespace = ns
        self.value = val

    def add_value_types(self, value_types):
        self.value_types = value_types

    def normalize_nsarg_value(self, nsarg_value):
        """Normalize NSArg value

        If needs quotes (only if it contains whitespace, comma or ')' ), make sure
        it is quoted, else remove quotes

        Args:
            nsarg_value (str): NSArg value, e.g. AKT1 of HGNC:AKT1

        Returns:
            str:
        """

        return quoting_nsarg(nsarg_value)

    def canonicalize(self):
        if isinstance(self, NSArg):
            self.update_nsval(nsval=self.canonical)
        return self

    def decanonicalize(self):
        if isinstance(self, NSArg):
            self.update_nsval(nsval=self.decanonical)
        return self

    def orthologize(self, ortho_species_id, belast):
        """Decanonical ortholog name used"""

        if (
            self.orthologs
            and ortho_species_id in self.orthologs
            and ortho_species_id != self.species_id
        ):
            self.orthology_species = ortho_species_id
            self.canonical = self.orthologs[ortho_species_id]["canonical"]
            self.decanonical = self.orthologs[ortho_species_id]["decanonical"]
            self.update_nsval(nsval=self.decanonical)
            self.orthologized = True

        elif self.species_id and ortho_species_id not in self.orthologs:
            self.orthologized = False
            belast.partially_orthologized = True

        return self

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
        return f"{self.namespace}:{self.value}"

    def print_tree(self, fmt: str = "medium") -> str:
        return f"NSArg: {self.namespace}:{self.value} canonical: {self.canonical} decanonical: {self.decanonical} orthologs: {self.orthologs} orig_species: {self.orthology_species}"

    def __str__(self):
        return f"{self.namespace}:{self.value}"

    __repr__ = __str__


class StrArg(Arg):
    def __init__(self, value, parent_function, value_types=[]):
        Arg.__init__(self, parent_function)
        self.value = value
        self.value_types = value_types
        self.type = "StrArg"

    def add_value_types(self, value_types):
        self.value_types = value_types

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
        return "{}".format(self.value)

    def __str__(self):
        return "StrArg: {}".format(self.value)

    __repr__ = __str__


def ast_dict_to_objects(ast_dict: Mapping[str, Any], bel_obj) -> BELAst:
    """Convert Tatsu AST dictionary to BEL AST object

    Args:
        ast_dict (Mapping[str, Any])

    Returns:
        BELAst: object representing the BEL Statement AST
    """
    ast_subject = ast_dict.get("subject", None)
    ast_object = ast_dict.get("object", None)

    bel_subject = None
    bel_object = None
    bel_relation = ast_dict.get("relation")

    if ast_subject:
        bel_subject = function_ast_to_objects(ast_subject, bel_obj)

    if ast_object:
        bel_object = function_ast_to_objects(ast_object, bel_obj)

    ast_obj = BELAst(bel_subject, bel_relation, bel_object, bel_obj.spec)

    return ast_obj


def function_ast_to_objects(fn_ast_dict, bel_obj):
    # needed and used

    # print(fn_ast_dict)
    spec = bel_obj.spec  # bel specification

    func_name = fn_ast_dict.get("function", None)
    potential_bel_stmt = fn_ast_dict.get("bel_statement", None)

    if func_name is None and potential_bel_stmt is not None:  # this is a nested BEL statement
        tmp_fn_obj = ast_dict_to_objects(potential_bel_stmt, bel_obj)
    else:
        tmp_fn_obj = Function(func_name, spec)
        tmp_fn_obj_args = fn_ast_dict.get("function_args", None)

        # for each argument in tmp_fn_obj_args, add it to our function object using add_args_to_compute_obj()
        add_args_to_compute_obj(bel_obj, tmp_fn_obj, tmp_fn_obj_args)

    return tmp_fn_obj


def add_args_to_compute_obj(our_bel_obj, our_obj, our_obj_args):
    # needed and used
    tmp_all_args_objs = []

    for argument in our_obj_args:

        fn_args = []
        tmp_arg_obj = None

        if "function" in argument:
            fn = argument.get("function", None)
            fn_parent = our_obj
            fn_args = argument.get("function_args", [])

            tmp_arg_obj = Function(fn, our_bel_obj.spec, parent_function=fn_parent)

        elif "modifier" in argument:
            fn = argument.get("modifier", None)
            fn_parent = our_obj
            fn_args = argument.get("modifier_args", [])

            tmp_arg_obj = Function(fn, our_bel_obj.spec, parent_function=fn_parent)

        elif "ns_arg" in argument:
            ns = argument["ns_arg"]["ns"]
            nsv = argument["ns_arg"]["ns_value"]
            ns_parent = our_obj

            tmp_arg_obj = NSArg(ns, nsv, ns_parent)

        elif "str_arg" in argument:
            sv = argument.get("str_arg", None)
            sv_parent = our_obj

            tmp_arg_obj = StrArg(sv, sv_parent)

        else:
            continue

        if fn_args:
            add_args_to_compute_obj(our_bel_obj, tmp_arg_obj, fn_args)

        if tmp_arg_obj is not None:
            our_obj.add_argument(tmp_arg_obj)
            tmp_all_args_objs.append(tmp_arg_obj)

    # nested loop to add siblings to each arg. exclude the arg itself as its own sibling by ignoring if index match.
    for idx, arg_obj in enumerate(tmp_all_args_objs):
        for sibling_idx, sibling_arg_obj in enumerate(tmp_all_args_objs):

            if idx == sibling_idx:  # skip adding self as sibling
                continue
            else:
                arg_obj.add_sibling(sibling_arg_obj)

    return


# BEL object utilities


def convert_nsarg_db(nsarg: str) -> dict:
    """Get default canonical and decanonical versions of nsarg

    Returns:
        dict: {'canonical': <nsarg>, 'decanonical': <nsarg>}
    """


def convert_nsarg(
    nsarg: str,
    api_url: str = None,
    namespace_targets: Mapping[str, List[str]] = None,
    canonicalize: bool = False,
    decanonicalize: bool = False,
) -> str:
    """[De]Canonicalize NSArg

    Args:
        nsarg (str): bel statement string or partial string (e.g. subject or object)
        api_url (str): BEL.bio api url to use, e.g. https://api.bel.bio/v1
        namespace_targets (Mapping[str, List[str]]): formatted as in configuration file example
        canonicalize (bool): use canonicalize endpoint/namespace targets
        decanonicalize (bool): use decanonicalize endpoint/namespace targets

    Results:
        str: converted NSArg
    """

    if not api_url:
        api_url = config["bel_api"]["servers"]["api_url"]
        if not api_url:
            log.error("Missing api url - cannot convert namespace")
            return None

    params = None
    if namespace_targets:
        namespace_targets_str = json.dumps(namespace_targets)
        params = {"namespace_targets": namespace_targets_str}

    if not namespace_targets:
        if canonicalize:
            api_url = api_url + "/terms/{}/canonicalized"
        elif decanonicalize:
            api_url = api_url + "/terms/{}/decanonicalized"
        else:
            log.warning("Missing (de)canonical flag - cannot convert namespaces")
            return nsarg
    else:

        api_url = api_url + "/terms/{}/canonicalized"  # overriding with namespace_targets

    request_url = api_url.format(url_path_param_quoting(nsarg))

    r = httpx.get(request_url, params=params, timeout=10)

    if r and r.status_code == 200:
        nsarg = r.json().get("term_id", nsarg)
    elif not r or r.status_code == 404:
        log.error(f"[de]Canonicalization endpoint missing: {request_url}")

    return nsarg


def convert_namespaces_str(
    bel_str: str,
    api_url: str = None,
    namespace_targets: Mapping[str, List[str]] = None,
    canonicalize: bool = False,
    decanonicalize: bool = False,
) -> str:
    """Convert namespace in string

    Uses a regex expression to extract all NSArgs and replace them with the
    updated NSArg from the BEL.bio API terms endpoint.

    Args:
        bel_str (str): bel statement string or partial string (e.g. subject or object)
        api_url (str): BEL.bio api url to use, e.g. https://api.bel.bio/v1
        namespace_targets (Mapping[str, List[str]]): formatted as in configuration file example
        canonicalize (bool): use canonicalize endpoint/namespace targets
        decanonicalize (bool): use decanonicalize endpoint/namespace targets

    Results:
        str: bel statement with namespaces converted
    """

    # pattern - look for capitalized namespace followed by colon
    #           and either a quoted string or a string that
    #           can include any char other than space, comma or ')'
    matches = re.findall(r'([A-Z]+:"(?:\\.|[^"\\])*"|[A-Z]+:(?:[^\),\s]+))', bel_str)
    for nsarg in matches:
        if "DEFAULT:" in nsarg:  # skip default namespaces
            continue

        updated_nsarg = convert_nsarg(
            nsarg,
            api_url=api_url,
            namespace_targets=namespace_targets,
            canonicalize=canonicalize,
            decanonicalize=decanonicalize,
        )
        if updated_nsarg != nsarg:
            bel_str = bel_str.replace(nsarg, updated_nsarg)

    return bel_str


def convert_namespaces_ast(
    ast,
    api_url: str = None,
    namespace_targets: Mapping[str, List[str]] = None,
    canonicalize: bool = False,
    decanonicalize: bool = False,
):
    """Recursively convert namespaces of BEL Entities in BEL AST using API endpoint

    Canonicalization and decanonicalization is determined by endpoint used and namespace_targets.

    Args:
        ast (BEL): BEL AST
        api_url (str): endpoint url with a placeholder for the term_id (either /terms/<term_id>/canonicalized or /terms/<term_id>/decanonicalized)
        namespace_targets (Mapping[str, List[str]]): (de)canonical targets for converting BEL Entities

    Returns:
        BEL: BEL AST
    """

    if isinstance(ast, NSArg):
        given_term_id = "{}:{}".format(ast.namespace, ast.value)

        # Get normalized term if necessary
        if (canonicalize and not ast.canonical) or (decanonicalize and not ast.decanonical):
            normalized_term = convert_nsarg(
                given_term_id,
                api_url=api_url,
                namespace_targets=namespace_targets,
                canonicalize=canonicalize,
                decanonicalize=decanonicalize,
            )
            if canonicalize:
                ast.canonical = normalized_term
            elif decanonicalize:
                ast.decanonical = normalized_term

        # Update normalized term
        if canonicalize:
            ns, value = ast.canonical.split(":")
            ast.change_nsvalue(ns, value)
        elif decanonicalize:
            ns, value = ast.canonical.split(":")
            ast.change_nsvalue(ns, value)

    # Recursively process every NSArg by processing BELAst and Functions
    if hasattr(ast, "args"):
        for arg in ast.args:
            convert_namespaces_ast(
                arg,
                api_url=api_url,
                namespace_targets=namespace_targets,
                canonicalize=canonicalize,
                decanonicalize=decanonicalize,
            )

    return ast


def populate_ast_nsarg_defaults(ast, belast, species_id=None):
    """Recursively populate NSArg AST entries for default (de)canonical values

    This was added specifically for the BEL Pipeline. It is designed to
    run directly against ArangoDB and not through the BELAPI.

    Args:
        ast (BEL): BEL AST

    Returns:
        BEL: BEL AST
    """

    if isinstance(ast, NSArg):
        given_term_id = "{}:{}".format(ast.namespace, ast.value)

        r = bel.terms.terms.get_normalized_terms(given_term_id)
        ast.canonical = r["canonical"]
        ast.decanonical = r["decanonical"]

        r = bel.terms.terms.get_terms(ast.canonical)

        if len(r) > 0:
            ast.species_id = r[0].get("species_id", False)
            ast.species_label = r[0].get("species_label", False)

        # Check to see if species is set and if it's consistent
        #   if species is not consistent for the entire AST - set species_id/label
        #   on belast to False (instead of None)
        if ast.species_id and species_id is None:
            species_id = ast.species_id
            belast.species.add((ast.species_id, ast.species_label))

        elif ast.species_id and species_id and species_id != ast.species_id:
            belast.species_id = False
            belast.species_label = False

    # Recursively process every NSArg by processing BELAst and Functions
    if hasattr(ast, "args"):
        for arg in ast.args:
            populate_ast_nsarg_defaults(arg, belast, species_id)

    return ast


def orthologize(ast, bo, species_id: str):
    """Recursively orthologize BEL Entities in BEL AST using API endpoint

    NOTE: - will take first ortholog returned in BEL.bio API result (which may return more than one ortholog)

    Args:
        ast (BEL): BEL AST
        endpoint (str): endpoint url with a placeholder for the term_id

    Returns:
        BEL: BEL AST
    """

    # if species_id == 'TAX:9606' and str(ast) == 'MGI:Sult2a1':
    #     import pdb; pdb.set_trace()

    if not species_id:
        bo.validation_messages.append(("WARNING", "No species id was provided for orthologization"))
        return ast

    if isinstance(ast, NSArg):
        if ast.orthologs:
            # log.debug(f'AST: {ast.to_string()}  species_id: {species_id}  orthologs: {ast.orthologs}')
            if ast.orthologs.get(species_id, None):
                orthologized_nsarg_val = ast.orthologs[species_id]["decanonical"]
                ns, value = orthologized_nsarg_val.split(":")
                ast.change_nsvalue(ns, value)
                ast.canonical = ast.orthologs[species_id]["canonical"]
                ast.decanonical = ast.orthologs[species_id]["decanonical"]
                ast.orthologized = True
                bo.ast.species.add((species_id, ast.orthologs[species_id]["species_label"]))
            else:
                bo.ast.species.add((ast.species_id, ast.species_label))
                bo.validation_messages.append(
                    ("WARNING", f"No ortholog found for {ast.namespace}:{ast.value}")
                )
        elif ast.species_id:
            bo.ast.species.add((ast.species_id, ast.species_label))

    # Recursively process every NSArg by processing BELAst and Functions
    if hasattr(ast, "args"):
        for arg in ast.args:
            orthologize(arg, bo, species_id)

    return ast


def populate_ast_nsarg_orthologs(ast, species):
    """Recursively collect NSArg orthologs for BEL AST

    This requires bo.collect_nsarg_norms() to be run first so NSArg.canonical is available

    Args:
        ast: AST at recursive point in belobj
        species: dictionary of species ids vs labels for or
    """

    ortholog_namespace = "EG"

    if isinstance(ast, NSArg):
        if re.match(ortholog_namespace, ast.canonical):
            orthologs = bel.terms.orthologs.get_orthologs(ast.canonical, list(species.keys()))
            for species_id in species:
                if species_id in orthologs:
                    orthologs[species_id]["species_label"] = species[species_id]

            ast.orthologs = copy.deepcopy(orthologs)

    # Recursively process every NSArg by processing BELAst and Functions
    if hasattr(ast, "args"):
        for arg in ast.args:
            populate_ast_nsarg_orthologs(arg, species)

    return ast


def preprocess_bel_stmt(stmt: str) -> str:
    """Clean up basic formatting of BEL statement

    Args:
        stmt: BEL statement as single string

    Returns:
        cleaned BEL statement
    """
    # TODO - statement formatting should be done by reassembling the AST -
    #   the comma, space formatting breaks Term validation

    stmt = stmt.strip()  # remove newline at end of stmt
    stmt = re.sub(r",+", ",", stmt)  # remove multiple commas
    # stmt = re.sub(r",", ", ", stmt)  # add space after each comma  BREAKS Validation
    stmt = re.sub(r" +", " ", stmt)  # remove multiple spaces

    return stmt


# TODO remove AST normalize_nsarg_value for this and add tests
def quoting_nsarg(nsarg_value):
    """Quoting nsargs

    If needs quotes (only if it contains whitespace, comma or ')' ), make sure
        it is quoted, else don't add them.


    """
    quoted = re.findall(r'^"(.*)"$', nsarg_value)

    if re.search(r"[),\s]", nsarg_value):  # quote only if it contains whitespace, comma or ')'
        if quoted:
            return nsarg_value
        else:
            return f'"{nsarg_value}"'
    else:
        if quoted:
            return quoted[0]
        else:
            return nsarg_value


# # See TODO in bel.py for this function - not currently enabled
# def simple_checks(stmt):
#     """Simple typo checks for BEL statement

#     Args:
#         stmt (str): BEL statement as single string

#     Returns:
#         Tuple[bool, List[Tuple[str, str]]]: is valid? and list of ...
#     """
#     messages = []
#     is_valid = True

#     # check for even number of parenthesis
#     left_p_ct = stmt.count('(')
#     right_p_ct = stmt.count(')')

#     if left_p_ct < right_p_ct:
#         messages.append(('ERROR', 'Unbalanced parenthesis: Missing left parenthesis somewhere!'))
#     elif right_p_ct < left_p_ct:
#         messages.append(('ERROR', 'Unbalanced parenthesis: Missing right parenthesis somewhere!'))

#     # check for even number of quotation marks
#     single_quote_ct = stmt.count('\'')
#     double_quote_ct = stmt.count('"')

#     if single_quote_ct > 0:  # single quotes not allowed
#         messages.append(('ERROR', 'Single quotes are not allowed! Please use double quotes.'))

#     if double_quote_ct % 2 != 0:  # odd number of quotations
#         messages.append(('ERROR', 'Unbalanced quotations: Missing quotation mark somewhere!'))

#     if messages:
#         is_valid = False

#     (is_valid, messages)


def handle_parser_syntax_error(e):
    col_failed = e.pos
    info = e.buf.line_info(e.pos)
    text = info.text.rstrip()
    leading = re.sub(r"[^\t]", " ", text)[: info.col]
    text = text.expandtabs()
    leading = leading.expandtabs()
    undefined_type = e.stack[-1]

    err_visualizer = "{}\n{}^".format(text, leading)
    if undefined_type == "relations":
        error_msg = "Failed parse at position {}. " "Check that you have a valid relation.".format(
            col_failed
        )
    elif undefined_type == "funcs":
        error_msg = (
            "Failed parse at position {}. "
            "Check that you have a valid primary or modifier function.".format(col_failed)
        )
    elif undefined_type == "function_open":
        error_msg = (
            "Failed parse at position {}. "
            "Check that you have have opened your parenthesis correctly before this point.".format(
                col_failed
            )
        )
    elif undefined_type == "function_close":
        error_msg = (
            "Failed parse at position {}. "
            "Check that you have have closed your parenthesis correctly before this point.".format(
                col_failed
            )
        )
    elif undefined_type == "full_nsv":
        error_msg = (
            "Failed parse at position {}. "
            "Check that you have a valid namespace argument.".format(col_failed)
        )
    else:
        error_msg = (
            "Failed parse at position {}. "
            "Check to make sure commas/spaces are not missing.".format(col_failed, undefined_type)
        )

    return error_msg, err_visualizer


def _dump_spec(spec):
    """Dump bel specification dictionary using YAML

    Formats this with an extra indentation for lists to make it easier to
    use cold folding on the YAML version of the spec dictionary.
    """
    with open("spec.yaml", "w") as f:
        yaml.dump(spec, f, Dumper=MyDumper, default_flow_style=False)


def _default_to_version(version, available_versions):

    if not available_versions:
        log.error("No versions available.")
        return None

    if any(char.isalpha() for char in version):
        log.error("Invalid version number entered. Examples: '2', '3.1', '3.2.6'.")
        return None

    version_semantic_regex = r"(\d+)(?:\.(\d+))?(?:\.(\d+))?"
    our_match = re.match(version_semantic_regex, version)

    if our_match:
        wanted_major = int(our_match.group(1)) if our_match.group(1) else "x"
        wanted_minor = int(our_match.group(2)) if our_match.group(2) else "x"
        wanted_patch = int(our_match.group(3)) if our_match.group(3) else "x"
        formatted_version = "{}.{}.{}".format(wanted_major, wanted_minor, wanted_patch)
    else:
        log.error("Invalid version number entered. Examples: '2', '3.1', '3.2.6'.")
        return None

    if formatted_version in available_versions:
        return formatted_version

    # now we need to find closest available version that is EQUAL OR GREATER

    available_versions.sort(key=lambda s: list(map(int, s.split("."))))

    best_choice = None

    for v in available_versions:
        v_split = v.split(".")
        v_maj = int(v_split[0])
        v_min = int(v_split[1])
        v_pat = int(v_split[2])

        if wanted_major == v_maj and wanted_minor == v_min and wanted_patch == v_pat:
            return v  # exact version found. return.
        elif wanted_major == v_maj and wanted_minor == v_min and wanted_patch == "x":
            best_choice = v  # continue to see if higher patch number available
            continue
        elif wanted_major == v_maj and wanted_minor == "x" and wanted_patch == "x":
            best_choice = v  # continue to see if higher minor/patch number available
            continue

    if best_choice is not None:
        log.error(
            "Version {} not available in library. Defaulting to {}.".format(version, best_choice)
        )
    else:
        log.error("Version {} not available in library.".format(version))

    return best_choice


class MyDumper(yaml.Dumper):
    def increase_indent(self, flow=False, indentless=False):
        return super(MyDumper, self).increase_indent(flow, False)
