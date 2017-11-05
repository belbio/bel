#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
This file contains helper objects.
"""

########################
# BEL statement object #
########################


class BELAst(object):

    def __init__(self, bel_subject, bel_relationship, bel_object):
        self.bel_subject = bel_subject
        self.bel_relationship = bel_relationship
        self.bel_object = bel_object
        self.args = [bel_subject, bel_relationship, bel_object]

    def to_string(self):
        if self.bel_subject and self.bel_relationship and self.bel_object:
            return '{} {} {}'.format(self.bel_subject, self.bel_relationship, self.bel_object)

        elif self.bel_subject:
            return '{}'.format(self.bel_subject)

        else:
            return ''

    def to_components(self):
        if self.bel_subject and self.bel_relationship and self.bel_object:
            return {
                'subject': self.ast.bel_subject.to_string(),
                'relation': self.ast.bel_relationship.to_string(),
                'object': self.ast.bel_object.to_string(),
            }

        elif self.bel_subject:
            return {'subject': self.ast.bel_subject.to_string(), }

        else:
            return None

    def __str__(self):
        return self.to_string(self)


class BELSubject(object):

    def __init__(self, fn=None, bel_statement=None):
        self.fn = fn  # TODO What is this for?
        self.bel_statement = bel_statement  # TODO What is this for?

    def to_string(self):
        return '{}'.format(self.bel_subject)

    def __str__(self):
        return self.to_string(self)


class BELRelationship(object):

    def __init__(self, relationship):
        self.relationship = relationship

    def to_string(self):
        return '{}'.format(self.bel_relationship)

    def __str__(self):
        return self.to_string(self)


class BELObject(object):

    def __init__(self, fn=None, bel_statement=None):
        self.fn = fn
        self.bel_statement = bel_statement

    def to_string(self):
        return '{}'.format(self.bel_object)

    def __str__(self):
        return self.to_string(self)

###################
# Function object #
###################


class Function(object):

    def __init__(self, ftype, name, alternate, parent_function=None):
        self.ftype = ftype
        self.name = name
        self.alternate_name = alternate
        self.parent_function = parent_function
        self.full_string = ''

        self.args = []
        self.siblings = []

    def is_primary(self):
        if self.ftype == 'primary':
            return True
        return False

    def is_modifier(self):
        if self.ftype == 'modifier':
            return True
        return False

    def add_argument(self, arg):
        self.args.append(arg)

    def add_sibling(self, sibling):
        self.siblings.append(sibling)

    def change_type(self, new_type):
        self.ftype = new_type

    def set_full_string(self, string):
        self.full_string = string

    def __str__(self):
        arg_string = ', '.join([a.to_string() for a in self.args])
        return '{}({})'.format(self.name, arg_string)

    def to_string(self):

        arg_string = ', '.join([a.to_string() for a in self.args])
        return '{}({})'.format(self.name, arg_string)

#####################
# Parameter objects #
#####################


class Param(object):

    def __init__(self, parent_function):
        self.parent_function = parent_function
        self.siblings = []
        self.full_string = ''

    def add_sibling(self, sibling):
        self.siblings.append(sibling)

    def set_full_string(self, string):
        self.full_string = string


class NSParam(Param):

    def __init__(self, namespace, value, parent_function):
        Param.__init__(self, parent_function)
        self.namespace = namespace
        self.value = value

    def change_nsvalue(self, namespace, value):
        self.namespace = namespace
        self.value = value

    def to_string(self):
        return '{}:{}'.format(self.namespace, self.value)


class StrParam(Param):

    def __init__(self, value, parent_function):
        Param.__init__(self, parent_function)
        self.value = value

    def to_string(self):
        return '{}'.format(self.value)
