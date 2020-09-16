# Standard Library
import json

# Local Imports
import bel.nanopub.validate
from bel.schemas.nanopubs import NanopubR
import pytest

# cSpell:disable

# @pytest.mark.skip(reason="Not finished with this test")
def test_validate_nanopub():

    nanopub = {
        "_key": "01DZZ0WBHER1B3MXW2TFDA2QWE",
        "nanopub": {
            "annotations": [{"id": "TAX:9606", "label": "human", "type": "Species"}],
            "assertions": [
                {
                    "object": "act(p(SPX:AKT1_HUMAN)",
                    "relation": "increases",
                    "subject": "act(p(SP:AKT1_HUMAN), ma))",
                }
            ],
            "citation": {
                "abstract": "Recently, we identified the two myeloid related protein-8 (MRP8) (S100A8) and MRP14 (S100A9) as fatty acid-binding proteins (Klempt, M., Melkonyan, H., Nacken, W., Wiesmann, D., Holtkemper, U., and Sorg, C. (1997) FEBS Lett. 408, 81-84). Here we present data that the S100A8/A9 protein complex represents the exclusive arachidonic acid-binding proteins in human neutrophils. Binding and competition studies revealed evidence that (i) fatty acid binding was dependent on the calcium concentration; (ii) fatty acid binding was specific for the protein complex formed by S100A8 and S100A9, whereas the individual components were unable to bind fatty acids; (iii) exclusively polyunsaturated fatty acids were bound by S100A8/A9, whereas saturated (palmitic acid, stearic acid) and monounsaturated fatty acids (oleic acid) as well as arachidonic acid-derived eicosanoids (15-hydroxyeicosatetraenoic acid, prostaglandin E(2), thromboxane B(2), leukotriene B(4)) were poor competitors. Stimulation of neutrophil-like HL-60 cells with phorbol 12-myristate 13-acetate led to the secretion of S100A8/A9 protein complex, which carried the released arachidonic acid. When elevation of intracellular calcium level was induced by A23187, release of arachidonic acid occurred without secretion of S100A8/A9. In view of the unusual abundance in neutrophilic cytosol (approximately 40% of cytosolic protein) our findings assign an important role for S100A8/A9 as mediator between calcium signaling and arachidonic acid effects. Further investigations have to explore the exact function of the S100A8/A9-arachidonic acid complex both inside and outside of neutrophils.",
                "authors": ["Kerkhoff, C", "Klempt, M", "Kaever, V", "Sorg, C"],
                "database": {"id": "10551823", "name": "PubMed"},
                "date_published": "1999-11-12",
                "source_name": "The Journal of biological chemistry",
                "title": "The two calcium-binding proteins, S100A8 and S100A9, are involved in the metabolism of arachidonic acid in human neutrophils.",
            },
            "evidence": "we identified the two myeloid related protein-8 (MRP8) (S100A8) and MRP14 (S100A9) as fatty acid-binding proteins",
            "id": "01DZZ0WBHER1B3MXW2TFDA2QWE",
            "metadata": {
                "gd_createTS": "2020-02-01T00:02:19.634Z",
                "gd_hash": "b9b868e675bdd8ab",
                "gd_internal_comments": "",
                "gd_rev": "_Z92MJja---",
                "gd_status": "draft",
                "gd_updateTS": "2020-02-01T00:02:19.634Z",
            },
            "schema_uri": "https://raw.githubusercontent.com/graphdati/schemas/master/nanopub_graphdati-1.0.0.json",
            "type": {"name": "BEL", "version": "2.1.1"},
        },
        "owners": [
            {
                "user_id": "auth0|5b0ec2d2157859716f2b2449",
                "first_name": "William",
                "last_name": "Hayes",
                "full_name": "William Hayes",
            }
        ],
    }

    nanopub = bel.nanopub.validate.validate(NanopubR(**nanopub), validation_level="force")

    print("DumpVar:\n", json.dumps(nanopub, indent=4))

    assert nanopub["nanopub"]["assertions"][0]["validation"]["status"] == "Error"
    assert (
        nanopub["nanopub"]["assertions"][0]["validation"]["errors"][0]["msg"]
        == "Too many close parentheses at index 25"
    )
    assert (
        nanopub["nanopub"]["assertions"][0]["validation"]["errors"][0]["visual"]
        == 'act(p(SP:AKT1_HUMAN), ma)<span class="accentuate">)</span> increases act(p(SPX:AKT1_HUMAN)'
    )


