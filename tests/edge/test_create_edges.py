import bel.edge.edges

from bel.Config import config

api_url = config['bel_api']['servers']['api_url']


# TODO - remove any computed orthologized edges that are species=None
def test_assertion_edge_info_dup_computed():
    """Do not allow computed edges to be created that are duplicates of the original edge or orig/orthologized edge"""

    bel_version = config['bel']['lang']['default_bel_version']
    orthologize_targets = ['TAX:9606', 'TAX:10090']

    assertions = [
        {'subject': 'complex(p(HGNC:EGF))', 'relation': 'hasComponent', 'object': 'p(HGNC:EGF)'},  # Should not result in a computed edge
    ]

    nanopub_type = ''  # e.g. not backbone which would skip orthologization

    r = bel.edge.edges.generate_assertion_edge_info(assertions, orthologize_targets, bel_version, api_url, nanopub_type)
    edge_info_list = r['edge_info_list']

    print('Edge Listing')
    for idx, edge in enumerate(edge_info_list):
        try:
            print(f'{idx}: {edge["decanonical"]["subject"]} {edge["decanonical"]["relation"]} {edge["decanonical"]["object"]} SpeciesID: {edge["species_id"]} EdgeTypes: {edge["edge_types"]}  Errors: {edge["errors"]}')
        except Exception:
            print(f'{idx}: {edge["errors"]}')

    edges = [edge for edge in edge_info_list if 'primary' not in edge['edge_types']]
    assert len(edges) == 0


def test_generate_assertion_edge_info1():
    """Set of assertions to test for creating edges"""

    bel_version = config['bel']['lang']['default_bel_version']
    orthologize_targets = ['TAX:9606', 'TAX:10090']

    assertions = [
        {'subject': 'act(p(HGNC:DUOX1))', 'relation': 'decreases', 'object': 'act(p(HGNC:SRC))'},
        {'subject': 'act(p(MGI:Nr1i2))', 'relation': 'increases', 'object': 'r(MGI:Cyp3a11)'},   # resulted in act(p(SP:CP1A1_MOUSE))    increases   r(MGI:Cyp3a11)
        {'subject': 'act(p(MGI:Abcc10))', 'relation': 'association', 'object': 'act(p(PMIPFAM:"ABCC subfamily transporter"))'},
        {'subject': 'act(p(MGI:Hnf4a))', 'relation': 'decreases', 'object': 'r(MGI:AhR)'},
        {'subject': 'path(TBD:"Neuropathic Pain")', 'relation': 'positiveCorrelation', 'object': 'p(HGNC:IL6)'},
    ]

    nanopub_type = ''  # e.g. not backbone which would skip orthologization

    r = bel.edge.edges.generate_assertion_edge_info(assertions, orthologize_targets, bel_version, api_url, nanopub_type)
    edge_info_list = r['edge_info_list']

    print('Edge Listing')
    for idx, edge in enumerate(edge_info_list):
        try:
            print(f'{idx}: {edge["decanonical"]["subject"]} {edge["decanonical"]["relation"]} {edge["decanonical"]["object"]} SpeciesID: {edge["species_id"]} EdgeTypes: {edge["edge_types"]}  Errors: {edge["errors"]}')
        except Exception:
            print(f'{idx}: {edge["errors"]}')

    bad_ns_flag = False
    for idx, edge in enumerate(edge_info_list):
        for ns in ['EG:', 'SP:']:
            if ns in [edge["decanonical"]["subject"], edge["decanonical"]["relation"], edge["decanonical"]["object"]]:
                bad_ns_flag = True
    assert not bad_ns_flag

    assert edge_info_list[3]['decanonical'] == {
        "subject": "act(p(MGI:Duox1))",
        "relation": "decreases",
        "object": "act(p(MGI:Src))",
    }

    assert len(edge_info_list) == 19


