# Standard Library
import copy
import re
from typing import List, Tuple

# Third Party Imports
import structlog

# Local Imports
import bel.db.arangodb as arangodb
import bel.db.elasticsearch
import bel.lang.belobj
import bel.utils
from bel.Config import config

log = structlog.getLogger(__name__)

es = bel.db.elasticsearch.get_client()

client = arangodb.get_client()
belapi_db = arangodb.get_belapi_handle(client)

bel_validations_name = arangodb.bel_validations_name
bel_validation_coll = belapi_db.collection(bel_validations_name)


def convert_msg_to_html(msg):
    """Convert \n into a <BR> for an HTML formatted message"""

    msg = re.sub("\n", "<br />", msg, flags=re.MULTILINE)
    return msg


def get_validation_for_hashes(hashes):
    """Get cached validations from validation cache database in arangodb"""

    hashes_str = '", "'.join(hashes)
    hashes_str = f'"{hashes_str}"'
    query = f"""
        FOR doc IN {bel_validations_name}
            FILTER doc._key in [{hashes_str}]
            RETURN {{ hash: doc._key, validation: doc.validation }}
    """

    validations = {}
    for r in belapi_db.aql.execute(query, batch_size=20):
        validations[r["hash"]] = r["validation"]

    return validations


def get_hash(string: str) -> str:
    """CityHash hash of assertion string"""

    return bel.utils._create_hash(string)


def get_assertion_str(assertion) -> str:

    assertion_str = (
        f'{assertion.get("subject")} {assertion.get("relation", "")} {assertion.get("object", "")}'
    )
    assertion_str = assertion_str.replace("None", "")
    assertion_str = assertion_str.rstrip()

    return assertion_str


def get_cached_assertion_validations(assertions, validation_level, error_level):
    """ Collect cached validations for assertions"""

    # Get hash keys for missing validations
    hashes = []
    for idx, assertion in enumerate(assertions):

        if (
            not assertion.get("validation", False)
            or assertion["validation"]["status"] == "processing"
        ):

            assertion["str"] = get_assertion_str(assertion)
            assertion["hash"] = get_hash(assertion["str"])
            hashes.append(assertion["hash"])

    val_by_hashkey = get_validation_for_hashes(hashes)

    for idx, assertion in enumerate(assertions):
        if assertion.get("hash", "") in val_by_hashkey:
            assertion["validation"] = copy.deepcopy(val_by_hashkey[assertion["hash"]])

            assertion_str = assertion.pop("str")
            assertion_hash = assertion.pop("hash")

            assertions[idx] = copy.deepcopy(assertion)

    return assertions


def save_validation_by_hash(hash_key: str, validation: dict, src: str) -> None:
    """Save validation results to cache

    Args:
        hash_key (str): hash key id
        validation (dict): validation object
        src (str): source string that was validated (annotation or assertion)
    """

    log.info("Save validation", hash_key=hash_key, validation=validation)

    doc = {"_key": hash_key, "validation": validation, "source": src}
    bel_validation_coll.insert(doc, overwrite=True, silent=True)


