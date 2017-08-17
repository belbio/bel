class InvalidParameter(Exception):
    def __init__(self, message):
        self.message = message


class ParameterMissing(Exception):
    def __init__(self, message):
        self.message = message


class NoValidSignature(Exception):
    def __init__(self, message):
        self.message = message


class InvalidRelationship(Exception):
    def __init__(self, message):
        self.message = message


class MissingParenthesis(Exception):
    def __init__(self, message):
        self.message = message


class NoParserFound(Exception):
    def __init__(self, version):
        self.message = 'No parser found for BEL v{}!'.format(version)
