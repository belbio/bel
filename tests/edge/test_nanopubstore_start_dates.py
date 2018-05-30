#!/usr/bin/env python

# from bel.Config import config
# import bel.edge.edges
# import json


# def test_get_start_dates():

#     doc = bel.edge.edges.get_start_dates()
#     print(doc)
#     assert doc['_key'] == 'nanopubstore_start_dt'
#     assert 'start_dates' in doc


# def test_update_start_dates():

#     bel.edge.pipeline.put_start_dates('https://nanopubstore.demo.biodati.com', '2018-02-21T01:01:30.000Z')
#     doc = bel.edge.pipeline.get_start_dates()
#     print(f'Doc1: {json.dumps(doc, indent=4)}')
#     assert '2018-02-21T01:01:30.000Z' == [start_date for start_date in doc['start_dates'] if start_date['nanopubstore_url'] == 'https://nanopubstore.demo.biodati.com'][0]['start_dt']

#     bel.edge.pipeline.put_start_dates('https://nanopubstore.test.biodati.com', '2018-01-21T01:01:30.000Z')
#     doc = bel.edge.pipeline.get_start_dates()
#     print(f'Doc2: {json.dumps(doc, indent=4)}')
#     assert '2018-01-21T01:01:30.000Z' == [start_date for start_date in doc['start_dates'] if start_date['nanopubstore_url'] == 'https://nanopubstore.test.biodati.com'][0]['start_dt']

#     bel.edge.pipeline.put_start_dates('https://nanopubstore.demo.biodati.com', '2018-02-30T01:01:30.000Z')
#     doc = bel.edge.pipeline.get_start_dates()
#     print(f'Doc3: {json.dumps(doc, indent=4)}')
#     assert '2018-02-30T01:01:30.000Z' == [start_date for start_date in doc['start_dates'] if start_date['nanopubstore_url'] == 'https://nanopubstore.demo.biodati.com'][0]['start_dt']


