from typing import Tuple
import re

import bel.db.elasticsearch
import bel.lang.belobj
from bel.Config import config

import structlog

log = structlog.getLogger(__name__)

es = bel.db.elasticsearch.get_client()


def convert_msg_to_html(msg):
    """Convert \n into a <BR> for an HTML formatted message"""

    msg = re.sub("\n", "<br />", msg, flags=re.MULTILINE)
    return msg


def validate(nanopub: dict, error_level: str = "WARNING") -> Tuple[str, str, str]:
    """Validate Nanopub

    Error Levels are similar to log levels - selecting WARNING includes both
    WARNING and ERROR, selecting ERROR just includes ERROR

    The validation result is a list of objects containing
        {
            'level': 'Warning|Error',
            'section': 'Assertion|Annotation|Structure',
            'label': '{Error|Warning}-{Assertion|Annotation|Structure}',  # to be used for faceting in Elasticsearch
            'index': idx,  # Index of Assertion or Annotation in Nanopub - starts at 0
            'msg': msg,  # Error or Warning message
        }

    Args:
        nanopub: nanopub record starting with nanopub...
        level: return WARNING or just ERROR?  defaults to warnings and errors
    Returns:
        list(tuples): [{'level': 'Warning', 'section': 'Assertion', 'label': 'Warning-Assertion', 'index': 0, 'msg': <msg>}]

    """

    # Validation results
    v = []

    bel_version = config["bel"]["lang"]["default_bel_version"]

    # Structural checks
    try:
        if not isinstance(nanopub["nanopub"]["assertions"], list):
            msg = "Assertions must be a list/array"
            v.append(
                {
                    "level": "Error",
                    "section": "Structure",
                    "label": "Error-Structure",
                    "msg": msg,
                    "msg_html": msg,
                }
            )
    except Exception as e:
        msg = 'Missing nanopub["nanopub"]["assertions"]'
        v.append(
            {
                "level": "Error",
                "section": "Structure",
                "label": "Error-Structure",
                "msg": msg,
                "msg_html": msg,
            }
        )

    try:
        if "name" in nanopub["nanopub"]["type"] and "version" in nanopub["nanopub"]["type"]:
            pass
        if nanopub["nanopub"]["type"]["name"].upper() == "BEL":
            bel_version = nanopub["nanopub"]["type"]["version"]

    except Exception as e:
        msg = 'Missing or badly formed type - must have nanopub["nanopub"]["type"] = {"name": <name>, "version": <version}'
        v.append(
            {
                "level": "Error",
                "section": "Structure",
                "label": "Error-Structure",
                "msg": msg,
                "msg_html": msg,
            }
        )

    try:
        for key in ["uri", "database", "reference"]:
            if key in nanopub["nanopub"]["citation"]:
                break
        else:
            msg = (
                'nanopub["nanopub"]["citation"] must have either a uri, database or reference key.'
            )
            v.append(
                {
                    "level": "Error",
                    "section": "Structure",
                    "label": "Error-Structure",
                    "msg": msg,
                    "msg_html": msg,
                }
            )
    except Exception as e:
        msg = 'nanopub["nanopub"] must have a "citation" key with either a uri, database or reference key.'
        v.append(
            {
                "level": "Error",
                "section": "Structure",
                "label": "Error-Structure",
                "msg": msg,
                "msg_html": msg,
            }
        )

    # Assertion checks
    if "assertions" in nanopub["nanopub"]:
        for idx, assertion in enumerate(nanopub["nanopub"]["assertions"]):
            bo = bel.lang.belobj.BEL(bel_version, config["bel_api"]["servers"]["api_url"])
            belstr = f'{assertion.get("subject")} {assertion.get("relation", "")} {assertion.get("object", "")}'
            belstr = belstr.replace("None", "")
            try:
                messages = (
                    bo.parse(belstr)
                    .semantic_validation(error_level=error_level)
                    .validation_messages
                )

                for message in messages:
                    (level, msg) = message
                    if error_level == "ERROR":
                        if level == "ERROR":
                            v.append(
                                {
                                    "level": f"{level.title()}",
                                    "section": "Assertion",
                                    "label": f"{level.title()}-Assertion",
                                    "index": idx,
                                    "msg": msg,
                                    "msg_html": convert_msg_to_html(msg),
                                }
                            )
                    else:
                        v.append(
                            {
                                "level": f"{level.title()}",
                                "section": "Assertion",
                                "label": f"{level.title()}-Assertion",
                                "index": idx,
                                "msg": msg,
                                "msg_html": convert_msg_to_html(msg),
                            }
                        )

            except Exception as e:
                msg = f"Could not parse: {belstr}"
                v.append(
                    {
                        "level": "Error",
                        "section": "Assertion",
                        "label": "Error-Assertion",
                        "index": idx,
                        "msg": msg,
                        "msg_html": msg,
                    }
                )
                log.exception(f"Could not parse: {belstr}")

    # Annotation checks
    if error_level == "WARNING":
        for idx, annotation in enumerate(nanopub["nanopub"].get("annotations", [])):
            term_type = annotation["type"]
            term_id = annotation["id"]
            # term_label = annotation['label']
            log.info(f"Annotation: {term_type}  ID: {term_id}")

            search_body = {
                "_source": ["src_id", "id", "name", "label", "annotation_types"],
                "query": {"term": {"id": term_id}},
            }

            results = es.search(index="terms", doc_type="term", body=search_body)
            if len(results["hits"]["hits"]) > 0:
                result = results["hits"]["hits"][0]["_source"]
                if term_type not in result["annotation_types"]:
                    msg = f'Annotation type: {term_type} for {term_id} does not match annotation types in database: {result["annotation_types"]}'
                    v.append(
                        {
                            "level": "Warning",
                            "section": "Annotation",
                            "index": idx,
                            "label": "Warning-Annotation",
                            "msg": msg,
                            "msg_html": msg,
                        }
                    )
            else:
                msg = f"Annotation term: {term_id} not found in database"
                v.append(
                    {
                        "level": "Warning",
                        "section": "Annotation",
                        "index": idx,
                        "label": "Warning-Annotation",
                        "msg": msg,
                        "msg_html": msg,
                    }
                )

    return v
