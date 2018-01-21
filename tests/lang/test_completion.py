import pytest
import json

import bel.lang.completion
import bel.utils

from bel.Config import config


def test_completion_fn_name_start_long():

    completions = bel.lang.completion.bel_completion('pa', bel_fmt='medium')
    print('Completions:\n', json.dumps(completions, indent=4))
    assert completions["completion_text"] == "pa"
    assert completions['completions'][0]['replacement'] == 'path()'
    assert completions['completions'][0]['cursor_loc'] == 5
    assert completions['entity_spans'] == []
    assert completions['function_help'] == []


def test_completion_fn_name_start_medium():

    completions = bel.lang.completion.bel_completion('pa', bel_fmt='long')
    print('Completions:\n', json.dumps(completions, indent=4))
    assert completions["completion_text"] == "pa"
    assert completions['completions'][0]['replacement'] == 'pathology()'
    assert completions['completions'][0]['cursor_loc'] == 10
    assert completions['entity_spans'] == []
    assert completions['function_help'] == []


def test_completion_fn_name_start_medium_2():

    completions = bel.lang.completion.bel_completion('path()', cursor_loc=1, bel_fmt='long')
    print('Completions:\n', json.dumps(completions, indent=4))
    assert completions["completion_text"] == "pa"
    assert completions['completions'][0]['replacement'] == 'pathology()'
    assert completions['completions'][0]['cursor_loc'] == 9
    assert completions['entity_spans'] == []
    assert completions['function_help'] == []


def test_completion_arg_fn():

    completions = bel.lang.completion.bel_completion('complex(pro(HGNC:EGFR))', cursor_loc=10, bel_fmt='long')
    print('Completions:\n', json.dumps(completions, indent=4))
    assert completions["completion_text"] == "pro"
    assert completions['completions'][0]['replacement'] == "complex(proteinAbundance(HGNC:EGFR))"
    assert completions['completions'][0]['cursor_loc'] == 24
    assert completions['entity_spans'] == []
    assert completions['function_help'] != []


def test_completion_arg_fn_2():

    completions = bel.lang.completion.bel_completion('complex(p(HGNC:EGFR))', cursor_loc=8, bel_fmt='medium')
    print('Completions:\n', json.dumps(completions, indent=4))
    assert completions["completion_text"] == "p"
    assert completions['completions'][0]['replacement'] == "complex(p(HGNC:EGFR))"
    assert completions['completions'][0]['cursor_loc'] == 9
    assert completions['entity_spans'] == []
    assert completions['function_help'] != []


def test_completion_arg_ns_prefix():

    if bel.utils.get_url(f"{config['bel_api']['servers']['api_url']}/simple_status").status_code != 200:
        pytest.xfail('BEL.bio API Test environment is not setup')

    completions = bel.lang.completion.bel_completion('complex(p(HGNC:EGFR))', cursor_loc=18, bel_fmt='medium')
    print('Completions:\n', json.dumps(completions, indent=4))
    assert completions["completion_text"] == "EGFR"
    assert completions['completions'][0]['replacement'] == "complex(p(HGNC:EGFR))"
    assert completions['completions'][0]['cursor_loc'] == 19
    assert completions['entity_spans'] == []
    assert completions['function_help'] != []


def test_completion_arg_ns_val():

    if bel.utils.get_url(f"{config['bel_api']['servers']['api_url']}/simple_status").status_code != 200:
        pytest.xfail('BEL.bio API Test environment is not setup')

    completions = bel.lang.completion.bel_completion('complex(p(HGNC:EGFR))', cursor_loc=12, bel_fmt='medium')
    print('Completions:\n', json.dumps(completions, indent=4))
    assert completions["completion_text"] == "HGN"
    assert completions['completions'][0]['replacement'] == "complex(p(HGNC:IDNK))"
    assert completions['completions'][0]['cursor_loc'] == 19
    assert completions['entity_spans'] == []
    assert completions['function_help'] != []


