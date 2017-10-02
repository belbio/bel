#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
This file contains helper objects.
"""


class Function(object):

    def __init__(self, type, name, alternate, args):
        self.type = type
        self.name = name
        self.alternate_name = alternate
        self.args = args

    def __str__(self):

        return self.name

class NSParam(object):
