# Standard Library
import json
import pprint

# Local Imports
import bel.lang.ast
import bel.lang.completion
from bel.lang.ast import BELAst
from bel.schemas.bel import AssertionStr, BelCompletion, BelFunctionHelp
from colorama import Fore

# def test_find_cursor_match():

#     assertion_str = "p(HGNC:AKT1)"
#     # assertion_str = 'complex(SCOMP:"Test named\" complex", p(HGNC:"207"!"AKT1 Test"), p(HGNC:207!"Test"), loc(nucleus)) increases p(HGNC:EGF) increases p(hgnc : "here I am" ! X)'

#     ast = bel.lang.ast.BELAst(assertion_str)

#     cursor = 8

#     r = bel.lang.completion.find_cursor_match(ast, cursor)

#     print("Results", r)

#     assert False


def test_highlighting():

    search_str = "test"
    match = "testmatch"
    expected = "<em>test</em>match"

    result = bel.lang.completion.highlight_match(search_str, match)
    print("Result", result)

    assert result == expected

    search_str = "test"
    match = "TEstmatch"
    expected = "<em>TEst</em>match"

    result = bel.lang.completion.highlight_match(search_str, match)
    print("Result", result)

    assert result == expected


def test_namespace_completions():

    search_str = "hg"
    expected = [
        BelCompletion(
            replacement="HGNC:", label="HGNC", highlight="<em>HG</em>NC", type="Namespace",
        )
    ]

    matches = bel.lang.completion.get_namespace_completions(search_str)
    print("Matches", matches)

    assert matches == expected

    search_str = "nc"
    expected = []

    matches = bel.lang.completion.get_namespace_completions(search_str)
    print("Matches", matches)

    assert matches == expected


def test_strarg_completions():

    search_str = "leu"

    expected = [
        BelCompletion(
            replacement="Leu",
            label="Leu [AminoAcid]",
            highlight="<em>Leu</em>",
            type="StrArg",
            cursor=0,
            entity_types=None,
            replacement_type=None,
        ),
        BelCompletion(
            replacement="Ile",
            label="Isoleucine [AminoAcid]",
            highlight="Iso<em>leu</em>cine",
            type="StrArg",
            cursor=0,
            entity_types=None,
            replacement_type=None,
        ),
    ]

    matches = bel.lang.completion.get_strarg_completions(search_str, ["AminoAcid"])
    print("Matches", matches)

    assert matches == expected


def test_function_completions():

    search_str = "act"

    expected = [
        BelCompletion(
            replacement="act",
            label="act()",
            highlight="<em>act</em>",
            type="Function",
            cursor=0,
            entity_types=None,
            replacement_type=None,
        ),
        BelCompletion(
            replacement="rxn",
            label="rxn()",
            highlight="re<em>act</em>ion",
            type="Function",
            cursor=0,
            entity_types=None,
            replacement_type=None,
        ),
        BelCompletion(
            replacement="reactants",
            label="reactants()",
            highlight="re<em>act</em>ants",
            type="Function",
            cursor=0,
            entity_types=None,
            replacement_type=None,
        ),
        BelCompletion(
            replacement="ma",
            label="ma()",
            highlight="molecular<em>Act</em>ivity",
            type="Function",
            cursor=0,
            entity_types=None,
            replacement_type=None,
        ),
    ]

    matches = bel.lang.completion.get_function_completions(search_str)

    print("Matches", matches)

    assert matches == expected

    expected = [
        BelCompletion(
            replacement="activity",
            label="activity()",
            highlight="<em>act</em>",
            type="Function",
            cursor=0,
            entity_types=None,
            replacement_type=None,
        ),
        BelCompletion(
            replacement="reaction",
            label="reaction()",
            highlight="re<em>act</em>ion",
            type="Function",
            cursor=0,
            entity_types=None,
            replacement_type=None,
        ),
        BelCompletion(
            replacement="reactants",
            label="reactants()",
            highlight="re<em>act</em>ants",
            type="Function",
            cursor=0,
            entity_types=None,
            replacement_type=None,
        ),
        BelCompletion(
            replacement="molecularActivity",
            label="molecularActivity()",
            highlight="molecular<em>Act</em>ivity",
            type="Function",
            cursor=0,
            entity_types=None,
            replacement_type=None,
        ),
    ]

    matches = bel.lang.completion.get_function_completions(search_str, bel_format="long")

    print("Matches", matches)

    assert matches == expected

    search_str = "ro"

    function_subset = [
        "geneAbundance",
        "rnaAbundance",
        "microRNAAbundance",
        "proteinAbundance",
        "complexAbundance",
    ]

    expected = [
        BelCompletion(
            replacement="p",
            label="p()",
            highlight="p<em>ro</em>teinAbundance",
            type="Function",
            cursor=0,
            entity_types=None,
            replacement_type=None,
        ),
        BelCompletion(
            replacement="m",
            label="m()",
            highlight="mic<em>ro</em>RNAAbundance",
            type="Function",
            cursor=0,
            entity_types=None,
            replacement_type=None,
        ),
    ]

    matches = bel.lang.completion.get_function_completions(
        search_str, function_subset=function_subset, bel_format="medium"
    )

    print("Matches", matches)

    assert matches == expected


