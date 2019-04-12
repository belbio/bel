import bel

SPECIFIED_VERSION = "2.0.0"
SPECIFIED_VERSION_UNDERLINED = "2_0_0"

SPECIFIED_ENDPOINT = "example-endpoint"

bel_obj = bel.BEL(version=SPECIFIED_VERSION, api_url=SPECIFIED_ENDPOINT)

######################
# INITIAL TEST CASES #
######################


# def test_semantic_class_instance():
#     assert isinstance(bel_obj.semantics, bel.lang.semantics.BELSemantics)


def test_correct_instantiation():
    assert bel_obj.version == SPECIFIED_VERSION
    assert bel_obj.api_url == SPECIFIED_ENDPOINT
