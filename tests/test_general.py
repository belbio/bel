import bel_lang

SPECIFIED_VERSION = '2.0.0'
SPECIFIED_VERSION_UNDERLINED = '2_0_0'

SPECIFIED_ENDPOINT = 'example-endpoint'

bel_obj = bel_lang.BEL(SPECIFIED_VERSION, SPECIFIED_ENDPOINT)

######################
# INITIAL TEST CASES #
######################


# def test_semantic_class_instance():
#     assert isinstance(bel_obj.semantics, bel_lang.semantics.BELSemantics)


def test_correct_instantiation():
    assert bel_obj.version == SPECIFIED_VERSION
    assert bel_obj.endpoint == SPECIFIED_ENDPOINT
