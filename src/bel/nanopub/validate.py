# Standard Library
import copy
import re
from typing import List, Tuple

# Third Party Imports
from loguru import logger

# Local Imports
import bel.core.settings as settings
import bel.core.utils
import bel.lang.belobj
from bel.belspec.crud import get_latest_version
from bel.db.arangodb import bel_db, bel_validations_coll, bel_validations_name
from bel.db.elasticsearch import es
from bel.schemas.nanopubs import NanopubR
from bel.schemas.bel import AssertionStr, ValidationError, ValidationErrors


def convert_msg_to_html(msg: str):
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
    for r in bel_db.aql.execute(query, batch_size=20):
        validations[r["hash"]] = r["validation"]

    return validations


def get_hash(string: str) -> str:
    """CityHash hash of assertion string"""

    return bel.core.utils._create_hash(string)


def get_assertion_str(assertion) -> str:

    assertion_str = (
        f'{assertion.get("subject")} {assertion.get("relation", "")} {assertion.get("object", "")}'
    )
    assertion_str = assertion_str.replace("None", "")
    assertion_str = assertion_str.rstrip()

    return assertion_str


def get_cached_assertion_validations(assertions, validation_level):
    """ Collect cached validations for assertions"""

    # Get hash keys for missing validations
    hashes = []
    for idx, assertion in enumerate(assertions):

        logger.info(f"Assertion index {idx}  Assertion dict: {assertion}")

        if (
            not assertion.get("validation", False)
            or assertion["validation"]["status"] == "Processing"
        ):

            assertion["str"] = get_assertion_str(assertion)
            assertion["hash"] = get_hash(assertion["str"])
            hashes.append(assertion["hash"])

    logger.info(f"Get assertion validation caches using hashes {hashes}")

    val_by_hashkey = get_validation_for_hashes(hashes)

    for idx, assertion in enumerate(assertions):
        if assertion.get("hash", "") in val_by_hashkey:
            assertion["validation"] = copy.deepcopy(val_by_hashkey[assertion["hash"]])

            assertion.pop("str", "")
            assertion.pop("hash", "")
            assertion["validation"].pop("validation_target", "")

            assertions[idx] = copy.deepcopy(assertion)

    return assertions


def save_validation_by_hash(hash_key: str, validation: ValidationErrors) -> None:
    """Save validation results to cache

    Args:
        hash_key (str): hash key id
        validation (dict): validation object
        src (str): source string that was validated (annotation or assertion)
    """

    doc = {"_key": hash_key, "validation": validation.dict(), "created_dt": bel.core.utils.dt_utc_formatted()}

    bel_validations_coll.insert(doc, overwrite=True, silent=True)


def validate_assertion(assertion, *, version: str, validation_level: str):
    """ Validate single assertion """

    assertion_obj = AssertionStr(
        subject=assertion["subject"], relation=assertion["relation"], object=assertion["object"]
    )

    # Add hash in order to cache validation
    assertion_hash = assertion.get("hash", None)
    if assertion_hash is None:
        assertion_hash = get_hash(assertion_obj.entire)

    bo = bel.lang.belobj.BEL(assertion_obj, version=version)
    bo.ast.validate()

    # Sort errors by severity and where in the Assertion it is found
    errors = sorted(bo.ast.errors, key=lambda x: (x.severity, x.index))

    # Add error visuals from visual_pairs
    for idx, error in enumerate(errors):
        if error.visual_pairs is not None:
            errors[idx].visual = bel.core.utils.html_wrap_span(
                assertion_obj.entire, error.visual_pairs
            )
            errors[idx].visual_pairs = None

    # Create Validation object
    validation = ValidationErrors(validation_target=assertion_obj.entire, errors=errors)

    # Add status to validation object to make it easy to highlight errors/warnings in the UI
    for error in bo.ast.errors:
        if error.severity == "Error" and validation.status != "Error":
            validation.status = "Error"

        elif error.severity == "Warning" and validation.status != "Error":
            validation.status = "Warning"

    assertion["validation"] = validation.dict(
        exclude={"validation_target"}, exclude_unset=True, exclude_none=True
    )
    save_validation_by_hash(assertion_hash, validation)

    return assertion


def validate_assertions(
    assertions: List[dict], *, version: str = "latest", validation_level: str = "complete"
):
    """ Validate assertions

    Args:
        assertions (List[dict]): List of assertion objects
        validation_level:   complete - fill in any missing assertion/annotation validations
                            force - redo all validations
                            cached - only return cached/pre-generated validations
    """

    logger.info(f"Assertions1 {assertions}")

    for idx, assertion in enumerate(assertions):
        if not assertion.get("validation", False) or not assertion["validation"].get("status", False):
            assertions[idx]["validation"] = {"status": "Processing"}

    # Process missing validations only
    if validation_level != "force":
        assertions = get_cached_assertion_validations(assertions, validation_level)

        if validation_level == "complete":
            for idx, assertion in enumerate(assertions):
                if (
                    not assertion.get("validation", False)
                    or assertion["validation"]["status"] == "Processing"
                ):
                    assertions[idx] = validate_assertion(
                        assertion, version=version, validation_level=validation_level
                    )

    # Force validation of all assertions
    else:
        for idx, assertion in enumerate(assertions):

            assertions[idx] = validate_assertion(
                assertion, version=version, validation_level=validation_level
            )

    return assertions


