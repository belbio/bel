import belpy
import pytest
from belpy.exceptions import *
from belpy.tools import ParseObject

B = belpy.BEL('2.0.0', 'example-endpoint')

def test_empty_string():

    statement = ''
    parse_obj = B.parse(statement)

    assert isinstance(parse_obj, ParseObject)
    assert parse_obj.ast is None
    assert parse_obj.error == 'Please include a valid BEL statement.'

def test_bad_string_start():

    statement = '$$!@$'
    parse_obj = B.parse(statement)

    assert isinstance(parse_obj, ParseObject)
    assert parse_obj.ast is None
    assert 'Failed parse at position 0.' in parse_obj.error

def test_whitespace_string():

    statement = 'a('
    parse_obj = B.parse(statement)

    print(parse_obj.error)
    assert isinstance(parse_obj, ParseObject)
    assert parse_obj.ast is None
    assert parse_obj.error == 'Please include a valid BEL statement.'

test_whitespace_string()
