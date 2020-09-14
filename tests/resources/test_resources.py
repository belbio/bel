from bel.resources.manage import update_resources, clean_configuration, delete_resource
import bel.db.arangodb as arangodb
import json


def test_load_resource():

    bel_config_coll = arangodb.bel_config_coll

    delete_resource("TAX", resource_type="namespace")
    delete_resource("inchikey", resource_type="namespace")

    update_resources(email="whayes@biodati.com", force=True)

    url = "http://resources.bel.bio.s3-us-east-2.amazonaws.com/resources_v2/namespaces/inchikey.jsonl.gz"

    update_resources(url=url, email="whayes@biodati.com", force=True)

    configuration = bel_config_coll.get("configuration")

    import json

    # print("DumpVar:\n", json.dumps(configuration, indent=4))

    assert False


def test_clean_configuration():

    configuration = {
        "update_bel_resources": {
            "namespaces": [
                "http://resources.bel.bio.s3-us-east-2.amazonaws.com/resources_v2/namespaces/up.jsonl.gz",
                "http://resources.bel.bio.s3-us-east-2.amazonaws.com/resources_v2/namespaces/tax_hmrz.jsonl.gz",
                "http://resources.bel.bio.s3-us-east-2.amazonaws.com/resources_v2/namespaces/tbd.jsonl.gz",
            ],
            "orthologs": [
                "http://resources.bel.bio.s3-us-east-2.amazonaws.com/resources_v2/orthologs/eg_hmrz.jsonl.gz"
            ],
        },
    }

    configuration = clean_configuration(configuration)

    print("Cleaned configuration:\n", json.dumps(configuration, indent=4))

    assert (
        configuration["update_bel_resources"]["namespaces"][0]
        == "http://resources.bel.bio.s3-us-east-2.amazonaws.com/resources_v2/namespaces/tax_hmrz.jsonl.gz"
    )

    configuration["update_bel_resources"]["namespaces"].append(
        "http://resources.bel.bio.s3-us-east-2.amazonaws.com/resources_v2/namespaces/inchikey.jsonl.gz"
    )

    configuration = clean_configuration(configuration)

    print("Added inchikey:\n", json.dumps(configuration, indent=4))

    assert (
        configuration["update_bel_resources"]["namespaces"][0]
        == "http://resources.bel.bio.s3-us-east-2.amazonaws.com/resources_v2/namespaces/inchikey.jsonl.gz"
    )