def validate_assertion(assertion, validation_level: str, error_level: str):
    """ Validate single assertion """

    bel_version = config["bel"]["lang"]["default_bel_version"]
    bo = bel.lang.belobj.BEL(bel_version, config["bel_api"]["servers"]["api_url"])

    if not assertion.get("hash", False):
        assertion_str = get_assertion_str(assertion)
        assertion_hash = get_hash(assertion_str)
    else:
        assertion_str = assertion.get("str", "")
        assertion_hash = assertion.get("hash", "")

    messages: List[Tuple] = []

    log.info("Assertion", assertion=assertion)

    if (
        assertion.get("subject", False) in [False, "", None]
        and assertion.get("relation", False) in [False, "", None]
        and assertion.get("object", False) in [False, "", None]
    ):
        messages.append(("ERROR", "Missing Assertion subject, relation and object"))

    elif not assertion.get("subject", False):
        messages.append(("ERROR", "Missing Assertion subject"))

    elif assertion.get("relation", False) and assertion.get("object", False) in [False, "", None]:
        messages.append(
            (
                "ERROR",
                "Missing Assertion object - if you have a subject and relation - you must have an object.",
            )
        )

    else:
        try:
            messages.extend(
                bo.parse(assertion_str)
                .semantic_validation(error_level=error_level)
                .validation_messages
            )
        except:
            messages.append(("ERROR", f"Could not parse {assertion_str}"))
            log.exception(f"Could not parse: {assertion_str}")

    validation = {"status": "good", "errors": [], "warnings": []}

    for message in messages:
        if message == []:
            continue

        log.info("Validation message", message_=message)

        (level, msg) = message
        if level == "ERROR":
            if validation["status"] != "error":
                validation["status"] = "error"

            validation["errors"].append(
                {
                    "level": f"{level.title()}",
                    "section": "Assertion",
                    "label": f"{level.title()}-Assertion",
                    "msg": msg,
                    "msg_html": convert_msg_to_html(msg),
                }
            )

        elif level == "WARNING":
            if validation["status"] != "error":
                validation["status"] = "warning"
            validation["warnings"].append(
                {
                    "level": f"{level.title()}",
                    "section": "Assertion",
                    "label": f"{level.title()}-Assertion",
                    "msg": msg,
                    "msg_html": convert_msg_to_html(msg),
                }
            )

    assertion["validation"] = copy.deepcopy(validation)
    save_validation_by_hash(assertion_hash, validation, assertion_str)

    assertion_str = assertion.pop("str", "")
    assertion_hash = assertion.pop("hash", "")

    return assertion


def validate_assertions(assertions: List[dict], validation_level: str, error_level: str):
    """ Validate assertions

    Args:
        assertions (List[dict]): List of assertion objects
        validation_level:   complete - fill in any missing assertion/annotation validations
                            force - redo all validations
                            cached - only return cached/pre-generated validations
        error_level:  [ERROR, WARNING] - what types of validation results to return
    """

    for idx, assertion in enumerate(assertions):
        if not assertion.get("validation", False):
            assertions[idx]["validation"] = {"status": "processing"}
        if not assertion["validation"].get("status", False):
            assertions[idx]["validation"] = {"status": "processing"}

    # Process missing validations only
    if validation_level != "force":
        assertions = get_cached_assertion_validations(assertions, validation_level, error_level)

        if validation_level == "complete":
            for idx, assertion in enumerate(assertions):
                if (
                    not assertion.get("validation", False)
                    or assertion["validation"]["status"] == "processing"
                ):
                    assertions[idx] = validate_assertion(assertion, validation_level, error_level)

    # Force validation of all assertions
    else:
        for idx, assertion in enumerate(assertions):

            assertions[idx] = validate_assertion(assertion, validation_level, error_level)

    return assertions


def get_cached_annotation_validations(annotations):
    """ Collect cached validations for annotations"""

    # Get hash keys for missing validations
    hashes = []
    for idx, annotation in enumerate(annotations):

        if (
            not annotation.get("validation", False)
            or annotation["validation"].get("status", "") == "processing"
        ):
            annotation["str"] = get_annotation_str(annotation)
            annotation["hash"] = get_hash(annotation["str"])
            annotations[idx] = copy.deepcopy(annotation)
            hashes.append(annotation["hash"])

    cached_validations = get_validation_for_hashes(hashes)

    for idx, annotation in enumerate(annotations):
        if annotation.get("hash", "") in cached_validations:
            annotation["validation"] = copy.deepcopy(cached_validations[annotation["hash"]])

            annotation.pop("hash", "")
            annotation.pop("annotation_str", "")

            annotations[idx] = copy.deepcopy(annotation)

    return annotations


def get_annotation_str(annotation):

    annotation_str = f"{annotation['type']} {annotation['id']}"
    annotation_str = annotation_str.strip()

    return annotation_str


