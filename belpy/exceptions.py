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