# Local Imports
# Third Party
import pytest

# Local
import bel.lang.parse
from bel.lang.ast import BELAst
from bel.schemas.bel import Pair

# TODO test reading in a string from a file doesn't remove the escape backslash


def test_ordered_pairs():
    """Matching left, right pairs of characters"""

    left = [10, 20, 40, 50, 70]
    right = [11, 21, 31, 51, 71, 81, 91, 101]

    correct = [
        Pair(start=10, end=11),
        Pair(start=20, end=21),
        Pair(start=None, end=31),
        Pair(start=40, end=None),
        Pair(start=50, end=51),
        Pair(start=70, end=71),
        Pair(start=None, end=81),
        Pair(start=None, end=91),
        Pair(start=None, end=101),
    ]

    result = bel.lang.parse.ordered_pairs(left, right)

    print("Result", result)

    assert correct == result


def test_matching_quotes1():

    assertion_str = 'complex(SCOMP:"Test named" complex", p(HGNC:"207"!"AKT1 Test), p(HGNC:207!"Test"), loc(X)) increases p(HGNC:EGF) increases p(hgnc : "here I am" ! X)'

    errors = []
    (matched_quotes, errors) = bel.lang.parse.find_matching_quotes(assertion_str, errors)

    print("Errors", errors)
    print("Quotes", matched_quotes)

    assert (
        errors[0].msg
        == "Missing right quote after left quote at position 50 and before position 74"
    )
    assert errors[0].severity == "Error"

    assert matched_quotes[0].start == 14
    assert matched_quotes[0].end == 34

    assert matched_quotes[2].start == 50
    assert matched_quotes[2].end is None

    assert matched_quotes[4].start == 132
    assert matched_quotes[4].end == 142


def test_matching_quotes2():

    assertion_str = 'p(HGNC:"AKT1'

    errors = []
    (matched_quotes, errors) = bel.lang.parse.find_matching_quotes(assertion_str, errors)

    print("Errors", errors)
    print("Quotes", matched_quotes)

    assert (
        errors[0].msg == "Missing right quote after left quote at position 7 and before position 12"
    )


def test_matching_quotes3():

    assertion_str = 'p(HGNC:"AKT1")'

    errors = []
    (matched_quotes, errors) = bel.lang.parse.find_matching_quotes(assertion_str, errors)

    print("Errors", errors)
    print("Quotes", matched_quotes)

    assert errors == []


def test_commas():

    assertion_str = 'complex(SCOMP:"Test named" complex", p(HGNC:"207"!"AKT1 Test), p(HGNC:207!"Test"), loc(X)) increases p(HGNC:EGF) increases p(hgnc : "here I am" ! X)'

    errors = []

    (matched_quotes, errors) = bel.lang.parse.find_matching_quotes(assertion_str, errors)
    (commas, errors) = bel.lang.parse.find_commas(assertion_str, matched_quotes, errors)

    print("Commas", commas)

    assert commas == [35, 61, 81]


def test_matching_parens():

    assertion_str = 'complex(SCOMP:"Test named" complex", p(HGNC:"207"!"AKT1 Test"), p(HGNC:207!"Test"), loc(X)) increases p(HGNC:EGF) equivalentTo p(hgnc : "here I am" ! X))'

    errors = []
    (matched_quotes, errors) = bel.lang.parse.find_matching_quotes(assertion_str, errors)
    (matched_parens, errors) = bel.lang.parse.find_matching_parens(
        assertion_str, matched_quotes, errors
    )

    print("Errors", errors)
    print("Quotes", matched_parens)

    assert errors[0].msg == "Too many close parentheses at index 152"
    assert errors[0].severity == "Error"

    assert matched_parens[0].start == 7
    assert matched_parens[0].end == 90
    assert matched_parens[1].start == 38
    assert matched_parens[1].end == 61