def validate_annotation(annotation):
    """Check elasticsearch index for annotation term"""

    if not annotation.get("hash", False):
        annotation_str = get_annotation_str(annotation)
        annotation_hash = get_hash(annotation_str)
    else:
        annotation_str = annotation.get("str", "")
        annotation_hash = annotation.get("hash", "")

    search_body = {
        "_source": ["src_id", "id", "name", "label", "annotation_types"],
        "query": {"term": {"id": annotation["id"]}},
    }

    annotation["validation"] = {"status": "good", "warnings": []}
    results = es.search(index="terms", doc_type="term", body=search_body)
    if len(results["hits"]["hits"]) > 0:
        result = results["hits"]["hits"][0]["_source"]
        if annotation["type"] not in result["annotation_types"]:
            annotation["validation"]["status"] = "warning"
            msg = f'Annotation type: {annotation["type"]} for {annotation["id"]} does not match annotation types in database: {result["annotation_types"]}'
            annotation["validation"]["warnings"].append(
                {
                    "level": "Warning",
                    "section": "Annotation",
                    "label": "Warning-Annotation",
                    "msg": msg,
                    "msg_html": msg,
                }
            )
    else:
        msg = f"Annotation term: {annotation['id']} not found in database"
        annotation["validation"]["status"] = "warning"
        annotation["validation"]["warnings"].append(
            {
                "level": "Warning",
                "section": "Annotation",
                "label": "Warning-Annotation",
                "msg": msg,
                "msg_html": msg,
            }
        )

    log.info("Saving annotation", annotation=annotation_str, hash=annotation_hash)

    save_validation_by_hash(annotation_hash, annotation["validation"], annotation_str)

    annotation.pop("hash", "")
    annotation.pop("annotation_str", "")

    return annotation


def validate_annotations(annotations: List[dict], validation_level: str):
    """ Validate annotations

    Args:
        annotations (List[dict]): List of annotation objects
        validation_level:   complete - fill in any missing annotation/annotation validations
                            force - redo all validations
                            cached - only return cached/pre-generated validations
        error_level:  [ERROR, WARNING] - what types of validation results to return
    """

    for idx, annotation in enumerate(annotations):
        if not annotation.get("validation", False):
            annotations[idx]["validation"] = {"status": "processing"}
        if not annotation["validation"].get("status", False):
            annotations[idx]["validation"] = {"status": "processing"}

    # Process missing validations only
    if validation_level != "force":
        annotations = get_cached_annotation_validations(annotations)

        if validation_level == "complete":
            for idx, annotation in enumerate(annotations):
                if (
                    not annotation.get("validation", False)
                    or annotation["validation"].get("status", "") == "processing"
                ):
                    annotations[idx] = validate_annotation(annotation)

    # Force validation of all annotations
    else:
        for idx, annotation in enumerate(annotations):
            annotations[idx] = validate_annotation(annotation)

    return annotations


def validate(nanopub: dict, error_level: str = "WARNING", validation_level: str = "complete"):
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
    Returns:
        list(tuples): [{'level': 'Warning', 'section': 'Assertion', 'label': 'Warning-Assertion', 'index': 0, 'msg': <msg>}]

    """

    # Validation results
    validation_results = []

    bel_version = config["bel"]["lang"]["default_bel_version"]

    # Structural checks
    try:
        if not isinstance(nanopub["nanopub"]["assertions"], list):
            msg = "Assertions must be a list/array"
            validation_results.append(
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
        validation_results.append(
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
        validation_results.append(
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
            validation_results.append(
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
        validation_results.append(
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
        nanopub["nanopub"]["assertions"] = validate_assertions(
            nanopub["nanopub"]["assertions"],
            validation_level=validation_level,
            error_level=error_level,
        )

    # Annotation checks
    if "annotations" in nanopub["nanopub"]:
        nanopub["nanopub"]["annotations"] = validate_annotations(
            nanopub["nanopub"]["annotations"], validation_level=validation_level
        )

    nanopub["nanopub"]["metadata"]["gd_validation"] = copy.deepcopy(validation_results)

    return nanopub
