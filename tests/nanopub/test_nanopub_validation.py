# Standard Library
import json

# Third Party
import pytest

# Local
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


def test_validate_nanopub_2():

    # {
    #     "subject": 'rxn(reactants(p(reactome:R-HSA-1839029.2!"cytosolic FGFR1 fusion mutants", var("p.Insertion of residues 429 to 822 at 250 from, UniProt:P11362, FGFR1"), var("p.Insertion of residues 429 to 822 at 164 from, UniProt:P11362, FGFR1"), var("p.Insertion of residues 429 to 822 at 627 from, UniProt:P11362, FGFR1"), var("p.Insertion of residues 429 to 822 at 491 from, UniProt:P11362, FGFR1"), var("p.Insertion of residues 429 to 822 at 1692 from, UniProt:P11362, FGFR1"), var("p.Insertion of residues 429 to 822 at 914 from, UniProt:P11362, FGFR1"), var("p.Insertion of residues 429 to 822 at 340 from, UniProt:P11362, FGFR1"), var("p.Insertion of residues 429 to 822 at 133 from, UniProt:P11362, FGFR1"), var("p.Insertion of residues 429 to 822 at 585 from, UniProt:P11362, FGFR1"), loc(GO:0005829!cytosol))), products(complex(reactome:R-HSA-1839026.2!"cytosolic FGFR1 fusion mutant dimers", loc(GO:0005829!cytosol))))'
    # }

    nanopub = {
        "nanopub": {
            "type": {"name": "BEL", "version": "latest"},
            "citation": {
                "authors": ["Ezzat, S", "Rothfels, K"],
                "database": {"name": "PubMed", "id": ""},
                "uri": "https://reactome.org/content/detail/R-HSA-1839031.3",
                "title": "Dimerization of cytosolic FGFR1 fusion proteins",
                "source_name": "Reactome",
                "date_published": "2018-01-26",
                "abstract": "",
                "source_type": "database",
            },
            "assertions": [
                {
                    "subject": 'rxn(reactants(p(reactome:R-HSA-1839029.2!"cytosolic FGFR1 fusion mutants", var("p.Insertion of residues 429 to 822 at 250 from, UniProt:P11362, FGFR1"), var("p.Insertion of residues 429 to 822 at 164 from, UniProt:P11362, FGFR1"), var("p.Insertion of residues 429 to 822 at 627 from, UniProt:P11362, FGFR1"), var("p.Insertion of residues 429 to 822 at 491 from, UniProt:P11362, FGFR1"), var("p.Insertion of residues 429 to 822 at 1692 from, UniProt:P11362, FGFR1"), var("p.Insertion of residues 429 to 822 at 914 from, UniProt:P11362, FGFR1"), var("p.Insertion of residues 429 to 822 at 340 from, UniProt:P11362, FGFR1"), var("p.Insertion of residues 429 to 822 at 133 from, UniProt:P11362, FGFR1"), var("p.Insertion of residues 429 to 822 at 585 from, UniProt:P11362, FGFR1"), loc(GO:0005829!cytosol))), products(complex(reactome:R-HSA-1839026.2!"cytosolic FGFR1 fusion mutant dimers", loc(GO:0005829!cytosol))))'
                }
            ],
            "id": "Reactome_R-HSA-1839031",
            "schema_uri": "https://raw.githubusercontent.com/belbio/schemas/master/schemas/nanopub_bel-1.1.0.yaml",
            "annotations": [
                {"type": "Species", "label": "Homo sapiens", "id": "TAX:9606"},
                {"type": "Disease", "label": "cancer", "id": "DO:162"},
            ],
            "evidence": "8p11 myeloproliferative syndrome (EMS) is a myeloproliferative disorder that rapidly progresses to acute myeloid leukemia if not treated (reviewed in Jackson, 2010, Knights and Cook, 2010).  A characteristic feature of EMS is the presence of fusion proteins that contain the kinase domain of FGFR1 and the oligomerization domain of an unrelated protein.  This is believed to promote the ligand independent dimerization and activation of the kinase domain. To date, there are 11 identified partners that form fusion proteins with FGFR1 in EMS: ZMYM2 (Xiao, 1998; Popovici, 1998; Reiter, 1998; Ollendorff, 1999; Xiao, 2000), FGFR1OP1 (Popovici, 1999), CNTRL (Guasch, 2000), BCR (Demiroglu, 2001), FGFR1OP2 (Grand, 2004), TRIM24 (Belloni, 2005), CUX1 (Wasag, 2011), MYO18A (Walz, 2005), CPSF6 (Hidalgo-Curtis, 2008), HERV-K (Guasch, 2003) and LRRFIP1 (Soler, 2009).",
            "metadata": {
                "collections": ["Reactome"],
                "gd_status": "review",
                "gd_createTS": "2012-02-10T01:07:10.000Z",
                "gd_updateTS": "2021-02-18T23:16:37.705Z",
                "gd_validation": {"status": "Good"},
                "gd_hash": "7be6fc57cf971488",
                "license_url": "https://creativecommons.org/publicdomain/zero/1.0",
                "creator_orcid": "0000-0002-0705-7048",
                "version": "Reactome_R-HSA-1839031.3",
                "source_url": "https://reactome.org/content/detail/R-HSA-1839031.3",
                "gd_internal_comments": "",
                "source": "Reactome",
                "license": "CC0",
            },
        }
    }

    nanopub_validated = bel.nanopub.validate.validate(NanopubR(**nanopub), validation_level="force")

    nanopub_validated_dict = nanopub_validated.dict()

    print("Validated Nanopub2:\n", nanopub_validated.json(indent=4))

    assert (
        nanopub_validated.nanopub.assertions[0].subject
        == """rxn(reactants(p(reactome:R-HSA-1839029.2!\"cytosolic FGFR1 fusion mutants\", var(\"p.Insertion of residues 429 to 822 at 250 from, UniProt:P11362, FGFR1\"), var(\"p.Insertion of residues 429 to 822 at 164 from, UniProt:P11362, FGFR1\"), var(\"p.Insertion of residues 429 to 822 at 627 from, UniProt:P11362, FGFR1\"), var(\"p.Insertion of residues 429 to 822 at 491 from, UniProt:P11362, FGFR1\"), var(\"p.Insertion of residues 429 to 822 at 1692 from, UniProt:P11362, FGFR1\"), var(\"p.Insertion of residues 429 to 822 at 914 from, UniProt:P11362, FGFR1\"), var(\"p.Insertion of residues 429 to 822 at 340 from, UniProt:P11362, FGFR1\"), var(\"p.Insertion of residues 429 to 822 at 133 from, UniProt:P11362, FGFR1\"), var(\"p.Insertion of residues 429 to 822 at 585 from, UniProt:P11362, FGFR1\"), loc(GO:0005829!cytosol))), products(complex(reactome:R-HSA-1839026.2!\"cytosolic FGFR1 fusion mutant dimers\", loc(GO:0005829!cytosol))))"""
    )
