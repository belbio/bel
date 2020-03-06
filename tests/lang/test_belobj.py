import bel.db.arangodb
import bel.lang.ast
import bel.lang.bel_utils
import bel.lang.belobj
from bel.Config import config

bo = bel.lang.belobj.BEL(
    config["bel"]["lang"]["default_bel_version"], config["bel_api"]["servers"]["api_url"]
)


def test_bel_semantic_validation():

    obsolete_NSArg = "p(HGNC:FAM46C)"

    bo.parse(obsolete_NSArg).semantic_validation()

    print("Validation messages", bo.validation_messages)

    assert bo.validation_messages[0][1] == "Obsolete term: HGNC:FAM46C  Current term: HGNC:TENT5C"
