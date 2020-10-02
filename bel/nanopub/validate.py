# Standard Library
import copy
import re
from typing import List, Tuple

# Third Party
# Third Party Imports
from loguru import logger

# Local
# Local Imports
import bel.core.settings as settings
import bel.core.utils
import bel.lang.belobj
from bel.belspec.crud import get_latest_version
from bel.db.arangodb import bel_db, bel_validations_coll, bel_validations_name
from bel.db.elasticsearch import es
from bel.schemas.bel import AssertionStr, ValidationError, ValidationErrors
from bel.schemas.nanopubs import NanopubR


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

    assertion_str = f'{assertion.get("subject", "")} {assertion.get("relation", "")} {assertion.get("object", "")}'
    assertion_str = assertion_str.replace("None", "")
    assertion_str = assertion_str.rstrip()

    return assertion_str


def get_cached_assertion_validations(assertions, validation_level):
    """ Collect cached validations for assertions"""

    # Get hash keys for missing validations
    hashes = []
    for idx, assertion in enumerate(assertions):

        if (
            not assertion.get("validation", False)
            or assertion["validation"]["status"] == "Processing"
        ):

            assertion["str"] = get_assertion_str(assertion)
            assertion["hash"] = get_hash(assertion["str"])
            hashes.append(assertion["hash"])

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

    doc = {
        "_key": hash_key,
        "validation": validation.dict(),
        "created_dt": bel.core.utils.dt_utc_formatted(),
    }

    bel_validations_coll.insert(doc, overwrite=True, silent=True)


def validate_assertion(assertion_obj: AssertionStr, *, version: str = "latest"):
    """ Validate single assertion """

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

    # Add status to validation object to make it easy to highlight errors/warnings in the UI
    validation_status = "Good"
    for error in bo.ast.errors:
        if error.severity == "Error" and validation_status != "Error":
            validation_status = "Error"

        elif error.severity == "Warning" and validation_status != "Error":
            validation_status = "Warning"

    if not validation_status:
        validation_status = "Good"

    if errors == []:
        errors = None

    validation = ValidationErrors(
        status=validation_status, validation_target=assertion_obj.entire, errors=errors
    )

    # Cache validation
    assertion_hash = get_hash(assertion_obj.entire)
    save_validation_by_hash(assertion_hash, validation)

    return validation.dict(exclude={"validation_target"}, exclude_none=True)


def validate_assertions(
    assertions: List[dict], *, version: str = "latest", validation_level: str = "complete"
):
    """Validate assertions

    Args:
        assertions (List[dict]): List of assertion objects
        validation_level:   complete - fill in any missing assertion/annotation validations
                            force - redo all validations
                            cached - only return cached/pre-generated validations
    """

    for idx, assertion in enumerate(assertions):
        if not assertion.get("validation", False) or not assertion["validation"].get(
            "status", False
        ):
            assertions[idx]["validation"] = {"status": "Processing"}

    # Process missing validations only
    if validation_level != "force":
        assertions = get_cached_assertion_validations(assertions, validation_level)

    for idx, assertion in enumerate(assertions):
        assertion_obj = AssertionStr(
            subject=assertion.get("subject", ""),
            relation=assertion.get("relation", ""),
            object=assertion.get("object", ""),
        )

        if (
            not assertion.get("validation", False)
            or assertion["validation"]["status"] == "Processing"
        ):
            assertions[idx]["validation"] = validate_assertion(assertion_obj, version=version)

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

            annotations[idx] = copy.deepcopy(annotation)

        annotation.pop("hash", "")
        annotation.pop("str", "")

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

    validation = ValidationErrors(status="Good")

    term_key = annotation["id"]
    terms = bel.terms.terms.get_terms(term_key)

    matched_term = None
    for term in terms:
        if term_key == term.key:
            matched_term = term
        elif matched_term is None and term_key in term.alt_keys:
            matched_term = term

    if matched_term is None:
        for term in terms:
            if term_key in term.obsolete_keys:
                matched_term = term

                validation.status = "Warning"
                if validation.errors is None:
                    validation.errors = []
                validation.errors.append(
                    ValidationError(
                        type="Annotation",
                        severity="Warning",
                        msg=f"Annotation term {term_key} is obsolete - please replace with {matched_term.key}",
                    )
                )

    if matched_term is not None and annotation["type"] not in matched_term.annotation_types:

        validation.status = "Warning"
        if validation.errors is None:
            validation.errors = []
        validation.errors.append(
            ValidationError(
                type="Annotation",
                severity="Warning",
                msg=f'Annotation type: {annotation["type"]} for {term_key} does not match annotation types in database: {matched_term.annotation_types}',
            )
        )

    elif matched_term is None:
        validation.status = "Warning"
        if validation.errors is None:
            validation.errors = []
        validation.errors.append(
            ValidationError(
                type="Annotation",
                severity="Warning",
                msg=f"Annotation term: {term_key} not found in Namespace database",
            )
        )

    save_validation_by_hash(annotation_hash, validation)

    annotation["validation"] = validation.dict(exclude={"validation_target"}, exclude_none=True)

    return annotation


def validate_annotations(annotations: List[dict], validation_level: str):
    """Validate annotations

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
        nanopub = nanopub.dict(exclude_unset=True, exclude_none=True)

    # Validation results
    validation = ValidationErrors()

    # Structural checks ####################################################################
    # Missing nanopub key in nanopub object
    if "nanopub" not in nanopub:

        validation.status = "Error"
        if validation.errors is None:
            validation.errors = []

        validation.errors.append(
            ValidationError(
                type="Nanopub", severity="Error", msg="Must have top-level nanopub key in object"
            )
        )

        nanopub["nanopub"]["metadata"]["gd_validation"] = validation.dict()

        return nanopub

    assertions = nanopub["nanopub"].get("assertions", [])
    if not assertions:
        if validation.errors is None:
            validation.errors = []
        validation.errors.append(
            ValidationError(
                type="Nanopub",
                severity="Error",
                msg="Assertions are required and must be a list/array",
            )
        )

    original_version = nanopub["nanopub"].get("type", {}).get("version", "latest")
    version = bel.belspec.crud.check_version(original_version)
    if original_version != "latest" and original_version != version:
        nanopub["nanopub"]["type"]["version"] = version

    # Check Citation object ####################################################################
    if not nanopub["nanopub"].get("citation", {}):
        if validation.errors is None:
            validation.errors = []
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
        if validation.errors is None:
            validation.errors = []
        validation.errors.append(
            ValidationError(
                type="Nanopub",
                severity="Error",
                msg='nanopub["nanopub"]["citation"] must have either a uri, database or reference key.',
            )
        )

    validation = validation.dict(exclude_none=True)

    nanopub["nanopub"]["metadata"]["gd_validation"] = validation

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

    nanopub = NanopubR(**nanopub)

    return nanopub


@logger.catch
def validate(nanopub: NanopubR, validation_level: str = "complete") -> NanopubR:
    """Validate Nanopub - wrapper for try/except"""

    try:
        nanopub = validate_sections(nanopub, validation_level)

    except Exception as e:
        logger.exception(f"Could not validate nanopub: {nanopub.nanopub.id}  error: {str(e)}")

    return nanopub


def remove_validation_cache():
    """Truncate validation cache"""

    bel_validations_coll.truncate()