def test_relations():

    assertion_str = 'complex(SCOMP:"Test named" complex", p(HGNC:"207"!"AKT1 Test), p(HGNC:207!"Test"), loc(X)) increases p(HGNC:EGF) equivalentTo p(hgnc : "here I am" ! X)'

    errors = []
    (matched_quotes, errors) = bel.lang.parse.find_matching_quotes(assertion_str, errors)
    version = "latest"
    (relations, errors) = bel.lang.parse.find_relations(
        assertion_str, matched_quotes, errors, version
    )

    print("Relations", relations)

    assert relations[0].span_str == "increases"
    assert relations[1].span_str == "equivalentTo"
    assert relations[1].start == 113


def test_functions():

    assertion_str = (
        r'complex(p(HGNC:AKT1!"Test label", pmod(X))) increases act(p(HGNC:AKT1), ma(kin))'
    )

    errors = []
    (matched_quotes, errors) = bel.lang.parse.find_matching_quotes(assertion_str, errors)
    (matched_parens, errors) = bel.lang.parse.find_matching_parens(
        assertion_str, matched_quotes, errors
    )

    version = "latest"
    (functions, errors) = bel.lang.parse.find_functions(
        assertion_str, matched_quotes, matched_parens, errors, version
    )

    for fn in functions:
        print("FN", fn, "\n")

    assert functions[0].span_str == 'complex(p(HGNC:AKT1!"Test label", pmod(X)))'
    assert functions[0].start == 0
    assert functions[0].end == 43
    assert functions[0].name.span_str == "complex"
    assert functions[2].span_str == "pmod(X)"
    assert functions[5].span_str == "ma(kin)"
    assert functions[3].start == 54
    assert functions[3].end == 80


def test_find_nsargs():

    assertion_str = 'complex(SCOMP:"Test named complex", p(HGNC:"207"!"AKT1 Test"), p(HGNC:207!"Test"), loc(X)) increases p(HGNC:EGF) increases p(hgnc : "here I am" ! X)'

    ns_arg_spans = bel.lang.parse.find_nsargs(assertion_str)

    print("NS Args")
    for nsarg in ns_arg_spans:
        print(nsarg, "\n")

    assert ns_arg_spans[0].start == 8
    assert ns_arg_spans[0].end == 34
    assert ns_arg_spans[0].span_str == 'SCOMP:"Test named complex"'
    assert ns_arg_spans[0].type == "ns_arg"

    assert ns_arg_spans[3].start == 103
    assert ns_arg_spans[3].end == 111
    assert ns_arg_spans[3].span_str == "HGNC:EGF"
    assert ns_arg_spans[3].type == "ns_arg"
    assert ns_arg_spans[3].namespace.span_str == "HGNC"
    assert ns_arg_spans[3].label is None


def test_find_strings():

    version = "latest"

    # assertion_str = "  stuff  "

    assertion_str = 'complex(SCOMP:"Test named complex", p(HGNC:"207"!"AKT1 Test"), p(HGNC:207!"Test"), loc(nucleus)) increases p(HGNC:EGF) increases p(hgnc : "here I am" ! X) decreases stuff here '

    errors = []
    (matched_quotes, errors) = bel.lang.parse.find_matching_quotes(assertion_str, errors)
    (matched_parens, errors) = bel.lang.parse.find_matching_parens(
        assertion_str, matched_quotes, errors
    )
    (commas, errors) = bel.lang.parse.find_commas(assertion_str, matched_quotes, errors)
    (relations, errors) = bel.lang.parse.find_relations(
        assertion_str, matched_quotes, errors, version
    )
    (functions, errors) = bel.lang.parse.find_functions(
        assertion_str, matched_quotes, matched_parens, errors, version
    )
    nsargs = bel.lang.parse.find_nsargs(assertion_str)

    components = relations + functions + nsargs

    string_spans = bel.lang.parse.find_strings(assertion_str, components)

    print("String spans", string_spans)

    assert string_spans[0].start == 87
    assert string_spans[0].end == 94
    assert string_spans[0].span_str == "nucleus"
    assert string_spans[0].type == "string_arg"

    assert string_spans[1].start == 165
    assert string_spans[1].end == 175
    assert string_spans[1].span_str == "stuff here"
    assert string_spans[1].type == "string"