def test_relation_completions():

    search_str_lc = "an"
    expected = [
        BelCompletion(
            replacement="analogous()",
            label="analogous()",
            highlight="<em>an</em>alogous",
            type="Relation",
            cursor=0,
            entity_types=None,
            replacement_type=None,
        ),
        BelCompletion(
            replacement=">>()",
            label=">>()",
            highlight="tr<em>an</em>slatedTo",
            type="Relation",
            cursor=0,
            entity_types=None,
            replacement_type=None,
        ),
        BelCompletion(
            replacement=":>()",
            label=":>()",
            highlight="tr<em>an</em>scribedTo",
            type="Relation",
            cursor=0,
            entity_types=None,
            replacement_type=None,
        ),
        BelCompletion(
            replacement="cnc()",
            label="cnc()",
            highlight="causesNoCh<em>an</em>ge",
            type="Relation",
            cursor=0,
            entity_types=None,
            replacement_type=None,
        ),
    ]

    matches = bel.lang.completion.get_relation_completions(search_str_lc, bel_format="medium")

    print("Matches", matches)

    assert matches == expected

    search_str_lc = "->"
    expected = [
        BelCompletion(
            replacement="->()",
            label="->()",
            highlight="<em>-></em>",
            type="Relation",
            cursor=0,
            entity_types=None,
            replacement_type=None,
        )
    ]

    matches = bel.lang.completion.get_relation_completions(search_str_lc, bel_format="medium")

    print("Matches", matches)

    assert matches == expected


def test_nsarg_completions():

    search_str = "AKT"

    expected = [
        BelCompletion(
            replacement="HGNC:391!AKT1",
            label="HGNC:391!AKT1",
            highlight="<em>AKT1</em>",
            type="NSArg",
            cursor=0,
            entity_types=None,
            replacement_type=None,
        ),
        BelCompletion(
            replacement="HGNC:392!AKT2",
            label="HGNC:392!AKT2",
            highlight="<em>AKT2</em>",
            type="NSArg",
            cursor=0,
            entity_types=None,
            replacement_type=None,
        ),
    ]

    matches = bel.lang.completion.get_nsarg_completions(
        search_str, entity_types=["Protein"], species_keys=["TAX:9606"], size=2,
    )

    print("Matches", matches)

    assert matches == expected


def test_find_cursor_match():
    """Find cursor match in Assertion AST - full assertion"""

    completion_str = "p(HGNC:AKT1, pmod(Ph, Ser))"
    assertion = AssertionStr(entire=completion_str)
    ast = BELAst(assertion=assertion)

    expected = {"1": ""}

    for i in range(len(completion_str) + 1):
        cursor = i
        (arg, position, search_str) = bel.lang.completion.find_cursor_match(ast.args, cursor)
        expected = ("proteinAbundance()", 0, "")

        std_color = Fore.WHITE
        if position is None:
            color = Fore.RED
            position = "None"
        else:
            color = std_color

        print(
            f"{color}Cursor: {cursor:3d} Position: {position:4} Search: {search_str:15s} ",
            f"{Fore.GREEN}Pre:{color} {completion_str[0:cursor]:20s}  {Fore.GREEN}Arg:{color} ",
            f"{str(arg):25s}  {Fore.GREEN}Parent:{color} {arg.parent} {std_color}\n",
        )

        if cursor == 26:
            assert position == 2
            assert str(arg) == "proteinModification(Ph, Ser)"


def test_find_cursor_match2():
    """Find cursor match in Assertion AST with missing paren"""

    completion_str = "p(HGNC:AKT1, ma(kin)"
    assertion = AssertionStr(entire=completion_str)
    ast = BELAst(assertion=assertion)

    for i in range(len(completion_str) + 1):
        cursor = i
        (arg, position, search_str) = bel.lang.completion.find_cursor_match(ast.args, cursor)
        expected = ("proteinAbundance()", 0, "")

        std_color = Fore.WHITE
        if position is None:
            color = Fore.RED
            position = "None"
        else:
            color = std_color

        print(
            f"{color}Cursor: {cursor:3d} Position: {position:4} Search: {search_str:15s} ",
            f"{Fore.GREEN}Pre:{color} {completion_str[0:cursor]:20s}  {Fore.GREEN}Arg:{color} ",
            f"{str(arg):25s}  {Fore.GREEN}Parent:{color} {arg.parent} {std_color}\n",
        )

        if cursor == 20:
            assert position == 1
            assert str(arg) == "molecularActivity(kin)"


