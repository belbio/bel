import bel.lang
from bel.Config import config

bel_obj = bel.lang.bel.BEL(config['bel']['lang']['default_bel_version'], config['bel_api']['servers']['api_url'])


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

