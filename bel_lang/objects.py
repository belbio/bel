#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
This file contains helper objects.
"""

########################
# BEL statement object #
########################


class BELStatement(object):

    def __init__(self, bel_subject, bel_relationship, bel_object):
        self.bel_subject = bel_subject
        self.bel_relationship = bel_relationship
        self.bel_object = bel_object

    def __str__(self):
        return '{} {} {}'.format(self.bel_subject, self.bel_relationship, self.bel_object)


class BELSubject(object):

    def __init__(self, fn=None, bel_statement=None):
        self.fn = fn
        self.bel_statement = bel_statement


class BELRelationship(object):

    def __init__(self, relationship):
        self.relationship = relationship


class BELObject(object):

    def __init__(self, fn=None, bel_statement=None):
        self.fn = fn
        self.bel_statement = bel_statement

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


class StrParam(Param):

    def __init__(self, value, parent_function):
        Param.__init__(self, parent_function)
        self.value = value