def get_cached_annotation_validations(annotations):
    """ Collect cached validations for annotations"""

    # Get hash keys for missing validations
    hashes = []
    for idx, annotation in enumerate(annotations):

        if (
            not annotation.get("validation", False)
            or annotation["validation"].get("status", "") == "Processing"
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
        annotation_hash = annotation["hash"]

    search_body = {
        "_source": ["src_id", "key", "name", "label", "annotation_types"],
        "query": {"term": {"key": annotation["id"]}},
    }

    validation = ValidationErrors()

    results = es.search(
        index=settings.TERMS_INDEX, doc_type=settings.TERMS_DOCUMENT_TYPE, body=search_body
    )

    if len(results["hits"]["hits"]) > 0:
        result = results["hits"]["hits"][0]["_source"]
        if annotation["type"] not in result["annotation_types"]:
            validation.status = "Warning"
            validation.errors.append(
                ValidationError(
                    type="Annotation",
                    severity="Warning",
                    msg=f'Annotation type: {annotation["type"]} for {annotation["id"]} does not match annotation types in database: {result["annotation_types"]}',
                )
            )
    else:
        validation.status = "Warning"
        validation.errors.append(
            ValidationError(
                type="Annotation",
                severity="Warning",
                msg=f"Annotation term: {annotation['id']} not found in database",
            )
        )

    save_validation_by_hash(annotation_hash, validation)

    annotation["validation"] = validation.dict(exclude={"validation_target"}, exclude_unset=True)

    return annotation


def validate_annotations(annotations: List[dict], validation_level: str):
    """ Validate annotations

    Args:
        annotations (List[dict]): List of annotation objects
        validation_level:   complete - fill in any missing annotation/annotation validations
                            force - redo all validations
                            cached - only return cached/pre-generated validations
    """

    for idx, annotation in enumerate(annotations):
        if not annotation.get("validation", False):
            annotations[idx]["validation"] = {"status": "Processing"}
        if not annotation["validation"].get("status", False):
            annotations[idx]["validation"] = {"status": "Processing"}

    # Process missing validations only
    if validation_level != "force":
        annotations = get_cached_annotation_validations(annotations)

        if validation_level == "complete":
            for idx, annotation in enumerate(annotations):
                if (
                    not annotation.get("validation", False)
                    or annotation["validation"].get("status", "") == "Processing"
                ):
                    annotations[idx] = validate_annotation(annotation)

    # Force validation of all annotations
    else:
        for idx, annotation in enumerate(annotations):
            annotations[idx] = validate_annotation(annotation)

    return annotations


def validate_sections(nanopub: NanopubR, validation_level: str = "complete") -> NanopubR:
    """Validate Nanopub sections"""

    if not isinstance(nanopub, dict):
        nanopub = nanopub.dict()

    # Validation results
    validation = ValidationErrors()

    # Structural checks ####################################################################
    # Missing nanopub key in nanopub object
    if "nanopub" not in nanopub:

        validation.status = "Error"
        validation.errors.append(
            ValidationError(
                type="Nanopub", severity="Error", msg="Must have top-level nanopub key in object"
            )
        )

        nanopub["nanopub"]["metadata"]["gd_validation"] = validation.dict()

        return nanopub

    assertions = nanopub["nanopub"].get("assertions", [])
    if not assertions:
        validation.errors.append(
            ValidationError(
                type="Nanopub",
                severity="Error",
                msg="Assertions are required and must be a list/array",
            )
        )

    version = nanopub["nanopub"].get("type", {}).get("version", "latest")
    version = bel.belspec.crud.check_version(version)

    # Check Citation object ####################################################################
    if not nanopub["nanopub"].get("citation", {}):
        validation.errors.append(
            ValidationError(
                type="Nanopub",
                severity="Error",
                msg='nanopub["nanopub"] object must have a "citation" key with either a uri, database or reference key.',
            )
        )

    for key in ["id", "uri", "database", "reference"]:
        if key in nanopub["nanopub"].get("citation", {}).keys():
            break
    else:
        validation.errors.append(
            ValidationError(
                type="Nanopub",
                severity="Error",
                msg='nanopub["nanopub"]["citation"] must have either a uri, database or reference key.',
            )
        )
    # Assertion checks ############################################################################
    if "assertions" in nanopub["nanopub"]:
        nanopub["nanopub"]["assertions"] = validate_assertions(
            nanopub["nanopub"]["assertions"], version=version, validation_level=validation_level
        )

    # Annotation checks ###########################################################################
    if "annotations" in nanopub["nanopub"]:
        nanopub["nanopub"]["annotations"] = validate_annotations(
            nanopub["nanopub"]["annotations"], validation_level=validation_level
        )

    nanopub["nanopub"]["metadata"]["gd_validation"] = validation.dict(exclude_none=True)

    return nanopub


def validate(nanopub: NanopubR, validation_level: str = "complete") -> NanopubR:
    """Validate Nanopub - wrapper for try/except"""

    try:
        nanopub = validate_sections(nanopub, validation_level)

    except Exception as e:
        logger.warning(
            f"Could not validate nanopub: {nanopub.get('_key', 'Unknown')}  error: {str(e)}"
        )

    return nanopub
