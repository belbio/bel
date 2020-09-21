# Local Imports
# Third Party
from bel.schemas.bel import AssertionStr, BelEntity, NsVal


def test_assertion_str():

    assertion = AssertionStr(subject=" hello", relation="there", object="world ")

    assert assertion.entire == "hello there world"

    # Does not update assertion.entire when SRO fields are altered
    assertion.entire = ""

    assertion.object = ""

    assert assertion.entire != "hello there"


def test_nsval():

    nsval = NsVal(namespace="HGNC", id="391", label="AKT1")

    assert nsval.key == "HGNC:391"
    assert str(nsval) == "HGNC:391!AKT1"

    assert nsval.db_key() == "HGNC:391"

    nsval = NsVal(namespace="TEST", id="show me", label="hello!world")

    assert nsval.key == 'TEST:"show me"'
    assert str(nsval) == 'TEST:"show me"!"hello!world"'
    assert nsval.db_key() == "TEST:_show_me_"

    nsval = NsVal(namespace="TEST", id='show me "hi" ', label="hello!world")

    assert nsval.key == 'TEST:"show me "hi""'
    assert str(nsval) == 'TEST:"show me "hi""!"hello!world"'
    assert nsval.db_key() == "TEST:_show_me_hi_"


def test_entity():

    entity = BelEntity("HGNC:AKT1")

    entity.normalize()

    assert entity.canonical.key == "EG:207"
    assert entity.decanonical.key == "HGNC:391"

    entity.all()
    assert entity.species_key == "TAX:9606"
    assert str(entity.orthologs["TAX:10116"]["decanonical"]) == "RGD:2081!Akt1"


def test_entity_fake():

    nsval = NsVal(namespace="TEST", id="hello world", label="testing")

    entity = BelEntity(nsval=nsval).normalize()

    expected = "TEST:_hello_world_"

    db_key = entity.canonical.db_key()

    assert db_key == expected

    entity = BelEntity("TBD:MyGene")

    entity.normalize()

    assert entity.canonical.key == "TBD:MyGene"
