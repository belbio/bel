import bel_lang
from bel_lang.defaults import defaults

bel_obj = bel_lang.BEL(defaults['bel_version'], defaults['belapi_endpoint'])


def test_empty_string():

    statement = ''
    bel_obj.parse(statement)

    assert bel_obj.ast is None
    assert 'Please include a valid BEL statement.' in bel_obj.validation_messages[0][1]


def test_bad_string_start():

    statement = '$$!@$'
    bel_obj.parse(statement)

    assert bel_obj.ast is None
    assert 'Failed parse at position 0.' in bel_obj.validation_messages[0][1]

# def test_whitespace_string():
#
#     statement = 'a('
#     parse_obj = bel_obj.parse(statement)
#
#     print(parse_obj.error)
#     assert isinstance(parse_obj, ParseObject)
#     assert parse_obj.ast is None
#     assert parse_obj.error == 'Please include a valid BEL statement.'