def test_validate_nanopub2():
    """Test nanopub validation using provided nanopub"""

    nanopub = {
        "rev": "_bFgy2ee--_",
        "owners": [
            {
                "user_id": "01dyjx9yy6jkkfwsfm15ndnry0",
                "first_name": "William",
                "last_name": "Hayes",
                "full_name": "William Hayes",
            }
        ],
        "is_deleted": False,
        "is_public": False,
        "source_url": "http://nanopubstore.dev.biodati.test/nanopub/01EHQ1SJ1FZW9SZ8QW2TWQG4CN",
        "nanopub": {
            "type": {"name": "BEL", "version": "2.1.2"},
            "citation": {
                "authors": [
                    "Roucou, Xavier",
                    "Rostovtseva, Tatiana",
                    "Montessuit, Sylvie",
                    "Martinou, Jean-Claude",
                    "Antonsson, Bruno",
                ],
                "database": {"name": "PubMed", "id": "11964155"},
                "title": "Bid induces cytochrome c-impermeable Bax channels in liposomes.",
                "source_name": "The Biochemical journal",
                "date_published": "2002-05-01",
                "abstract": "Bax is a proapoptotic member of the Bcl-2 family of proteins. The Bax protein is dormant in the cytosol of normal cells and is activated upon induction of apoptosis. In apoptotic cells, Bax gets translocated to mitochondria, inserts into the outer membrane, oligomerizes and triggers the release of cytochrome c, possibly by channel formation. The BH3 domain-only protein Bid induces a conformational change in Bax before its insertion into the outer membrane. The mechanism by which Bid promotes Bax activation is not understood, and whether Bid is the only protein required for Bax activation is unclear. Here we report that recombinant full-length Bax (Bax(FL)) does not form channels in lipid bilayers when purified as a monomer. In contrast, in the presence of Bid cut with caspase 8 (cut Bid), Bax forms ionic channels in liposomes and planar bilayers. This channel-forming activity requires an interaction between cut Bid and Bax, and is inhibited by Bcl-x(L). Moreover, in the absence of the putative transmembrane C-terminal domain, Bax does not form ionic channels in the presence of cut Bid. Cut Bid does not induce Bax oligomerization in liposomes and the Bax channels formed in the presence of cut Bid are not large enough to permeabilize vesicles to cytochrome c. In conclusion, our results suggest that monomeric Bax(FL) can form channels only in the presence of cut Bid. Cut Bid by itself is unable to induce Bax oligomerization in lipid membranes. It is suggested that another factor that might be present in mitochondria is required for Bax oligomerization.",
                "comments": " ",
            },
            "assertions": [
                {"subject": "", "relation": "", "object": "a(MESH:D014867!Water)"},
                {
                    "subject": "a(CHEBI:15428!glycine)",
                    "relation": "",
                    "object": "",
                    "validation": {"status": "Good", "errors": None},
                },
            ],
            "id": "01EHQ1SJ1FZW9SZ8QW2TWQG4CN",
            "schema_uri": "https://raw.githubusercontent.com/belbio/schemas/master/schemas/nanopub_bel-1.1.0.yaml",
            "annotations": [
                {
                    "type": "",
                    "label": "Ion Channels",
                    "id": "MESH:D007473",
                    "validation": {
                        "status": "Warning",
                        "errors": [
                            {
                                "type": "Annotation",
                                "severity": "Warning",
                                "label": "Annotation-Warning",
                                "msg": "Annotation type:  for MESH:D007473 does not match annotation types in database: []",
                                "visual": None,
                                "visual_pairs": None,
                                "index": 0,
                            }
                        ],
                        "validation_target": None,
                    },
                    "hash": "1759921126727370510",
                    "str": "MESH:D007473",
                },
                {
                    "type": "Species",
                    "label": "human",
                    "id": "TAX:9606",
                    "validation": {"status": "Good", "errors": None, "validation_target": None},
                    "hash": "7430120383187917444",
                    "str": "Species TAX:9606",
                },
            ],
            "evidence": "",
            "metadata": {
                "collections": [],
                "gd_status": "draft",
                "gd_createTS": "2020-09-08T14:26:54.114Z",
                "gd_updateTS": "2020-09-10T15:49:14.361Z",
                "gd_validation": {"status": "Good"},
                "gd_hash": "8637bb93aa2bf8fe",
                "gd_creator": "01dyjx9yy6jkkfwsfm15ndnry0",
                "gd_internal_comments": "",
            },
        },
    }

    nanopub_validated = bel.nanopub.validate.validate(nanopub, validation_level="force")

    print("Validated Nanopub:\n", json.dumps(nanopub_validated, indent=4))

    assert (
        nanopub["nanopub"]["assertions"][0]["validation"]["errors"][0]["msg"]
        == "Missing Assertion Subject or Relation"
    )