def test_completion_arg_StrArgNSArg_1():

    completions = bel.lang.completion.bel_completion('complex(p(HGNC:EGFR, pmod(pa)))', cursor_loc=26, bel_fmt='medium')
    print('Completions:\n', json.dumps(completions, indent=4))
    assert completions["completion_text"] == "p"
    assert completions['completions'][0]['replacement'] == "complex(p(HGNC:EGFR, pmod(Ph)))"
    assert completions['completions'][0]['cursor_loc'] == 28
    assert completions['entity_spans'] == []
    assert completions['function_help'] != []


def test_completion_arg_StrArgNSArg_2():

    completions = bel.lang.completion.bel_completion('complex(p(HGNC:EGFR, pmod(pa)))', cursor_loc=27, bel_fmt='medium')
    print('Completions:\n', json.dumps(completions, indent=4))
    assert completions["completion_text"] == "pa"
    assert completions['completions'][0]['replacement'] == "complex(p(HGNC:EGFR, pmod(Palm)))"
    assert completions['completions'][0]['cursor_loc'] == 30
    assert completions['entity_spans'] == []
    assert completions['function_help'] != []


def test_completion_relation_end():

    completions = bel.lang.completion.bel_completion('complex(p(HGNC:EGFR, pmod(pa))) inc', bel_fmt='medium')
    print('Completions:\n', json.dumps(completions, indent=4))
    assert completions["completion_text"] == "inc"
    assert completions['completions'][0]['replacement'] == "complex(p(HGNC:EGFR, pmod(pa))) increases"
    assert completions['completions'][0]['cursor_loc'] == 41
    assert completions['entity_spans'] == []
    assert completions['function_help'] == []


def test_completion_relation_end_short():

    completions = bel.lang.completion.bel_completion('complex(p(HGNC:EGFR, pmod(pa))) ->', bel_fmt='short')
    print('Completions:\n', json.dumps(completions, indent=4))
    assert completions["completion_text"] == "->"
    assert completions['completions'][0]['replacement'] == "complex(p(HGNC:EGFR, pmod(pa))) ->"
    assert completions['completions'][0]['cursor_loc'] == 34
    assert completions['entity_spans'] == []
    assert completions['function_help'] == []


def test_completion_relation_end_short_cursorloc():

    completions = bel.lang.completion.bel_completion('complex(p(HGNC:EGFR, pmod(pa))) -> ', cursor_loc=32, bel_fmt='short')
    print('Completions:\n', json.dumps(completions, indent=4))
    assert ["--", "->", "-|"] == sorted([c['label'] for c in completions["completions"]])
    assert ["complex(p(HGNC:EGFR, pmod(pa))) -> "] == [c['replacement'] for c in completions["completions"] if c['replacement'] == "complex(p(HGNC:EGFR, pmod(pa))) -> "]
    assert completions['completions'][0]['cursor_loc'] == 34
    assert completions['entity_spans'] == []
    assert completions['function_help'] == []


def test_completion_nested_relation_end():

    completions = bel.lang.completion.bel_completion('complex(p(HGNC:EGFR, pmod(pa))) increases (p(HGNC:EGF) dec', bel_fmt='medium')
    print('Completions:\n', json.dumps(completions, indent=4))
    assert completions["completion_text"] == "dec"
    assert completions['completions'][0]['replacement'] == "complex(p(HGNC:EGFR, pmod(pa))) increases (p(HGNC:EGF) decreases"
    assert completions['completions'][0]['cursor_loc'] == 64
    assert completions['entity_spans'] == []
    assert completions['function_help'] == []


def test_completion_nested_relation():

    completions = bel.lang.completion.bel_completion('complex(p(HGNC:EGFR, pmod(pa))) increases (p(HGNC:EGF) decreases p(HGNC:AKT1))', cursor_loc=60, bel_fmt='medium')
    print('Completions:\n', json.dumps(completions, indent=4))
    assert completions["completion_text"] == "decrea"
    assert completions['completions'][0]['replacement'] == "complex(p(HGNC:EGFR, pmod(pa))) increases (p(HGNC:EGF) decreases p(HGNC:AKT1))"
    assert completions['completions'][0]['cursor_loc'] == 64
    assert completions['entity_spans'] == []
    assert completions['function_help'] == []
