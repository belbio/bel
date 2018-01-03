import pytest
import bel.nanopub.nanopubs as nb
import yaml
import os

local_dir = os.path.dirname(__file__)


with open(f"{local_dir}/datasets/nanopub_bel-0.9.0.yaml", 'r') as f:
    schema = yaml.load(f)

with open(f"{local_dir}/datasets/nanopub_bel-bad_test-0.9.0.yaml", 'r') as f:
    bad_nanopub = yaml.load(f)

with open(f"{local_dir}/datasets/nanopub_bel-good_test-0.9.0.yaml", 'r') as f:
    good_nanopub = yaml.load(f)


@pytest.mark.skip(reason="Not finished with this test")
def test_valid_schema():

    (is_valid, messages) = nb.validate_to_schema(good_nanopub, schema)
    assert is_valid is True

    (is_valid, messages) = nb.validate_to_schema(bad_nanopub, schema)
    assert is_valid is False
    assert len(messages) > 0
