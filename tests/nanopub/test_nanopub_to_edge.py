import pytest
import bel.nanopub.nanopubs as nb
import json
import os

local_dir = os.path.dirname(__file__)


def remove_dt_keys(edges):
    """Remove datetime keys since they break the assertions"""
    for edge in edges:
        if 'edge_dt' in edge['edge']['relation']:  # TODO can probably get rid of this as we don't add edge_dt until just before laoding into EdgeStore
            del edge['edge']['relation']['edge_dt']

    return edges


@pytest.mark.skip(reason="Skip for now - need to update Annotations")
def test_simple_nanopub():
    """Convert simple nanopub to edges"""

    with open(f"{local_dir}/datasets/nanopub_bel-good-1.0.0.json", 'r') as f:
        nanopub = json.load(f)

    with open(f"{local_dir}/datasets/edges-good-1.0.0.json", 'r') as f:
        edges_result = json.load(f)

    N = nb.Nanopub()
    edges = N.bel_edges(nanopub)

    print('Edges:\n', json.dumps(edges, indent=4))
    edges = remove_dt_keys(edges)
    assert edges_result == edges


@pytest.mark.skip(reason="Skip for now - need to update Annotations")
def test_multiple_nanopub():
    """Convert nanopub with multiple assertions to edges"""

    with open(f"{local_dir}/datasets/nanopub_bel-good-multiple-assertions-1.0.0.json", 'r') as f:
        nanopub = json.load(f)

    with open(f"{local_dir}/datasets/edges-good-multiple-assertions-1.0.0.json", 'r') as f:
        edges_result = json.load(f)

    N = nb.Nanopub()
    edges = N.bel_edges(nanopub)

    print('Edges:\n', json.dumps(edges, indent=4))
    edges = remove_dt_keys(edges)
    assert edges_result == edges


@pytest.mark.skip(reason="Skip for now - need to update Annotations")
def test_nested_nanopub():
    """Convert nanopub with nested assertion to edges"""

    with open(f"{local_dir}/datasets/nanopub_bel-good-nested-1.0.0.json", 'r') as f:
        nanopub = json.load(f)

    with open(f"{local_dir}/datasets/edges-good-nested-1.0.0.json", 'r') as f:
        edges_result = json.load(f)

    N = nb.Nanopub()
    edges = N.bel_edges(nanopub)

    print('Edges:\n', json.dumps(edges, indent=4))
    edges = remove_dt_keys(edges)
    assert edges_result == edges


@pytest.mark.skip(reason="Skip for now - need to update Annotations")
def test_degradation_nanopub():
    """Convert nanopub with degradation assertion to edges"""

    with open(f"{local_dir}/datasets/nanopub_bel-good-degradation-1.0.0.json", 'r') as f:
        nanopub = json.load(f)

    with open(f"{local_dir}/datasets/edges-good-degradation-1.0.0.json", 'r') as f:
        edges_result = json.load(f)

    N = nb.Nanopub()
    edges = N.bel_edges(nanopub)

    print('Edges:\n', json.dumps(edges, indent=4))
    edges = remove_dt_keys(edges)
    assert edges_result == edges
