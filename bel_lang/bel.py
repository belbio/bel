import importlib
import sys
from typing import Mapping, Any, List, Tuple
from tatsu.exceptions import FailedParse

import bel_lang.bel_specification as bel_specification
import bel_lang.bel_utils as bel_utils
import bel_lang.ast as bel_lang_ast
import bel_lang.exceptions as bel_ex
import bel_lang.semantics as semantics
import bel_lang.computed_edges as computed_edges
from bel_lang.defaults import defaults

import logging
log = logging.getLogger(__name__)

sys.path.append('../')


class BEL(object):
    """BEL Language object

    This object handles BEL statement/triple processing, parsing, (de)canonicalization,
    orthologization, computing BEL Edges and (TODO) statement completion.

    To convert BEL Statement to BEL Edges:

        statement = "p(HGNC:AKT1) increases p(HGNC:EGF)"
        bel_obj = bel_lang.BEL(defaults['bel_version'], defaults['belapi_endpoint'])
        bel_obj.parse(statement)  # Adds ast to bel_obj
        bel_obj.orthologize('TAX:10090')  # Run orthologize before canonicalize if needed, updates bel_obj.ast and returns self
        bel_obj.canonicalize()  # updates bel_obj.ast and returns self

        computed_edges = bel_obj.computed()

        primary_edge = bel_obj.ast.to_components()

    """

    # TODO - don't provide defaults - was a bad idea

    def __init__(self, version: str = defaults['bel_version'], endpoint: str = defaults['belapi_endpoint']) -> None:
        """Initialize BEL object used for validating/processing/etc BEL statements

        Args:
            version (str): BEL Version, defaults to bel_lang.defaults.defaults['bel_version']
            endpoint (str): BEL API endpoint,  defaults to bel_lang.defaults.defaults['belapi_endpoint']
        """

        bel_versions = bel_specification.get_bel_versions()

        # use bel_utils._default_to_version to check if valid version, and if it exists or not
        self.version = bel_utils._default_to_version(version, bel_versions)

        if self.version == '':
            log.error('Cannot continue with invalid version. Exiting.')
            sys.exit()
        
        self.endpoint = endpoint

        # Validation error/warning messages
        # List[Tuple[str, str]], e.g. [('ERROR', 'this is an error msg'), ('WARNING', 'this is a warning'), ]
        self.validation_messages = []

        # self.semantics = BELSemantics()  # each instance also instantiates a BELSemantics object used in parsing statements
        self.spec = bel_specification.get_specification(self.version)

        # bel_utils._dump_spec(self.spec)

        # Import Tatsu parser
        # use importlib to import our parser (a .py file) and set the BELParse object as an instance variable
        try:
            imported_parser_file = importlib.import_module(self.spec['parser_path'])
            self.parser = imported_parser_file.BELParser()
        except Exception as e:
            # if not found, we raise the NoParserFound exception which can be found in bel_lang.exceptions
            raise bel_ex.NoParserFound(self.version)

    def parse(self, statement: str, strict: bool = False, parseinfo: bool = False) -> 'BEL':
        """Parse and semantically validate BEL statement

        Parses a BEL statement given as a string and returns an AST, Abstract Syntax Tree (defined in ast.py)
        if the statement is valid, self.parse_valid. Else, the AST attribute is None and there will be validation error messages
        in self.validation_messages.  self.validation_messages will contain WARNINGS if
        warranted even if the statement parses correctly.

        Args:
            statement (str): BEL statement
            strict (bool): specify to use strict or loose parsing; defaults to loose
            parseinfo (bool): specify whether or not to include Tatsu parse information in AST

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
            self.validation_messages.append(('ERROR', 'Please include a valid BEL statement.'))
            return self

        try:
            # see if an AST is returned without any parsing errors
            ast_dict = self.parser.parse(self.bel_stmt, rule_name='start', trace=False, parseinfo=parseinfo)

            self.ast = bel_lang_ast.ast_dict_to_objects(ast_dict, self)

            self.parse_valid = True

        except FailedParse as e:
            # if an error is returned, send to handle_syntax, error
            error, visualize_error = bel_utils.handle_parser_syntax_error(e)
            self.parse_visualize_error = visualize_error
            self.validation_messages.append(('ERROR', error))
            self.ast = None

        except Exception as e:
            log.error('Error {}, error type: {}'.format(e, type(e)))
            self.validation_messages.append(('ERROR', 'Error {}, error type: {}'.format(e, type(e))))

        # Run semantics validation - and decorate AST with nsarg entity_type and arg optionality
        semantics.validate(self)

        return self

    def syntax_parse(self, statement: str, strict: bool = False, parseinfo: bool = False) -> 'BEL':
        """Syntax parse - does not semantically validate

        Parses a BEL statement given as a string and returns a AST object.  self.parse_valid
        is True if a valid syntax parse.  self.validation_messages will show
        any ERRORS or WARNINGS.

        This method can be used for BEL Edge parsing in order to alter the statement
        format (short, medium, long).

        Args:
            statement (str): BEL statement
            strict (bool): specify to use strict or loose parsing; defaults to loose
            parseinfo (bool): specify whether or not to include Tatsu parse information in AST

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
            self.validation_messages.append(('ERROR', 'Please include a valid BEL statement.'))
            return self

        try:
            # see if an AST is returned without any parsing errors
            ast_dict = self.parser.parse(self.bel_stmt, rule_name='start', trace=False, parseinfo=parseinfo)

            self.ast = bel_lang_ast.ast_dict_to_objects(ast_dict, self)

            self.parse_valid = True

        except FailedParse as e:
            # if an error is returned, send to handle_syntax, error
            error, visualize_error = bel_utils.handle_parser_syntax_error(e)
            self.parse_visualize_error = visualize_error
            self.validation_messages.append(('ERROR', error))
            self.ast = None

        except Exception as e:
            log.error('Error {}, error type: {}'.format(e, type(e)))
            self.validation_messages.append(('ERROR', 'Error {}, error type: {}'.format(e, type(e))))

        return self

    def canonicalize(self, namespace_targets: Mapping[str, List[str]] = None) -> 'BEL':
        """
        Takes an AST and returns a canonicalized BEL statement string.

        Args:
            namespace_targets (Mapping[str, List[str]]): override default canonicalization
                settings of BEL.bio API endpoint - see {endpoint}/status to get default canonicalization settings

        Returns:
            BEL: returns self
        """

        # TODO Need to order position independent args

        canonicalize_endpoint = self.endpoint + '/terms/{}/canonicalized'

        self.ast = bel_utils.convert_namespaces(self.ast, canonicalize_endpoint, namespace_targets=namespace_targets)
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

        decanonicalize_endpoint = self.endpoint + '/terms/{}/decanonicalized'

        self.ast = bel_utils.convert_namespaces(self.ast, decanonicalize_endpoint, namespace_targets=namespace_targets)
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

    def compute_edges(self, rules: List[str] = None, fmt="medium") -> List[Mapping[str, Any]]:
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

        edges = []
        for es, er, eo in edges_ast:

            # Some components are not part of AST - e.g. NSArg
            if isinstance(es, bel_lang_ast.Function):
                es = es.to_string(fmt='medium')
            if isinstance(eo, bel_lang_ast.Function):
                eo = eo.to_string(fmt='medium')

            edges.append({'subject': es, 'relation': er, 'object': eo})

        return edges

    def completion(self, partial: str, component_type: str, value_type: str, fmt='medium') -> List[Tuple[str, str, str]]:
        """Suggest bel statement completions

        Takes a partially completed function, modifier function, or a relation and suggest a fuzzy match out of
        all available options filtering by context, e.g.:

           - functions if in function context
           - nsarg filtered by entity_type based on surrounding function, etc

        Args:
            partial (str): the partial string
            component_type (str): ['subject', 'relation', 'object']
            value_type (str): value type (function, modifier function, or relation; makes sure we match right list)
            fmt (str): short, medium or long form of function/relationship names to be returned

        Returns:
            List[Tuple[str, str, str]]: A list of suggested values as tuples
        """

        # (
        #     'matched string - highlighted',
        #     'canonical_match_value',
        #     'full field replacement with match',
        #     'cursor_location'
        # )

        # matched string - synonym, short/long name, etc that is matched, matched string wrapped
        #     in <em></em>
        # canonical_match_value - name/value to insert
        # full field replacement - the full string to replace in the text field being completed
        # cursor location - updated location of the cursor - placed in appropriate spot
        #     of suggested string (e.g. just inside new function, at beginning
        #     of object text field if completing relation, after , or ')' if
        #     completing a function argument)

        # TODO - issue #51

        suggestions = []
        # # TODO: get the following list of things - initialize YAML into this library so we can grab all funcs,
        # # mfuncs, and r.
        # if value_type == 'function':
        #     suggestions = []
        #
        # elif value_type == 'mfunction':
        #     suggestions = []
        #
        # elif value_type == 'relation':
        #     suggestions = []
        #
        # else:
        #     suggestions = []

        return suggestions

    def relation_list(self, fmt: str ="long") -> List[str]:
        """Return relation list for this BEL Version in the requested format

        Args:
            fmt (str): format of relation name: long, medium or short (abbreviation)

        Returns:
            List[str]: list of relation names in requested format
        """

        if fmt == 'short':
            return [self.spec['relations'][relation]['abbreviation'] for relation in self.spec['relations']]
        else:
            return [relation for relation in self.spec['relations']]


