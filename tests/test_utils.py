# Standard Library
import re

# Local Imports
import bel.utils as utils


def test_first_true():

    test1 = [False, 1, "2", None]
    test2 = [None, "", "2", None]
    test3 = [None, False, ""]

    result = utils.first_true(test1)
    assert result == 1

    result = utils.first_true(test2)
    assert result == "2"

    # Result is the default value '3'
    result = utils.first_true(test3, "3")
    assert result == "3"


def test_create_hash():

    h = utils._create_hash("test")
    assert h == "8581389452482819506"


def test_generate_id():

    _id = utils._generate_id()
    assert re.match("\w{26,26}", str(_id))