def test_get_function_help():

    completion_str = "p(HGNC:AKT1)"
    assertion = AssertionStr(entire=completion_str)
    ast = BELAst(assertion=assertion)

    expected = [
        BelFunctionHelp(
            function_summary="proteinAbundance(NSArg, loc|frag()?, var|pmod()*)",
            argument_help=[
                "Namespace argument of following type(s): Protein",
                "Zero or one of each function(s): location, fragment",
                "Zero or more of each function(s): variant, proteinModification",
            ],
            description="Denotes the abundance of a protein",
        ),
        BelFunctionHelp(
            function_summary="proteinAbundance(fus(), loc()?, var()*)",
            argument_help=[
                "One of following function(s): fusion",
                "Zero or one of each function(s): location",
                "Zero or more of each function(s): variant",
            ],
            description="Denotes the abundance of a protein",
        ),
    ]

    result = bel.lang.completion.get_function_help(ast.args[0].args[0])

    print("Help", result)

    assert result == expected


def test_completion_replace_nsarg():
    """Provide ns:id!label formatted nsarg"""

    completion_str = "p(HGNC:AKT1)"
    cursor = 10
    species_keys = ["TAX:9606"]

    completion_response = bel.lang.completion.bel_completion(
        completion_str, cursor=cursor, species_keys=species_keys
    )

    completion_response.to_print()

    assert completion_response.completions[0].replacement == "p(HGNC:391!AKT1)"


def test_completion_function_context():

    completion_str = "p("
    cursor = 2
    species_keys = ["TAX:9606"]

    completion_response = bel.lang.completion.bel_completion(
        completion_str, species_keys=species_keys
    )

    # completion_response.to_print()

    print("Response", completion_response)
    print("First completion", completion_response.completions[0].dict())

    assert completion_response.completions[0].dict() == {
        "replacement": "p(fus())",
        "label": "fus()",
        "highlight": "fus",
        "type": "Function",
        "cursor": 5,
    }


def test_completion_nsarg():

    completion_str = "p(akt1"
    cursor = 4
    species_keys = ["TAX:9606"]

    completion_response = bel.lang.completion.bel_completion(
        completion_str, species_keys=species_keys
    )

    completion_response.to_print()

    assert completion_response.completions[0].replacement == "p(EG:207!AKT1)"


def test_completion_string():

    completion_str = "pop(huma"
    species_keys = ["TAX:9606"]

    completion_response = bel.lang.completion.bel_completion(
        completion_str, species_keys=species_keys
    )

    completion_response.to_print()

    assert completion_response.completions[0].replacement == "pop(TAX:9606!human)"


def test_completion_modifier():

    completion_str = "p(HGNC:391!AKT1, "
    species_keys = ["TAX:9606"]

    completion_response = bel.lang.completion.bel_completion(
        completion_str, species_keys=species_keys
    )

    completion_response.to_print()

    assert completion_response.completions[0].replacement == "p(HGNC:391!AKT1, loc())"


def test_completion_pmod():

    # TODO - problem with the completion context  line 485 in completion.py

    completion_str = "p(HGNC:391!AKT1, pmo"
    # looking for pmod()

    cursor = 20
    species_keys = ["TAX:9606"]

    completion_response = bel.lang.completion.bel_completion(
        completion_str, cursor=cursor, species_keys=species_keys
    )

    completion_response.to_print()

    assert completion_response.completions[0].replacement == "p(HGNC:391!AKT1, pmod())"


def test_completion_pmod_arg1():

    completion_str = "p(HGNC:391!AKT1, pmod(P"
    # Looking for Ph for phosphorylation

    cursor = 23
    species_keys = ["TAX:9606"]

    completion_response = bel.lang.completion.bel_completion(
        completion_str, cursor=cursor, species_keys=species_keys
    )

    completion_response.to_print()

    assert completion_response.completions[0].replacement == "p(HGNC:391!AKT1, pmod(Ph))"


def test_completion_pmod_arg2():

    completion_str = "p(HGNC:391!AKT1, pmod(Ph, S"
    # Looking for Ser for Serine
    cursor = 27
    species_keys = ["TAX:9606"]

    completion_response = bel.lang.completion.bel_completion(
        completion_str, cursor=cursor, species_keys=species_keys
    )

    completion_response.to_print()

    assert completion_response.completions[0].replacement == "p(HGNC:391!AKT1, pmod(Ph, Ser))"


def test_completion_pmod_arg3():

    completion_str = "p(HGNC:391!AKT1, pmod(Ph, "
    # Looking for Ser for Serine
    cursor = 27
    species_keys = ["TAX:9606"]

    completion_response = bel.lang.completion.bel_completion(
        completion_str, cursor=cursor, species_keys=species_keys
    )

    completion_response.to_print()

    assert completion_response.completions[0].replacement == "p(HGNC:391!AKT1, pmod(Ph, Ala))"


def test_completion_raw_string():
    """This really breaks the completion engine"""

    completion_str = "a"
    species_keys = ["TAX:9606"]

    completion_response = bel.lang.completion.bel_completion(
        completion_str, species_keys=species_keys
    )

    completion_response.to_print()

    assert completion_response.completions[0].replacement == "a()"

    completion_str = "zero"
    species_keys = ["TAX:9606"]

    completion_response = bel.lang.completion.bel_completion(
        completion_str, species_keys=species_keys
    )

    completion_response.to_print()

    assert completion_response.completions[0].replacement == 'MESH:D018993!"Myelin P0 Protein"'
