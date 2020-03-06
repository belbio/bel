# Local Imports
import bel.lang.ast
import bel.lang.bel_utils
import bel.lang.belobj
import pytest
from bel.Config import config

bo = bel.lang.belobj.BEL(
    config["bel"]["lang"]["default_bel_version"], config["bel_api"]["servers"]["api_url"]
)


@pytest.mark.skip(reason="Missing namespace info")
def test_nsarg_normalization():
    """Test adding canonical, decanonical forms to NSArgs in BEL AST"""

    canonical = "EG:207"
    decanonical = "HGNC:AKT1"

    obj_canonical = "EG:1950"
    obj_decanonical = "HGNC:EGF"

    bo.parse("p(SP:P31749) increases p(SP:P01133)")
    bo.collect_nsarg_norms()

    print(bo.ast.bel_subject.args[0].canonical)
    print(bo.ast.bel_subject.args[0].decanonical)

    bo.print_tree()

    assert canonical == bo.ast.bel_subject.args[0].canonical
    assert decanonical == bo.ast.bel_subject.args[0].decanonical
    assert obj_canonical == bo.ast.bel_object.args[0].canonical
    assert obj_decanonical == bo.ast.bel_object.args[0].decanonical

    assert bo.ast.collected_nsarg_norms


@pytest.mark.skip(reason="Missing namespace info")
def test_nested_nsarg_normalization():
    """Test adding canonical, decanonical forms to nested bel stmt for NSArgs in BEL AST"""

    subj_canonical = "EG:207"
    subj_decanonical = "HGNC:AKT1"

    nested_subj_canonical = "EG:1950"
    nested_subj_decanonical = "HGNC:EGF"

    bo.parse("p(SP:P31749) increases (p(SP:P01133) decreases p(HGNC:ER))")
    bo.collect_nsarg_norms()

    print(bo.ast.bel_subject.args[0].canonical)
    print(bo.ast.bel_subject.args[0].decanonical)

    bo.print_tree()

    assert subj_canonical == bo.ast.bel_subject.args[0].canonical
    assert subj_decanonical == bo.ast.bel_subject.args[0].decanonical
    assert nested_subj_canonical == bo.ast.bel_object.bel_subject.args[0].canonical
    assert nested_subj_decanonical == bo.ast.bel_object.bel_subject.args[0].decanonical

    assert bo.ast.collected_nsarg_norms


@pytest.mark.skip(reason="Missing namespace info")
def test_appending_orthologs_to_nsargs():
    """Add orthologs to AST NSArgs for use in orthologization"""

    bo.parse("p(SP:P31749) increases p(SP:P01133)")
    bo.collect_orthologs(["TAX:9606", "TAX:10090", "TAX:10116"])

    print("Sub Orthologs", bo.ast.bel_subject.args[0].orthologs)
    print("Obj Orthologs", bo.ast.bel_object.args[0].orthologs)

    orthologs = bo.ast.bel_subject.args[0].orthologs
    assert orthologs["TAX:10116"]["decanonical"] == "RGD:Akt1"
    assert orthologs["TAX:10090"]["decanonical"] == "MGI:Akt1"

    orthologs = bo.ast.bel_object.args[0].orthologs
    assert orthologs["TAX:10090"]["decanonical"] == "MGI:Egf"

    assert bo.ast.collected_orthologs


@pytest.mark.skip(reason="Missing namespace info")
def test_nested_appending_orthologs_to_nsargs():
    """Add orthologs to AST NSArgs to nested bel stmt for use in orthologization"""

    bo.parse("p(SP:P31749) increases (p(SP:P01133) increases p(HGNC:EGFR))")
    bo.collect_orthologs(["TAX:9606", "TAX:10090", "TAX:10116"])

    print("Sub Orthologs", bo.ast.bel_subject.args[0].orthologs)
    print("Nested Sub Orthologs", bo.ast.bel_object.bel_subject.args[0].orthologs)
    print("Nested Obj Orthologs", bo.ast.bel_object.bel_object.args[0].orthologs)

    orthologs = bo.ast.bel_subject.args[0].orthologs
    assert orthologs["TAX:10116"]["decanonical"] == "RGD:Akt1"
    assert orthologs["TAX:10090"]["decanonical"] == "MGI:Akt1"

    orthologs = bo.ast.bel_object.bel_subject.args[0].orthologs
    assert orthologs["TAX:10090"]["decanonical"] == "MGI:Egf"

    assert bo.ast.collected_orthologs
