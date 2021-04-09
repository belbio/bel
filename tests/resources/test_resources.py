# Standard Library
import json

# Third Party
import pytest

# Local
import bel.db.arangodb as arangodb
from bel.resources.manage import delete_resource, update_resources


def test_update_namespace():

    results = update_resources(
        urls=[
            "http://resources.bel.bio.s3.us-east-2.amazonaws.com/resources_v2/namespaces/tax_hmrz.jsonl.gz"
        ],
        force=True,
    )

    print("Results", results)

    assert (
        results[
            "http://resources.bel.bio.s3.us-east-2.amazonaws.com/resources_v2/namespaces/tax_hmrz.jsonl.gz"
        ]["state"]
        == "Succeeded"
    )
