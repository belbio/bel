import bel.edge.edges

from bel.Config import config

api_url = config['bel_api']['servers']['api_url']


def test_generate_assertion_edge_info():

    bel_version = '2.0.0'
    orthologize_targets = ['TAX:9606', 'TAX:10090']

    assertions = [
        {'subject': 'p(HGNC:AKT1)', 'relation': 'increases', 'object': 'act(p(HGNC:EGF))'},
        {'subject': 'complex(p(HGNC:AKT1), p(HGNC:EGF))', 'relation': 'increases', 'object': 'bp(GO:apoptosis)'},
        {'subject': 'complex(p(HGNC:AKT1), p(HGNC:EGF))'},
        {'subject': 'complex(p(HGNC:AKT1), p(HGNC:EGF))', 'relation': 'increases', 'object': 'bp(GO:apoptosis))'},  # bad assertion - extra paren in object
        {'subject': 'act(p(MGI:Akt1))', 'relation': 'decreases', 'object': 'r(MGI:Sult2a1)'},
        {'subject': 'act(p(MGI:Rora))', 'relation': 'decreases', 'object': 'r(MGI:Egf)'},
        {'subject': 'a(SCHEM:"Smoke, cigarette")', 'relation': 'decreases', 'object': 'p(RGD:Birc3)'},

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

    assert len(edge_info_list[14]['errors']) == 1

    assert edge_info_list[19]["decanonical"]["subject"] == 'act(p(HGNC:RORA))'

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


