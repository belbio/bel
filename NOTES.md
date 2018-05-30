## belc

Load nanopubs into Arangodb

    belc pipeline ../bel_content/bel_nanopubs/small_corpus.v2.json --db_delete true --db_save true


## JSON BEL Spec tricks

Get list of all function summaries

    cat bel/lang/versions/bel_v2_0_0.json | jq '.["function_signatures"][]["signatures"][]["argument_summary"]'

Get all function signatures

    cat bel/lang/versions/bel_v2_0_0.json | jq '.["function_signatures"][]["signatures"]' | more
