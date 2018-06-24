import bel.lang.belobj
from bel.Config import config

bo = bel.lang.belobj.BEL(config['bel']['lang']['default_bel_version'], config['bel_api']['servers']['api_url'])


def test_empty_string():

    statement = ''
    bo.parse(statement)

    assert bo.ast is None
    assert 'Please include a valid BEL statement - found empty string.' in bo.validation_messages[0][1]


def test_bad_string_start():

    statement = '$$!@$'
    bo.parse(statement)

    assert bo.ast is None
    assert 'Failed parse at position 0.' in bo.validation_messages[0][1]

# def test_whitespace_string():
#
#     statement = 'a('
#     parse_obj = bo.parse(statement)
#
#     print(parse_obj.error)
#     assert isinstance(parse_obj, ParseObject)
#     assert parse_obj.ast is None
#     assert parse_obj.error == 'Please include a valid BEL statement.'

