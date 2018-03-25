import datetime

import bel.db
from bel.Config import config

import logging
log = logging.getLogger(__name__)

arangodb_client = bel.db.arangodb.get_client()
belapi_handle = bel.db.arangodb.get_belapi_handle(arangodb_client)


def get_start_date(nanopubstore_api: str) -> str:
    """Get start_date to filter nanopubs for conversion to edges

    Also set datetime flag to indicate that nanopubs are being processed for
    given nanopubstore_api. Only start processing if start_date is null.
    If start_date is not null and has been running for more than 2 hours,
    send an email to admin email listed on config.

    Args:
        nanopubstore_api: API endpoint for Nanopubstore, e.g.
        <nanopubstore_api>/nanopubs/timed

    Returns:
        str: start_date in 1900-01-01T00:00:00.000 format
    """

    start_date = "1900-01-01T00:00:00Z"
    processing_nanopubs = ''

    query = f"""
        FOR setting in settings
            FILTER setting._key == {nanopubstore_api}
            RETURN {start_date: setting.start_date, processing_nanopubs: setting.processing_nanopubs}
    """
    settings_cursor = bel.db.arangodb.aql_query(belapi_handle, query)
    for setting in settings_cursor:
        start_date = setting['start_date']
        processing_nanopubs = setting['processing_nanopubs']

    dtnow = datetime.datetime.now()

    # Check to see if processing_nanopubs is stuck
    if processing_nanopubs:
        process_start = bel.utils.parse_dt(processing_nanopubs)
        time_difference = dtnow - process_start
        # If it's been longer than 2 hours since last run started and
        #   hasn't reset the processing_nanopubs dt_flag - send notification
        if time_difference / datetime.timedelta(seconds=1) > 7200:
            mail_to = config['bel_api']['mail']['admin_email']
            subject = f'WARNING: Processing nanopubs for {nanopubstore_api}'
            msg = f"""
                Possible issue with processing nanopubs - still running after more
                than 2 hours.  Check BEL API {config['bel_api']['servers']['api_url']}
                using NanopubStore: {nanopubstore_api}. May need to access ArangoDB and
                reset processing_nanopubs datetime flag.
            """
            common.mail.send_mail(mail_to, subject, msg, mail_from=mail_to)
    if not processing_nanopubs:
        query = f"UPDATE {{ _key: {nanopubstore_api}, processing_nanopubs: {dtnow} }}"


def put_start_date(nanopubstore_api: str, start_date: str):
    """Pub start_date for next run to process nanopubs into edges

    Remove flag to indicate nanopubs are being processed at the same
    time you update the start_date.

    Args:
        nanopubstore_api: API endpoint for Nanopubstore, e.g.
            <nanopubstore_api>/nanopubs/timed
        start_date: date string in 1900-01-01T00:00:00.000 format - only nanopubs
            that are updated on or after that time will be processed
    """

    query = f"""
        UPSERT {{ _key: {nanopubstore_api} }}
        INSERT {{ _key: {nanopubstore_api}, start_date: {start_date}, processing_nanopubs: ''}}
        UPDATE: {{ _key: {nanopubstore_api}, start_date: {start_date}, processing_nanopubs: '' }}
    """
    bel.db.arangodb.aql_query(belapi_handle, query)


def run_pipeline(nanopubstore_url: str, start_dt: str = None):
    """Webhook to process new nanopubs in NanopubStore into edges

    Will only process published nanopubs.  The last start_date stored
    in ArangoDB in the db: belapi, collection: admin will be used unless
    it is overridden in the process_nanopubstore_into_edges call. The
    start_date will be updated to the date in the response header and stored
    in the arangodb document.

    Args:
        nanopubstore_url: API endpoint for Nanopubstore, e.g.
            <nanopubstore_api>/nanopubs/timed
        start_dt: date string in 1900-01-01T00:00:00.000Z format -
            only nanopubs that are updated on or after that time will be processed
            if not set, check BEL API settings in ArangoDB for last start_dt
            for the nanopubstore_url
    """

    # https://docs.arangodb.com/3.0/AQL/Operations/Update.html
    # UPDATE {"_key": <nanopubstore_api>, "start_date": "2018-02-18T18:24:03Z"} IN admin OPTIONS { ignoreErrors: true }
    #    OPTIONS are to ignore errors when replace creates a new document

    log.info(f'Run pipeline {nanopubstore_api}  {start_dt}')

    # if not start_dt:
    #     start_dt = None
    # if not nanopubstore_api:
    #     nanopubstore_api = config['bel_api']['servers']['nanopubstore']

    # params = {'startTime': start_dt, 'published': true}

    # nanopub_ids = bel.utils.get_url(f'{nanopubstore_api}/nanopubs/timed', params=params)

    # for nanopub_id in nanopub_ids:
    #     nanopub = bel.utils.get_url(f'{nanopubstore_api}/nanopubs/{nanopub_id}')
