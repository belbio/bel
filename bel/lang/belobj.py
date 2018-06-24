import importlib
import sys
from typing import Mapping, Any, List, Tuple
from tatsu.exceptions import FailedParse

import bel.lang.bel_specification as bel_specification
import bel.lang.bel_utils as bel_utils
import bel.lang.ast as lang_ast
import bel.lang.exceptions as bel_ex
import bel.lang.semantics as semantics
import bel.lang.computed_edges as computed_edges

from bel.Config import config

import logging
log = logging.getLogger(__name__)

sys.path.append('../')


class BEL(object):
    """BEL Language object

    This object handles BEL statement/triple processing, parsing, (de)canonicalization,
    orthologization, computing BEL Edges and (TODO) statement completion.

    To convert BEL Statement to BEL Edges:

        statement = "p(HGNC:AKT1) increases p(HGNC:EGF)"
        bel_obj = bel.lang.belobj.BEL('2.0.0', 'https://api.bel.bio/v1')  # can get default version and api_url from belbio_conf.yml file as well
        bel_obj.parse(statement)  # Adds ast to bel_obj
        bel_obj.orthologize('TAX:10090')  # Run orthologize before canonicalize if needed, updates bel_obj.ast and returns self
        bel_obj.canonicalize()  # updates bel_obj.ast and returns self

        computed_edges = bel_obj.computed()

        primary_edge = bel_obj.ast.to_components()

    """

    def __init__(self, version: str = None, api_url: str = None) -> None:
        """Initialize BEL object used for validating/processing/etc BEL statements

        Args:
            version (str): BEL Version, defaults to config['bel']['lang']['default_bel_version']
            api_url (str): BEL API endpoint,  defaults to config['bel_api']['servers']['api_url']
        """

        bel_versions = bel_specification.get_bel_versions()

        # use bel_utils._default_to_version to check if valid version, and if it exists or not
        if not version:
            self.version = config['bel']['lang']['default_bel_version']
        else:
            self.version = version

        self.version = bel_utils._default_to_version(self.version, bel_versions)

        if self.version not in bel_versions:
            log.error('Cannot continue with invalid version. Exiting.')
            sys.exit()

        if not api_url:
            self.api_url = config['bel_api']['servers']['api_url']
        else:
            self.api_url = api_url

        # Validation error/warning messages
        # List[Tuple[str, str]], e.g. [('ERROR', 'this is an error msg'), ('WARNING', 'this is a warning'), ]
        self.validation_messages = []

        # self.semantics = BELSemantics()  # each instance also instantiates a BELSemantics object used in parsing statements
        self.spec = bel_specification.get_specification(self.version)

        # bel_utils._dump_spec(self.spec)

        # Import Tatsu parser
        # use importlib to import our parser (a .py file) and set the BELParse object as an instance variable

        try:
            imported_parser_file = importlib.import_module(self.spec['admin']['parser_path'])
            self.parser = imported_parser_file.BELParser()
        except Exception as e:
            # if not found, we raise the NoParserFound exception which can be found in bel.lang.exceptions
            raise bel_ex.NoParserFound(self.version)

    def parse(self, statement: str, strict: bool = False, parseinfo: bool = False, rule_name: str = 'start', error_level: str = 'WARNING') -> 'BEL':
        """Parse and semantically validate BEL statement

        Parses a BEL statement given as a string and returns an AST, Abstract Syntax Tree (defined in ast.py)
        if the statement is valid, self.parse_valid. Else, the AST attribute is None and there will be validation error messages
        in self.validation_messages.  self.validation_messages will contain WARNINGS if
        warranted even if the statement parses correctly.

        Error Levels are similar to log levels - selecting WARNING includes both
        WARNING and ERROR, selecting ERROR just includes ERROR

        Args:
            statement: BEL statement
            strict: specify to use strict or loose parsing; defaults to loose
            parseinfo: specify whether or not to include Tatsu parse information in AST
            rule_name: starting point in parser - defaults to 'start'
            error_level: return ERRORs only or also WARNINGs

        Returns:
            ParseObject: The ParseObject which contain either an AST or error messages.
        """

        self.ast = None
        self.parse_valid = False
        self.parse_visualize_error = ''
        self.validation_messages = []  # Reset messages when parsing a new BEL Statement

        self.original_bel_stmt = statement

        # pre-process to remove extra white space, add space after commas, etc.
        self.bel_stmt = bel_utils.preprocess_bel_stmt(statement)

        # TODO - double check these tests before enabling
        # is_valid, messages = bel_utils.simple_checks(self.bel_stmt)
        # if not is_valid:
        #     self.validation_messages.extend(messages)
        #     return self

        # Check to see if empty string for bel statement
        if len(self.bel_stmt) == 0:
            self.validation_messages.append(('ERROR', 'Please include a valid BEL statement - found empty string.'))
            return self

        try:
            # see if an AST is returned without any parsing errors

            ast_dict = self.parser.parse(self.bel_stmt, rule_name=rule_name, trace=False, parseinfo=parseinfo)
            self.ast = lang_ast.ast_dict_to_objects(ast_dict, self)

            self.parse_valid = True

        except FailedParse as e:
            # if an error is returned, send to handle_syntax, error
            error, visualize_error = bel_utils.handle_parser_syntax_error(e)
            self.parse_visualize_error = visualize_error
            self.validation_messages.append(('ERROR', f'{error} BEL: {self.original_bel_stmt}\n{visualize_error}'))
            self.ast = None

        except Exception as e:
            log.error('Error {}, error type: {}'.format(e, type(e)))
            self.validation_messages.append(('ERROR', 'Error {}, error type: {}'.format(e, type(e))))

        # Run semantics validation - and decorate AST with nsarg entity_type and arg optionality
        semantics.validate(self, error_level)

        return self

    def canonicalize(self, namespace_targets: Mapping[str, List[str]] = None) -> 'BEL':
        """
        Takes an AST and returns a canonicalized BEL statement string.

        Args:
            namespace_targets (Mapping[str, List[str]]): override default canonicalization
                settings of BEL.bio API api_url - see {api_url}/status to get default canonicalization settings

        Returns:
            BEL: returns self
        """

        # TODO Need to order position independent args

        self.ast = bel_utils.convert_namespaces_ast(self.ast, canonicalize=True, api_url=self.api_url, namespace_targets=namespace_targets)

        return self

    def decanonicalize(self, namespace_targets: Mapping[str, List[str]] = None) -> 'BEL':
        """
        Takes an AST and returns a decanonicalized BEL statement string.

        Args:
            namespace_targets (Mapping[str, List[str]]): override default decanonicalization
                settings of BEL.bio API endpoint - see {endpoint}/status to get default decanonicalization settings

        Returns:
            BEL: returns self
        """

        self.ast = bel_utils.convert_namespaces_ast(self.ast, decanonicalize=True, namespace_targets=namespace_targets)
        return self

    def orthologize(self, species_id: str) -> 'BEL':
        """Orthologize BEL AST to given species_id

        Will return original entity (ns:value) if no ortholog found.

        Args:
            species_id (str): species id to convert genes/rna/proteins into

        Returns:
            BEL: returns self
        """

        self.ast = bel_utils.orthologize(self.ast, self, species_id)

        return self

    def compute_edges(self, rules: List[str] = None, ast_result=False, fmt="medium") -> List[Mapping[str, Any]]:
        """Computed edges from primary BEL statement

        Takes an AST and generates all computed edges based on BEL Specification YAML computed signatures.
        Will run only the list of computed edge rules if given.

        Args:
            rules (list): a list of rules to filter; only the rules in this list will be applied to computed
            fmt (str): short, medium or long version of BEL Edge (function and relation names)
        Returns:
            List[Mapping[str, Any]]: BEL Edges in medium format
        """

        compute_rules = self.spec['computed_signatures'].keys()

        if rules:
            compute_rules = [rule for rule in compute_rules if rule in rules]

        edges_ast = computed_edges.compute_edges(self.ast, self.spec, compute_rules)

        if ast_result:
            return edges_ast

        edges = []
        for es, er, eo in edges_ast:

            # Some components are not part of AST - e.g. NSArg
            if isinstance(es, lang_ast.Function):
                es = es.to_string(fmt='medium')
            if isinstance(eo, lang_ast.Function):
                eo = eo.to_string(fmt='medium')

            edges.append({'subject': es, 'relation': er, 'object': eo})

        return edges

    def to_string(self, fmt: str = 'medium') -> str:
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
            return self.ast.to_string(ast_obj=self.ast, fmt=fmt)
        else:
            return ''

    def to_triple(self, fmt: str = 'medium') -> dict:
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
            return self.ast.to_components(ast_obj=self.ast, fmt=fmt)
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
            return ''


