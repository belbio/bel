import requests
import json
import urllib.parse

from arango import ArangoError

import bel.utils
from bel.Config import config
import bel.db.arangodb as arangodb

from structlog import get_logger
log = get_logger()

arango_client = arangodb.get_client()

belapi_db = arangodb.get_belapi_handle(arango_client)

state_mgmt = belapi_db.collection(arangodb.belapi_statemgmt_name)
start_dates_doc_key = 'nanopubstore_start_dates'


def update_nanopubstore_start_dt(url: str, start_dt: str):
    """Add nanopubstore start_dt to belapi.state_mgmt collection

    Args:
        url: url of nanopubstore
        start_dt: datetime of last query against nanopubstore for new ID's
    """

    hostname = urllib.parse.urlsplit(url)[1]

    start_dates_doc = state_mgmt.get(start_dates_doc_key)
    if not start_dates_doc:
        start_dates_doc = {'_key': start_dates_doc_key, 'start_dates': [{'nanopubstore': hostname, 'start_dt': start_dt}]}
        state_mgmt.insert(start_dates_doc)
    else:
        for idx, start_date in enumerate(start_dates_doc['start_dates']):
            if start_date['nanopubstore'] == hostname:
                start_dates_doc['start_dates'][idx]['start_dt'] = start_dt
                break
        else:
            start_dates_doc['start_dates'].append({'nanopubstore': hostname, 'start_dt': start_dt})

        state_mgmt.replace(start_dates_doc)


def get_nanopubstore_start_dt(url: str):
    """Get last start_dt recorded for getting new nanopub ID's"""

    hostname = urllib.parse.urlsplit(url)[1]

    start_dates_doc = state_mgmt.get(start_dates_doc_key)
    if start_dates_doc and start_dates_doc.get('start_dates'):
        date = [dt['start_dt'] for dt in start_dates_doc['start_dates'] if dt['nanopubstore'] == hostname]
        log.info(f'Selected start_dt: {date}  len: {len(date)}')
        if len(date) == 1:
            return date[0]

    return '1900-01-01T00:00:00.000Z'


def get_new_nanopub_urls(ns_root_url: str = None, start_dt: str = None) -> list:
    """Get new nanopub urls

    Limited by last datetime retrieved (start_dt)

    Returns:
        list: list of nanopub urls
    """
    if not ns_root_url:
        ns_root_url = config['bel_api']['servers']['nanopubstore']

    url = f'{ns_root_url}/nanopubs/timed'
    if not start_dt:
        start_dt = get_nanopubstore_start_dt(ns_root_url)
    params = {'startTime': start_dt, 'published': True}

    r = bel.utils.get_url(url, params=params, cache=False)

    if r.status_code == 200:
        data = r.json()

        new_start_dt = data['queryTime']
        update_nanopubstore_start_dt(ns_root_url, new_start_dt)
        urls = []
        for nid in data['data']:
            urls.append(f'{ns_root_url}/nanopubs/{nid}')
        return urls

    else:
        log.error(f'Bad request to Nanopubstore', url=url, status=r.status_code, type='api_request')
        return []


def get_nanopub(url):
    """Get Nanopub from nanopubstore given url"""

    r = bel.utils.get_url(url, cache=False)
    if r and r.json():
        return r.json()
    else:
        return {}

