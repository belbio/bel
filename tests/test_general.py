import belpy
import pytest
from belpy.exceptions import *

SPECIFIED_VERSION = '2.0.0'
SPECIFIED_VERSION_UNDERLINED = '2_0_0'

SPECIFIED_ENDPOINT = 'example-endpoint'

B = belpy.BEL(SPECIFIED_VERSION, SPECIFIED_ENDPOINT)

######################
# INITIAL TEST CASES #
######################


def test_semantic_class_instance():
    assert isinstance(B.semantics, belpy.semantics.BELSemantics)


def test_correct_instantiation():
    assert B.version == SPECIFIED_VERSION
    assert B.endpoint == SPECIFIED_ENDPOINT
    assert B.version_dots_as_underscores == SPECIFIED_VERSION_UNDERLINED
