class InvalidArgeter(Exception):
    def __init__(self, message):
        self.message = message


class ArgeterMissing(Exception):
    def __init__(self, function):
        self.message = "There are no args given to {}().".format(function)


class NoValidSignature(Exception):
    def __init__(self, message):
        self.message = message


class InvalidRelationship(Exception):
    def __init__(self, given_r):
        self.message = '"{}" is not a defined relation.'.format(given_r)


class MissingParenthesis(Exception):
    def __init__(self, message):
        self.message = message


class InvalidCharacter(Exception):
    def __init__(self, message):
        self.message = message


class MissingQuotation(Exception):
    def __init__(self, message):
        self.message = message


class NoParserFound(Exception):
    def __init__(self, version):
        self.message = "No parser found for BEL v{}!".format(version)
