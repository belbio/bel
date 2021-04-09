# Standard Library
import json

# Third Party
import pytest


def test_optimize(client):

    response = client.get("/bel/optimize/g(ensembl:ENSG00000157557)")

    print("Response", response.json())

    assert False
