import importlib
import os
import pprint
import requests
import sys
import glob
from typing import Mapping, Any, List

import yaml
from tatsu.ast import AST
from tatsu.exceptions import FailedParse
import traceback
import time

from bel_lang.exceptions import NoParserFound
from bel_lang.semantics import BELSemantics
from bel_lang.tools import ParseObject
import bel_lang.tools as tools
from bel_lang.defaults import defaults

import logging
log = logging.getLogger(__name__)

sys.path.append('../')


def get_bel_versions() -> List[str]:
    """Get BEL Language versions supported

    Get the list of all BEL Language versions supported.

    Returns:
        List[str]: list of versions
    """

    files = glob.glob('{}/versions/bel_v*.yaml'.format(os.path.dirname(__file__)))
    versions = []
    for fn in files:
        yaml_dict = yaml.load(open(fn, 'r').read())
        versions.append(yaml_dict['version'])

    return versions


class BEL(object):
    """BEL Language object

    To convert BEL Statement to BEL Edges:

        statement = "p(HGNC:AKT1) increases p(HGNC:EGF)"
        bel_obj = bel_lang.BEL(defaults['bel_version'], defaults['belapi_endpoint'])
        bel_obj.parse(statement)  # Adds ast to bel_obj
        bel_obj.orthologize('TAX:10090')  # Run orthologize before canonicalize if needed, updates bel_obj.ast and returns self
        bel_obj.canonicalize()  # updates bel_obj.ast and returns self

        computed_edges = bel_obj.computed()

        primary_edge = bel_obj.ast.to_components()

    """

    def __init__(self, version: str = defaults['bel_version'], endpoint: str = defaults['belapi_endpoint']) -> None:
        """Initialize BEL object used for validating/processing/etc BEL statements

        Args:
            version (str): BEL Version, defaults to bel_lang.defaults.defaults['bel_version']
            endpoint (str): BEL API endpoint,  defaults to bel_lang.defaults.defaults['belapi_endpoint']
        """

        bel_versions = get_bel_versions()
        if version not in bel_versions:
            log.error('Version {} not available in bel_lang library package'.format(version))
            sys.exit()

        self.version = version
        self.endpoint = endpoint
        self.messages = []  # List[Tuple[str, str]], e.g. [('ERROR', 'this is an error msg'), ('WARNING', 'this is a warning'), ]

        # use this variable to find our parser file since periods aren't recommended in file names
        self.version_dots_as_underscores = version.replace('.', '_')

        # each instance also instantiates a BELSemantics object used in parsing statements
        self.semantics = BELSemantics()

        # get the current directory name, and use that to find the version's parser file location
        cur_dir_name = os.path.basename(os.path.dirname(os.path.realpath(__file__)))
        parser_dir = '{}.versions.parser_v{}'.format(cur_dir_name, self.version_dots_as_underscores)

        # use importlib to import our parser (a .py file) and set the BELParse object as an instance variable
        try:
            imported_parser_file = importlib.import_module(parser_dir)
            self.parser = imported_parser_file.BELParser()
        except Exception as e:
            # if not found, we raise the NoParserFound exception which can be found in bel_lang.exceptions
            raise NoParserFound(version)

        # try to load the version's YAML dictionary as well for functions like _create()
        # set this BEL instance's relationships, signatures, term translations, etc.
        try:
            current_stored_dir = os.path.dirname(__file__)
            yaml_file_name = 'versions/bel_v{}.yaml'.format(self.version_dots_as_underscores)
            yaml_file_path = '{}/{}'.format(current_stored_dir, yaml_file_name)
            self.yaml_dict = yaml.load(open(yaml_file_path, 'r').read())

            self.translate_terms = tools.func_name_translate(self)  # this killed a kitten :(
            self.relationships = tools.get_all_relationships(self)
            self.function_signatures = tools.get_all_function_signatures(self)

            self.primary_functions = tools.get_all_primary_funcs(self)
            self.modifier_functions = tools.get_all_modifier_funcs(self)

            self.computed_sigs = tools.get_all_computed_sigs(self)
            self.computed_funcs = tools.get_all_computed_funcs(self)
            self.computed_mfuncs = tools.get_all_computed_mfuncs(self)

            # print(self.computed_sigs.keys())
            # print('COMPUTED SIGS FUNCTIONS')
            # print(self.computed_funcs)
            # print('COMPUTED SIGS M_FUNCTIONS')
            # print(self.computed_mfuncs)

        except Exception as e:
            # print(e)
            # traceback.print_exc()
            # print('Warning: Version {} YAML not found. Some functions will not work correctly.'.format(self.version))
            log.error('Warning: BEL Specification for Version {} YAML not found. Cannot proceed.'.format(self.version))
            sys.exit()

    def parse(self, statement: str, strict: bool = False, parseinfo: bool = False) -> 'BEL':
        """
        Parses a BEL statement given as a string and returns a ParseObject, which contains an abstract syntax tree (
        AST) if the statement is valid. Else, the AST attribute is None and there will be exception messages in
        ParseObject.error and ParseObject.visual_err.

        Args:
            statement (str): BEL statement
            strict (bool): specify to use strict or loose parsing; defaults to loose
            parseinfo (bool): specify whether or not to include Tatsu parse information in AST

        Returns:
            ParseObject: The ParseObject which contain either an AST or error messages.
        """

        self.ast = None
        self.valid = False
        self.visualize_error = ''
        self.messages = []  # Reset messages when parsing a new BEL Statement

        self.original_bel_stmt = statement
        # pre-process to remove extra white space, add space after commas, etc.
        self.bel_stmt = tools.preprocess_bel_line(statement)

        # Check to see if empty string for bel statement
        if len(self.bel_stmt) == 0:
            self.messages.append(('ERROR', 'Please include a valid BEL statement.'))
            return self

        try:
            # see if an AST is returned without any parsing errors
            ast_dict = self.parser.parse(self.bel_stmt, rule_name='start', semantics=self.semantics, trace=False, parseinfo=parseinfo)

            import json
            print('DumpVar:\n', json.dumps(ast_dict, indent=4))

            self.ast = tools.ast_dict_to_objects(ast_dict, self)
            self.valid = True

        except FailedParse as e:
            # if an error is returned, send to handle_syntax, error
            error, visualize_error = tools.handle_syntax_error(e)

            self.visualize_error = visualize_error
            self.messages.append(('ERROR', error))
            self.ast = None

        except Exception as e:
            log.error('Error {}, error type: {}'.format(e, type(e)))
            self.messages.append(('ERROR', 'Error {}, error type: {}'.format(e, type(e))))

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

        # TODO Need to order position independent parameters

        canonicalize_endpoint = self.endpoint + '/terms/{}/canonicalized'

        self.ast = tools.convert_namespaces(self.ast, canonicalize_endpoint, namespace_targets=namespace_targets)
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

        self.ast = tools.convert_namespaces(self.ast, decanonicalize_endpoint, namespace_targets=namespace_targets)
        return self

    def orthologize(self, species_id: str) -> 'BEL':
        """Orthologize BEL AST to given species_id

        Will return original entity (ns:value) if no ortholog found.

        Args:
            species_id (str): species id to convert genes/rna/proteins into

        Returns:
            BEL: returns self
        """

        orthologize_req_url = self.endpoint + '/orthologs/{}/' + species_id
        self.ast = tools.orthologize(self.ast, orthologize_req_url)
        return self

    def computed(self, rule_set: List[str] = None) -> List[Mapping[str, Any]]:
        """Computed edges from primary BEL statement

        Takes an AST and generates all computed edges based on BEL Specification YAML computed signatures.
        Will run only the list of computed edge rules if given.

        Args:
            rule_set (list): a list of rules to filter; only the rules in this list will be applied to computed

        Returns:
            List[Mapping[str, Any]]
        """

        edges = tools.compute(self.ast.bel_subject, self, rule_set)
        edges.extend(tools.compute(self.ast.bel_object, self, rule_set))

        return edges

    def suggest(self, partial: str, value_type: str):
        """
        Takes a partially completed function, modifier function, or a relationship and suggest a fuzzy match out of
        all available options.

        Args:
            partial (str): the partial string
            value_type (str): value type (function, modifier function, or relationship; makes sure we match right list)

        Returns:
            list: A list of suggested values.
        """

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
        # elif value_type == 'relationship':
        #     suggestions = []
        #
        # else:
        #     suggestions = []

        return suggestions

    def ast_components(self, ast: AST):
        """
        Returns the components of a BEL AST as values within a dictionary under the keys 'subject', 'relationship',
        and 'object'.

        Args:
            ast (AST): BEL AST

        Returns:
            dict: The dictionary that contains the components as its values.
        """

        # TODO - what is this for?  Issue #49  Doesn't seem to be needed

        components_dict = dict()
        components_dict['subject'] = ast.get('subject', None)

        # if a relationship exists, this means that an object must also exist
        if ast.get('relationship', None) is not None:
            components_dict['object'] = ast.get('object', None)
            components_dict['relationship'] = ast.get('relationship', None)

        return components_dict

    def flatten(self, ast: AST):
        """
        Takes an AST and flattens it into a BEL statement string.

        Args:
            ast (AST): BEL AST

        Returns:
            str: The string generated from the AST.
        """

        # TODO Doesn't seem to be needed

        # grab the three components of the AST
        s = ast.get('subject', None)
        r = ast.get('relationship', None)
        o = ast.get('object', None)

        # if no relationship, this means only subject is present
        if r is None:
            sub = tools.decode(s)
            final = '{}'.format(sub)
        # else the full form BEL statement with subject, relationship, and object are present
        else:
            sub = tools.decode(s)
            obj = tools.decode(o)
            final = '{} {} {}'.format(sub, r, obj)

        return final

    def _create(self, count: int = 1, max_params: int = 3):
        """
        Creates a specified number of invalid BEL statement objects for testing purposes.

        Args:
            count (int): the number of statements to create; defaults to 1
            max_params (int): max number of params each function can take (a large number may exceed recursive depth)

        Returns:
            list: A list of InvalidStatementObject objects.
        """

        # statements will be inside objects, so we need a new list for those
        list_of_bel_stmt_objs = []

        # if user specifies < 1 test statements, do as he/she wishes and return an empty list
        if count < 1:
            return list_of_bel_stmt_objs

        return tools.create_invalid(self, count, max_params)

    def load(self, filename: str, loadn: int = -1, preprocess: bool = False):
        """
        Reads a text file of BEL statements separated by newlines, and returns an array of the BEL statement strings.

        Args:
            filename (str): location/name of the text file
            loadn (int): how many statements to load from the file. If unspecified, all are loaded
            preprocess (bool): denote whether or not to run each statement through the preprocessor

        Returns:
            list: The list of statement strings.
        """

        # create an empty list to put our loaded statements
        statements = []

        # open the file that we're loading statements off of
        f = open(filename)
        line_count = 0

        # for each statement in our file (each statement should be on a newline)
        for line in f:
            if line_count == loadn:  # once number of lines processed equals user specified, stop
                break

            if preprocess:  # if preprocess if selected, clean up the statement string
                line = tools.preprocess_bel_line(line)
            else:
                line = line.strip()

            statements.append(line)
            line_count += 1

        # close the file and return the list
        f.close()

        return statements

    def wm_computed_edges(self, rule_set: List[str] = None) -> List[Mapping[str, Any]]:
        """Computed edges from primary BEL statement

        Takes an AST and generates all computed edges based on BEL Specification YAML computed signatures.
        Will run only the list of computed edge rules if given.

        Args:
            rule_set (list): a list of rules to filter; only the rules in this list will be applied to computed

        Returns:
            List[Mapping[str, Any]]
        """

        computed_signatures = yaml.loads("""
  component_of:
    trigger_type:
      - Function
      - NSParam
    subject: trigger_value
    relation: componentOf
    object: parent_function
    examples:
      - given_statement: "act(complex(SCOMP:\"PP2A Complex\"), ma(GO:\"phosphatase activity\"))"
        computed:
          - "complex(SCOMP:\"PP2A Complex\") componentOf act(complex(SCOMP:\"PP2A Complex\"), ma(GO:\"phosphatase activity\"))"
          - "SCOMP:\"PP2A Complex\" componentOf complex(SCOMP:\"PP2A Complex\")"
          - "GO:\"phosphatase activity\" componentOf act(complex(SCOMP:\"PP2A Complex\"), ma(GO:\"phosphatase activity\"))"

  degradation:
    trigger_function: degradation
    subject: trigger_value
    relation: directlyDecreases
    object: args
    examples:
      - given_statement: "deg(r(HGNC:MYC))"
        computed:
          - "deg(r(HGNC:MYC)) directlyDecreases r(HGNC:MYC)"

        """)

        compute_rules = self.bel_specification.get('computed_signatures')

        if rule_set:
            compute_rules = [rule for rule in compute_rules if rule in rule_set]

        edges = tools.compute_edges(self, rule_set)

        return edges


def wm_compute_edges(ast, compute_rules):

    from bel_lang.objects import Function

    computed_edges = []

    for rule in compute_rules:
        function_name, args, parent_function = None, None, None, None

        if isinstance(ast, Function):
            function_name = ast.name  # TODO - this should be the canonical function name not randomly abbr or long form
            args = ast.args
            parent_function = ast.parent_function

        trigger_functions = rule.get('trigger_function', None)
        trigger_types = rule.get('trigger_type', None)

        if function_name in trigger_functions:  # trigger_functions is a list of canonical function names from bel_specification
            rule_subject_value = rule.get('subject')
            if rule_subject_value == 'trigger_value':
                subject = ast

            relation = rule.get('relation')

            rule_object_value = rule.get('object')
            if rule_object_value == 'args':
                for arg in args:
                    computed_edges.extend((subject, relation, arg))
            elif rule_object_value == 'parent_function':
                computed_edges.extend((subject, relation, parent_function))

        if isinstance(ast, trigger_types):
            rule_subject_value = rule.get('subject')
            if rule_subject_value == 'trigger_value':
                subject = ast

            relation = rule.get('relation')

            rule_object_value = rule.get('object')
            if rule_object_value == 'parent_function':
                computed_edges.extend((subject, relation, parent_function))
