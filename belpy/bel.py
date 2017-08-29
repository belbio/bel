 import importlib
import os

from tatsu.exceptions import FailedParse
from tatsu.ast import AST

import sys

sys.path.append('../')

from belpy.semantics import BELSemantics
from belpy.tools import TestBELStatementGenerator, ValidationObject, ParseObject
from belpy.tools import preprocess_bel_line, handle_syntax_error, decode, compute
from belpy.exceptions import NoParserFound


class BEL(object):

    def __init__(self, version: str, endpoint: str):
        """The BEL class contains the version and endpoint, and all functions needed to work with statements.

        Args:
            version (:obj:`str`): BEL language version specific to this instance.
            endpoint (:obj:`str`): URI of TermStore endpoint specific to this instance.
        """

        self.version = version
        self.endpoint = endpoint

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
            # if not found, we raise the NoParserFound exception which can be found in belpy.exceptions
            raise NoParserFound(version)


    def parse(self, statement: str, strict: bool = False):
        """
        Parses a BEL statement given as a string and returns a ParseObject, which contains an abstract syntax tree (
        AST) if the statement is valid. Else, the AST attribute is None and there will be exception messages in
        ParseObject.error and ParseObject.visual_err.

        Args:
            statement (str): BEL statement
            strict (bool): specify to use strict or loose parsing; defaults to loose

        Returns:
            ParseObject: The ParseObject which contain either an AST or error messages.
        """

        ast = None
        error = None
        err_visual = None

        if statement == '':
            error = 'Please include a valid BEL statement.'
            return ParseObject(ast, error, err_visual)

        statement = preprocess_bel_line(statement)

        try:
            ast = self.parser.parse(statement, rule_name='start', semantics=self.semantics, trace=False,
                                    parseinfo=False)
        except FailedParse as e:
            error, err_visual = handle_syntax_error(e)
        except Exception as e:
            print(e)
            print(type(e))

        return ParseObject(ast, error, err_visual)

    def stmt_components(self, statement: str):
        """
        Returns the components of a BEL statement as values within a dictionary under the keys 'subject',
        'relationship', and 'object'.

        Args:
            statement (str): BEL statement

        Returns:
            dict: The dictionary that contains the components as its values.
        """

        components_dict = dict.fromkeys(['object', 'relationship', 'subject'])
        p = self.parse(statement)
        ast = p.ast

        if ast is None:
            components_dict['object'] = None
            components_dict['relationship'] = None
            components_dict['subject'] = None
            print(p.error)
            print(p.err_visual)
        else:
            components_dict['object'] = ast.get('object', None)
            components_dict['relationship'] = ast.get('relationship', None)
            components_dict['subject'] = ast.get('subject', None)

        return components_dict

    def ast_components(self, ast: AST):
        """
        Returns the components of a BEL AST as values within a dictionary under the keys 'subject', 'relationship',
        and 'object'.

        Args:
            ast (AST): BEL AST

        Returns:
            dict: The dictionary that contains the components as its values.
        """

        components_dict = {}
        components_dict['subject'] = ast.get('subject', None)

        if ast.get('relationship', None) is not None:
            components_dict['object'] = ast.get('object', None)
            components_dict['relationship'] = ast.get('relationship', None)

        return components_dict

    def _create(self, count: int = 1, max_params: int = 3):
        """
        Creates a specified number of invalid BEL statement objects for testing purposes.

        Args:
            count (int): the number of statements to create; defaults to 1
            max_params (int): max number of params each function can take (a large number may exceed recursive depth)

        Returns:
            list: A list of BEL statement objects.
        """

        list_of_bel_stmt_objs = []

        # if user specifies < 1 test statements, do as he/she wishes
        if count < 1:
            return list_of_bel_stmt_objs

        generator = TestBELStatementGenerator(version=self.version)

        for _ in range(count):  # each loop makes one invalid statement
            s = generator.make_statement(max_params)
            list_of_bel_stmt_objs.append(s)

        return list_of_bel_stmt_objs

    def flatten(self, ast: AST):
        """
        Takes an AST and flattens it into a BEL statement string.

        Args:
            ast (AST): BEL AST

        Returns:
            str: The string generated from the AST.
        """
        s = ast.get('subject', None)
        r = ast.get('relationship', None)
        o = ast.get('object', None)

        if r is None:  # if no relationship, this means only subject is present
            sub = decode(s)
            final = '{}'.format(sub)
        else:  # else the full form BEL statement with subject, relationship, and object are present
            sub = decode(s)
            obj = decode(o)
            final = '{} {} {}'.format(sub, r, obj)

        return final

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
        stmts = []

        f = open(filename)
        lcount = 0

        for line in f:

            if lcount == loadn:  # once number of lines processed equals user specified, then stop
                break

            if preprocess:
                line = preprocess_bel_line(line)
            else:
                line = line.strip()

            stmts.append(line)
            lcount += 1

        f.close()

        return stmts

    def validate(self, statement: str, strict: bool = False):
        """
        Validates a BEL statement and returns a ValidationObject.

        Args:
            statement (str): BEL statement
            strict (bool): specify to use strict or loose parsing; defaults to loose

        Returns:
            ValidationObject: The ValidationObject which contain either an AST or error messages, and valid boolean.

        """

        # TODO: strict/loose validation
        p = self.parse(statement)

        if p.ast is None:
            valid = False
        else:
            valid = True

        return ValidationObject(p.ast, p.error, p.err_visual, valid)

    def suggest(self, partial: str, value_type: str):
        """
        Takes a partially completed function, modifier function, or a relationship and suggest a fuzzy match out of
        all available options.

        Args:
            partial (str): the partial string
            value_type (str): value type (function, modifier function, or relationship; makes sure we match with right list)

        Returns:
            list: A list of suggested values.
        """

        suggestions = []
        # TODO: get the following list of things - initialize YAML into this library so we can grab all funcs,
        # mfuncs, and r.
        if value_type == 'function':
            suggestions = []

        elif value_type == 'mfunction':
            suggestions = []

        elif value_type == 'relationship':
            suggestions = []

        else:
            suggestions = []

        return suggestions

    def canonicalize(self, ast: AST):
        # TODO: this definition
        """
        Takes an AST and returns a canonicalized BEL statement string.

        Args:
            ast (AST): BEL AST

        Returns:
            str: The canonicalized string generated from the AST.
        """

    def computed(self, ast: AST):
        # TODO: this definition
        """
        Takes an AST and computes all canonicalized edges.

        Args:
            ast (AST): BEL AST

        Returns:
            list:  List of canonicalized computed edges to load into the EdgeStore.
        """


        list_of_computed = []

        s = ast.get('subject', None)
        o = ast.get('object', None)

        if o is None:  # if no object, this means only subject is present
            compute_list = compute(s)
            list_of_computed.extend(compute_list)
        else:  # else the full form BEL statement with subject, relationship, and object are present
            compute_list_subject = compute(s)
            compute_list_object = compute(o)
            list_of_computed.extend(compute_list_subject)
            list_of_computed.extend(compute_list_object)

        return sorted(list(set(list_of_computed)))