def test_generate_assertion_edge_info2():
    """Additional set of assertions to test for creating edges"""

    bel_version = config['bel']['lang']['default_bel_version']
    orthologize_targets = ['TAX:9606', 'TAX:10090']

    assertions = [
        {'subject': 'p(HGNC:AKT1)', 'relation': 'increases', 'object': 'act(p(HGNC:EGF))'},
        {'subject': 'complex(p(HGNC:AKT1), p(HGNC:EGF))', 'relation': 'increases', 'object': 'bp(GO:apoptosis)'},
        {'subject': 'complex(p(HGNC:AKT2), p(HGNC:EGF))'},
        {'subject': 'complex(p(HGNC:AKT1), p(HGNC:EGF))', 'relation': 'increases', 'object': 'bp(GO:apoptosis))'},  # bad assertion - extra paren in object
        {'subject': 'act(p(MGI:Akt1))', 'relation': 'decreases', 'object': 'r(MGI:Sult2a1)'},  # MGI:Sult2a1 doesn't have an ortholog
        {'subject': 'act(p(MGI:Rora))', 'relation': 'decreases', 'object': 'r(MGI:Egf)'},
        {'subject': 'a(SCHEM:"Smoke, cigarette")', 'relation': 'decreases', 'object': 'p(RGD:Birc3)'},  # RGD:Birc3 - no orthologs in EntrezGene
    ]

    nanopub_type = ''  # e.g. not backbone which would skip orthologization

    r = bel.edge.edges.generate_assertion_edge_info(assertions, orthologize_targets, bel_version, api_url, nanopub_type)
    edge_info_list = r['edge_info_list']

    # print('Dump All:\n', json.dumps(edge_info_list, indent=4))

    print('Edge Listing')
    for idx, edge in enumerate(edge_info_list):
        try:
            print(f'{idx}: {edge["decanonical"]["subject"]} {edge["decanonical"]["relation"]} {edge["decanonical"]["object"]} SpeciesID: {edge["species_id"]} EdgeTypes: {edge["edge_types"]}  Errors: {edge["errors"]}')
        except Exception:
            print(f'{idx}: {edge["errors"]}')

    assert edge_info_list[0]['decanonical'] == {
        "subject": "p(HGNC:AKT1)",
        "relation": "increases",
        "object": "act(p(HGNC:EGF))"
    }
    assert edge_info_list[0]['canonical'] == {
        "subject": "p(EG:207)",
        "relation": "increases",
        "object": "act(p(EG:1950))"
    }

    assert edge_info_list[1]['canonical'] == {
        "subject": "p(EG:1950)",
        "relation": "hasActivity",
        "object": "act(p(EG:1950))"
    }

    assert edge_info_list[1]['edge_types'] == ['computed']

    assert edge_info_list[2]["canonical"] == {
        "subject": "p(EG:11651)",
        "relation": "increases",
        "object": "act(p(EG:13645))"
    }

    assert edge_info_list[2]["species_id"] == "TAX:10090"

    errors = [edge['errors'] for edge in edge_info_list if edge['errors']]

    assert len(errors) == 1

    assert len(edge_info_list) == 22


def test_nanopub_to_edges():

    nanopub = {
        "isDeleted": False,
        "source_url": "http://example.com",
        "isPublished": True,
        "associatedids": None,
        "_key": "8eecb1c5-2a41-483f-8c05-b790dae438a2",
        "_rev": "_XU5P6kS---",
        "nanopub": {
            "id": "8eecb1c5-2a41-483f-8c05-b790dae438a2",
            "type": {
                "name": "BEL",
                "version": "2.1.0"
            },
            "annotations": [
                {
                    "id": "",
                    "label": "0.01",
                    "type": "p-value"
                },
                {
                    "id": "",
                    "label": "ELISA",
                    "type": "Methodology"
                },
                {
                    "id": "",
                    "label": "52 ALS patients and 31 non-ALS patients",
                    "type": "Cohort"
                },
                {
                    "id": "UBERON:serum",
                    "label": "serum",
                    "type": "Anatomy"
                },
                {
                    "id": "MESH:\"Amyotrophic Lateral Sclerosis\"",
                    "label": "Amyotrophic Lateral Sclerosis",
                    "type": "Disease"
                },
                {
                    "id": "TAX:9606",
                    "label": "human",
                    "type": "Species"
                }
            ],
            "citation": {
                "abstract": "No Abstract Loaded.",
                "database": {
                    "id": "26332465",
                    "name": "PubMed"
                }
            },
            "assertions": [
                {
                    "subject": "path(MESH:\"Amyotrophic Lateral Sclerosis\")",
                    "relation": "positiveCorrelation",
                    "object": "pop(CL:\"fat cell\")"
                },
                {
                    "subject": "act(p(HGNC:AKT1), ma(kin))",
                    "relation": "increases",
                    "object": "complex(p(HGNC:EGF), p(HGNC:ESR1))"
                }
            ],
            "evidence": "Compared to the non-ALS patients, the ALS patients displayed significantly increased levels of IFN-γ in both CSF and serum, and these values consistently correlated with disease progression.",
            "metadata": {
                "gd:createTS": "2018-04-13T00:14:05.902",
                "gd:creator": "amontagut",
                "gd:published": True,
                "gd:updateTS": "2018-06-11T16:46:50.869Z",
                "project": "Fasting Presentation Curation"
            }
        }
    }

    orthologize_targets = ['TAX:9606', 'TAX:10090']
    r = bel.edge.edges.nanopub_to_edges(nanopub, orthologize_targets=orthologize_targets)

    print('Edge Listing')
    for edge in r['edges']:
        # print('DumpVar:\n', json.dumps(edge, indent=4))
        print(f'{edge["edge"]["relation"]["subject"]} {edge["edge"]["relation"]["relation"]} {edge["edge"]["relation"]["object"]} SpeciesID: {edge["edge"]["relation"]["species_id"]} EdgeTypes: {edge["edge"]["relation"]["edge_types"]}')

    # print('Dump All:\n', json.dumps(r['edges'], indent=4))

    assert len(r['edges']) == 9

    assert r['edges'][0]['edge']['relation']['species_id'] == 'None'

    # TODO - add more assertions


