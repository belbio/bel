# Standard Library
import datetime
import importlib
import os
import sys
from typing import Any, List, Mapping, Optional, Union

# Third Party
# Third Party Imports
from loguru import logger

# Local
# Local Imports
import bel.belspec.crud
import bel.core.settings as settings
import bel.terms.terms
from bel.lang.ast import BELAst
from bel.schemas.bel import AssertionStr, Key

sys.path.append("../")

"""BEL object

This manages the BEL AST object which is responsible for parsing, validation, (de)canonicalization and orthologization.

The BelEntity Object handles all of the NSArg entity manipulation (canonicalization, normalization, orthologization, etc).
"""


class BEL(object):
    """BEL Language object

    This object handles BEL statement/triple processing, parsing, (de)canonicalization,
    orthologization and other purposes.
    """

    def __init__(self, assertion: AssertionStr = None, version: str = "latest") -> None:
        """Initialize BEL object used for validating/processing/etc BEL statements

        Args:
            assertion: BEL Assertion
            version: BEL Version - defaults to settings.BEL_DEFAULT_VERSION or latest version
        """

        self.assertion = assertion

        self.clean_assertion()

        self.version = bel.belspec.crud.check_version(version)

        # Validation error/warning messages
        # List[Tuple[str, str]], e.g. [('ERROR', 'this is an error msg'), ('WARNING', 'this is a warning'), ]
        self.validation_messages = []

        self.ast: Optional[BELAst] = None

        if self.assertion:
            self.ast = BELAst(assertion=assertion, version=version)

    def clean_assertion(self):
        """Various tasks to clean the assertion component strings"""

        # Remove smart quotes
        if self.assertion:
            self.assertion.subject = (
                self.assertion.subject.replace("“", '"').replace("”", '"').strip()
            )
            self.assertion.relation = (
                self.assertion.relation.replace("“", '"').replace("”", '"').strip()
            )
            self.assertion.object = (
                self.assertion.object.replace("“", '"').replace("”", '"').strip()
            )
            self.assertion.entire = (
                self.assertion.entire.replace("“", '"').replace("”", '"').strip()
            )

    def parse(self, assertion: AssertionStr = None) -> "BEL":
        """Parse BEL Assertion string"""

        # Add or override assertion string object in parse method
        if assertion is not None:
            self.assertion = assertion
            self.clean_assertion()

        self.ast = BELAst(assertion=assertion, version=self.version)

        return self

    def canonicalize(self) -> "BEL":
        """
        Takes an AST and returns a canonicalized BEL statement string.

        Returns:
            BEL: returns self
        """

        # TODO Need to order position independent args

        if self.ast:
            self.ast.canonicalize()

        return self

    def decanonicalize(self) -> "BEL":
        """
        Takes an AST and returns a decanonicalized BEL statement string.

        Returns:
            BEL: returns self
        """

        if self.ast:
            self.ast.decanonicalize()

        return self

    def orthologize(self, species_key: Key) -> "BEL":
        """Orthologize BEL AST to given species_id

        Will return original entity (ns:value) if no ortholog found.

        Args:
            species_id (str): species id to convert genes/rna/proteins into

        Returns:
            BEL: returns self
        """

        if self.ast:
            self.ast.orthologize(species_key)

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

        if self.ast:
            return f"{self.ast.to_string(fmt=fmt)}"

    def to_triple(self, fmt: str = "medium") -> dict:
        """Convert AST object to BEL triple

        Args:
            fmt (str): short, medium, long formatted BEL statements
                short = short function and short relation format
                medium = short function and long relation format
                long = long function and long relation format

        Returns:
            dict: {'subject': <subject>, 'relation': <relations>, 'object': <object>}
        """

        if self.ast:
            return self.ast.to_triple(fmt=fmt)
        else:
            return {}

    def print_tree(self) -> str:
        """Convert AST object to tree view of BEL AST

        Returns:
            printed tree of BEL AST
        """

        if self.ast:
            return self.ast.print_tree(ast_obj=self.ast)
        else:
            return ""

    def dump(self) -> str:
        """Dump out the BEL object"""

        # Standard Library
        import textwrap

        s = f"""
            BEL Object dump:
                version: {self.version}
                assertion: {self.assertion.entire}
                species: {self.ast.species}
                ast: {self.ast.print_tree()}
        """

        print(textwrap.dedent(s))
