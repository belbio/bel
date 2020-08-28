#!/usr/bin/env python
# -*- coding: utf-8-*-

"""
Usage: $ {1: program}.py
"""

# Local Imports
import bel.core.settings as settings
settings.ELASTICSEARCH_URL = "http://thor:9200"
import bel.resources.resource  # isort:skip

settings.TERMS_INDEX = "terms2"
settings.ARANGO_URL = "http://thor:8529"



def db_setup():
    import bel.resources.resource
    import bel.db.arangodb
    import bel.db.elasticsearch


def main():

    db_setup()

    namespaces = [
        "do",
        "eg_hmrz",
        "go",
        "hgnc",
        "mesh",
        "mgi",
        "rgd",
        "sp_hmrz",
        "tax_hmrz",
        "chebi",
        "up",
        "tbd",
        "pubchem",
        "inchikey",
    ]

    orthologs = [
           "eg_hmrz"
    ]

    for namespace in namespaces:
        fn = f"/Users/william/belres/namespaces/{namespace}.jsonl.gz"
        bel.resources.resource.load_resource(resource_fn=fn, force=True)

    for ortholog in orthologs:
        fn = f"/Users/william/belres/orthologs/{ortholog}.jsonl.gz"
        bel.resources.resource.load_resource(resource_fn=fn, force=True)


if __name__ == "__main__":

    main()
