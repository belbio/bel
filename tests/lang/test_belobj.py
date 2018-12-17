import bel.lang.ast
import bel.lang.belobj
import bel.lang.bel_utils
import bel.db.arangodb

from bel.Config import config

bo = bel.lang.belobj.BEL(config['bel']['lang']['default_bel_version'], config['bel_api']['servers']['api_url'])


def test_species():

    assertion = 'p(SP:P31749) increases act(p(HGNC:EGF))'
    bo.parse(assertion)
    bo.collect_nsarg_norms()

    print(f'Species should equal TAX:9606 :: {bo.ast.species}')

    correct = set()
    correct.add(('TAX:9606', 'human', ))

    assert correct == bo.ast.species


def test_multi_species():

    assertion = 'p(MGI:Egf) increases act(p(HGNC:EGF))'
    bo.parse(assertion)
    bo.collect_nsarg_norms()

    print(f'Species should be human and mouse:: {bo.ast.species}')

    correct = set()
    correct.add(('TAX:9606', 'human', ))
    correct.add(('TAX:10090', 'mouse', ))

    assert correct == bo.ast.species


def test_orthologization():
    """Test orthologization of assertion"""

    assertion = 'p(SP:P31749) increases act(p(HGNC:EGF))'
    correct = 'p(MGI:Akt1) increases act(p(MGI:Egf))'
    result = bo.parse(assertion).orthologize('TAX:10090').to_string()
    print('Orthologized assertion', result)

    assert correct == result

    # Check species
    correct = set()
    correct.add(('TAX:10090', 'mouse', ))

    assert correct == bo.ast.species


def test_multi_orthologization():
    """Test multiple species orthologization of assertion"""

    assertion = 'p(MGI:Akt1) increases act(p(HGNC:EGF))'
    correct = 'p(MGI:Akt1) increases act(p(MGI:Egf))'
    result = bo.parse(assertion).orthologize('TAX:10090').to_string()
    print('Orthologized assertion', result)

    assert correct == result

    # Check species
    correct = set()
    correct.add(('TAX:10090', 'mouse', ))

    assert correct == bo.ast.species


def test_canonicalization():
    """Test canonicalization of assertion"""

    assertion = 'p(SP:P31749) increases act(p(HGNC:EGF))'
    correct = 'p(EG:207) increases act(p(EG:1950))'
    result = bo.parse(assertion).canonicalize().to_string()
    print('Canonicalized assertion', result)

    assert correct == result


def test_decanonicalization():
    """Test canonicalization of assertion"""

    assertion = 'p(EG:207) increases act(p(EG:1950))'
    correct = 'p(HGNC:AKT1) increases act(p(HGNC:EGF))'

    result = bo.parse(assertion).decanonicalize().to_string()
    print('deCanonicalized assertion', result)

    assert correct == result

    assertion = 'p(SP:P31749) increases act(p(HGNC:EGF))'
    correct = 'p(HGNC:AKT1) increases act(p(HGNC:EGF))'

    result = bo.parse(assertion).decanonicalize().to_string()
    print('deCanonicalized assertion', result)

    assert correct == result
