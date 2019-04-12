import bel.lang.bel_utils as bel_utils


def test_quoting_nsarg():

    test_arg = "AKT1"
    correct_arg = "AKT1"

    assert correct_arg == bel_utils.quoting_nsarg(test_arg)

    test_arg = '"AKT1"'
    correct_arg = "AKT1"

    assert correct_arg == bel_utils.quoting_nsarg(test_arg)

    test_arg = "help me"
    correct_arg = '"help me"'

    assert correct_arg == bel_utils.quoting_nsarg(test_arg)

    test_arg = "help)me"
    correct_arg = '"help)me"'

    assert correct_arg == bel_utils.quoting_nsarg(test_arg)

    test_arg = "help,me"
    correct_arg = '"help,me"'

    assert correct_arg == bel_utils.quoting_nsarg(test_arg)

    test_arg = '"help,me"'
    correct_arg = '"help,me"'

    assert correct_arg == bel_utils.quoting_nsarg(test_arg)
