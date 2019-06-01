import pytest

import bel.lang.belobj
import bel.lang.bel_utils

from bel.Config import config
import bel.Config

bo = bel.lang.belobj.BEL(
    config["bel"]["lang"]["default_bel_version"], config["bel_api"]["servers"]["api_url"]
)

# TODO Add test for specified canonical_targets - need to make sure BEL.bio API endpoint is updated to handle this querystring arg

# TODO Add test for 'act(p(HGNC:BCR, fus(HGNC:ABL1)), ma(kin)) directlyIncreases p(HGNC:CBL, pmod(Ph, Y, 700))'  (bad fusion())


def test_convert_nsarg():
    """Test embedded forward slash"""

    nsarg = 'SCOMP:"p85/p110 PI3Kinase Complex"'

    expected_nsarg = 'SCOMP:"p85/p110 PI3Kinase Complex"'

    canon_nsarg = bel.lang.bel_utils.convert_nsarg(nsarg)

    assert canon_nsarg == expected_nsarg


@pytest.mark.skip(reason="Missing namespace info")
def test_canon_one():

    statement = 'act(p(HGNC:AKT1), ma(GO:"kinase activity"))'

    expected = 'activity(proteinAbundance(EG:207), molecularActivity(GO:"kinase activity"))'

    bo.parse(statement)

    bo.canonicalize()

    print(f"Result {bo.ast.to_string(fmt='long')}")

    assert bo.ast.to_string(fmt="long") == expected


@pytest.mark.skip(reason="Missing namespace info")
def test_canon_two():

    statement = 'act(p(HGNC:MYD88), ma(GO:"catalytic activity")) directlyIncreases complex(p(HGNC:MYD88),p(HGNC:IRAK1),p(HGNC:IRAK4))'

    expected = 'activity(proteinAbundance(EG:4615), molecularActivity(GO:"catalytic activity")) directlyIncreases complexAbundance(proteinAbundance(EG:4615), proteinAbundance(EG:3654), proteinAbundance(EG:51135))'

    bo.parse(statement)

    bo.canonicalize()

    assert bo.ast.to_string(fmt="long") == expected


@pytest.mark.skip(reason="Missing namespace info")
def test_canon_nested():

    statement = 'act(p(HGNC:MYD88), ma(GO:"catalytic activity")) directlyIncreases (complex(p(HGNC:MYD88), p(HGNC:IRAK1), p(HGNC:IRAK4)) directlyIncreases complex(p(HGNC:MYD88), p(HGNC:IRAK1), p(HGNC:IRAK4)))'

    expected = 'activity(proteinAbundance(EG:4615), molecularActivity(GO:"catalytic activity")) directlyIncreases (complexAbundance(proteinAbundance(EG:4615), proteinAbundance(EG:3654), proteinAbundance(EG:51135)) directlyIncreases complexAbundance(proteinAbundance(EG:4615), proteinAbundance(EG:3654), proteinAbundance(EG:51135)))'

    bo.parse(statement)

    bo.canonicalize()

    assert bo.ast.to_string(fmt="long") == expected


@pytest.mark.skip(reason="Missing namespace info")
def test_canonicalization():
    """Test canonicalization of assertion"""

    assertion = "p(SP:P31749) increases act(p(HGNC:EGF))"
    correct = "p(EG:207) increases act(p(EG:1950))"
    result = bo.parse(assertion).canonicalize().to_string()
    print("Canonicalized assertion", result)

    assert correct == result


@pytest.mark.skip(
    reason="Skip until we update BEL parsing with the partial parser instead of Tatsu"
)
def test_canonicalization_NSArg():
    """Test canonicalization of plain NSArg"""

    assertion = "HGNC:IL6"
    correct = "EG:3569"
    result = bo.parse(assertion).canonicalize().to_string()
    print("Canonicalized assertion", result)

    assert correct == result


@pytest.mark.skip(reason="Missing namespace info")
def test_decanon_one():

    statement = 'act(p(EG:207), ma(GO:"kinase activity"))'

    expected = 'activity(proteinAbundance(HGNC:AKT1), molecularActivity(GO:"kinase activity"))'

    bo.parse(statement)

    bo.decanonicalize()

    assert bo.ast.to_string(fmt="long") == expected


@pytest.mark.skip(reason="Missing namespace info")
def test_decanon_two():

    statement = 'act(p(EG:4615), ma(GO:"catalytic activity")) directlyIncreases complex(p(EG:4615), p(EG:3654), p(EG:51135))'

    expected = 'activity(proteinAbundance(HGNC:MYD88), molecularActivity(GO:"catalytic activity")) directlyIncreases complexAbundance(proteinAbundance(HGNC:MYD88), proteinAbundance(HGNC:IRAK1), proteinAbundance(HGNC:IRAK4))'

    bo.parse(statement)

    bo.decanonicalize()

    assert bo.ast.to_string(fmt="long") == expected


@pytest.mark.skip(reason="Missing namespace info")
def test_decanon_nested():

    statement = 'act(p(EG:4615), ma(GO:"catalytic activity")) directlyIncreases (complex(p(EG:4615), p(EG:3654), p(EG:51135)) directlyIncreases complexAbundance(p(EG:4615), p(EG:3654), p(EG:51135)))'

    expected = 'activity(proteinAbundance(HGNC:MYD88), molecularActivity(GO:"catalytic activity")) directlyIncreases (complexAbundance(proteinAbundance(HGNC:MYD88), proteinAbundance(HGNC:IRAK1), proteinAbundance(HGNC:IRAK4)) directlyIncreases complexAbundance(proteinAbundance(HGNC:MYD88), proteinAbundance(HGNC:IRAK1), proteinAbundance(HGNC:IRAK4)))'

    bo.parse(statement)

    bo.decanonicalize()

    assert bo.ast.to_string(fmt="long") == expected


@pytest.mark.skip(reason="Missing namespace info")
def test_decanonicalization():
    """Test canonicalization of assertion"""

    assertion = "p(EG:207) increases act(p(EG:1950))"
    correct = "p(HGNC:AKT1) increases act(p(HGNC:EGF))"

    result = bo.parse(assertion).decanonicalize().to_string()
    print("deCanonicalized assertion", result)

    assert correct == result

    assertion = "p(SP:P31749) increases act(p(HGNC:EGF))"
    correct = "p(HGNC:AKT1) increases act(p(HGNC:EGF))"

    result = bo.parse(assertion).decanonicalize().to_string()
    print("deCanonicalized assertion", result)

    assert correct == result
