class InvalidParameter(Exception):
    def __init__(self, message):
        self.message = message


class ParameterMissing(Exception):
    def __init__(self, function):
        self.message = 'There are no parameters given to {}().'.format(function)


class NoValidSignature(Exception):
    def __init__(self, message):
        self.message = message


class InvalidRelationship(Exception):
    def __init__(self, given_r):
        self.message = '\"{}\" is not a defined relationship.'.format(given_r)


class MissingParenthesis(Exception):
    def __init__(self, message):
        self.message = message


class MissingQuotation(Exception):
    def __init__(self, message):
        self.message = message


class NoParserFound(Exception):
    def __init__(self, version):
        self.message = 'No parser found for BEL v{}!'.format(version)
