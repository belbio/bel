# Standard Library
import json

# Third Party
import pytest

# Local
# Local Imports
import bel.nanopub.validate
from bel.schemas.nanopubs import NanopubR

# cSpell:disable

# @pytest.mark.skip(reason="Not finished with this test")
def test_validate_nanopub():

    nanopub = {
        "_key": "01DZZ0WBHER1B3MXW2TFDA2QWE",
        "nanopub": {
            "annotations": [
                {"id": "TAX:9606", "label": "human", "type": "Species"},
                {"id": "HGNC:A2MP", "label": "A2MP", "type": "Disease"},
            ],
            "assertions": [
                {
                    "object": "act(p(SPX:AKT1_HUMAN)",
                    "relation": "increases",
                    "subject": "act(p(SP:AKT1_HUMAN), ma))",
                },
                {"subject": "g(HGNC:A2MP)"},
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
                "gd_validation": [],
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

    nanopub_validated = bel.nanopub.validate.validate(NanopubR(**nanopub), validation_level="force")

    nanopub_validated_dict = nanopub_validated.dict()

    print("Validated Nanopub:\n", nanopub_validated.json(indent=4))

    assert nanopub_validated_dict["nanopub"]["assertions"][0]["validation"]["status"] == "Error"
    assert (
        nanopub_validated_dict["nanopub"]["assertions"][0]["validation"]["errors"][0]["msg"]
        == "Too many close parentheses at index 25"
    )
    assert (
        nanopub_validated_dict["nanopub"]["assertions"][0]["validation"]["errors"][0]["visual"]
        == 'act(p(SP:AKT1_HUMAN), ma)<span class="accentuate">)</span> increases act(p(SPX:AKT1_HUMAN)'
    )

    assert (
        nanopub_validated_dict["nanopub"]["annotations"][1]["validation"]["errors"][0]["msg"]
        == "Annotation term HGNC:A2MP is obsolete - please replace with HGNC:8"
    )
    assert (
        nanopub_validated_dict["nanopub"]["annotations"][1]["validation"]["errors"][1]["msg"]
        == "Annotation type: Disease for HGNC:A2MP does not match annotation types in database: []"
    )


def test_validate_nanopub2():

    nanopub = json.loads(
        """{
            "rev": "_bLpe16a--_",
            "owners": [
                {
                "user_id": "303928642",
                "first_name": "Wendy",
                "last_name": "Zimmerman",
                "full_name": " Wendy Zimmerman"
                }
            ],
            "is_deleted": false,
            "is_archived": null,
            "is_public": false,
            "source_url": "https://nanopubstore.thor.biodati.com/nanopub/01EAAA7EJZC8B7EF5T78FN53JR",
            "nanopub": {
                "type": {
                "name": "BEL",
                "version": "2.1.0"
                },
                "citation": {
                "id": null,
                "authors": [
                    "Knoop, L L",
                    "Baker, S J"
                ],
                "database": {
                    "name": "PubMed",
                    "id": "10827180"
                },
                "reference": "J Biol Chem 2000 Aug 11 275(32) 24865-71",
                "uri": null,
                "title": "The splicing factor U1C represses EWS/FLI-mediated transactivation.",
                "source_name": "The Journal of biological chemistry",
                "date_published": "2000-08-11",
                "abstract": ""
                },
                "assertions": [
                {
                    "subject": "p(HGNC:SNRPC)",
                    "relation": "decreases",
                    "object": "act(p(fus(HGNC:EWSR1, start, HGNC:FLI1, end)), ma(tscript))",
                    "validation": null
                }
                ],
                "id": "01EAAA7EJZC8B7EF5T78FN53JR",
                "schema_uri": "https://raw.githubusercontent.com/belbio/schemas/master/schemas/nanopub_bel-1.1.0.yaml",
                "annotations": [
                {
                    "type": "Species",
                    "label": "human",
                    "id": "TAX:9606",
                    "validation": null
                }
                ],
                "evidence": "Importantly, co-expression of U1C represses EWS/FLI-mediated transactivation, demonstrating that this interaction can have functional ramifications.",
                "metadata": {
                "collections": [
                    "corrected",
                    "Selventa-Full"
                ],
                "gd_status": "finalized",
                "gd_createTS": "2020-06-08T15:54:17.566Z",
                "gd_updateTS": "2020-06-09T14:21:38.573Z",
                "gd_validation": {
                    "status": "Good",
                    "errors": null,
                    "validation_target": null
                },
                "gd_hash": "73b5b7b36f9bf6a6",
                "statement_group": "67265439",
                "gd_abstract": "EWS is an RNA-binding protein involved in human tumor-specific chromosomal translocations. In approximately 85% of Ewing's sarcomas, such translocations give rise to the chimeric gene EWS/FLI. In the resulting fusion protein, the RNA binding domains from the C terminus of EWS are replaced by the DNA-binding domain of the ETS protein FLI-1. EWS/FLI can function as a transcription factor with the same DNA binding specificity as FLI-1. EWS and EWS/FLI can associate with the RNA polymerase II holoenzyme as well as with SF1, an essential splicing factor. Here we report that U1C, one of three human U1 small nuclear ribonucleoprotein-specific proteins, interacts in vitro and in vivo with both EWS and EWS/FLI. U1C interacts with other splicing factors and is important in the early stages of spliceosome formation. Importantly, co-expression of U1C represses EWS/FLI-mediated transactivation, demonstrating that this interaction can have functional ramifications. Our findings demonstrate that U1C, a well characterized splicing protein, can also function in transcriptional regulation. Furthermore, they suggest that EWS and EWS/FLI may function both in transcriptional and post-transcriptional processes.",
                "gd_creator": "303928642"
                }
            }
            }"""
    )

    nanopub_validated = bel.nanopub.validate.validate(NanopubR(**nanopub), validation_level="force")

    nanopub_validated_dict = nanopub_validated.dict()

    print("Validated Nanopub2:\n", nanopub_validated.json(indent=4))

    assert False

    # assert nanopub_validated_dict["nanopub"]["assertions"][0]["validation"]["status"] == "Error"
    # assert (
    #     nanopub_validated_dict["nanopub"]["assertions"][0]["validation"]["errors"][0]["msg"]
    #     == "Too many close parentheses at index 25"
    # )
    # assert (
    #     nanopub_validated_dict["nanopub"]["assertions"][0]["validation"]["errors"][0]["visual"]
    #     == 'act(p(SP:AKT1_HUMAN), ma)<span class="accentuate">)</span> increases act(p(SPX:AKT1_HUMAN)'
    # )

    # assert (
    #     nanopub_validated_dict["nanopub"]["annotations"][1]["validation"]["errors"][0]["msg"]
    #     == "Annotation term HGNC:A2MP is obsolete - please replace with HGNC:8"
    # )
    # assert (
    #     nanopub_validated_dict["nanopub"]["annotations"][1]["validation"]["errors"][1]["msg"]
    #     == "Annotation type: Disease for HGNC:A2MP does not match annotation types in database: []"
    # )
