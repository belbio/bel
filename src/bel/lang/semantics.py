# Semantic validation code

# Standard Library
import re
from typing import List, Tuple

# Third Party Imports
from loguru import logger

# Local Imports
import bel.terms.terms
from bel.belspec.crud import get_enhanced_belspec
from bel.core.utils import http_client, url_path_param_quoting
from bel.lang.ast import BELAst, Function, NSArg, StrArg


def validate(bo, error_level: str = "WARNING") -> Tuple[bool, List[Tuple[str, str]]]:
    """Semantically validate BEL AST

    Add errors and warnings to bel_obj.validation_messages

    Error Levels are similar to log levels - selecting WARNING includes both
    WARNING and ERROR, selecting ERROR just includes ERROR

    Args:
        bo: main BEL language object
        error_level: return ERRORs only or also WARNINGs

    Returns:
        Tuple[bool, List[Tuple[str, str]]]: (is_valid, messages)
    """

    if bo.ast:
        bo = validate_functions(bo.ast, bo)  # No WARNINGs generated in this function
        if error_level == "WARNING":
            bo = validate_arg_values(bo.ast, bo)  # validates NSArg and StrArg values

    else:
        # Don't show general error if more specific error is already added
        errors = [error for error in bo.validation_messages if error[0] == "ERROR"]
        if not errors:
            bo.validation_messages.append(("ERROR", "Invalid BEL Assertion - cannot parse"))

    for msg in bo.validation_messages:
        if msg[0] == "ERROR":
            bo.parse_valid = False
            break

    return bo


def validate_functions(ast: BELAst, bo):
    """Recursively validate function signatures

    Determine if function matches one of the available signatures. Also,

    1. Add entity types to AST NSArg, e.g. Abundance, ...
    2. Add optional to  AST Arg (optional means it is not a
        fixed, required argument and needs to be sorted for
        canonicalization, e.g. reactants(A, B, C) )

    Args:
        bo: bel object

    Returns:
        bel object
    """

    belspec = bo.ast.belspec

    if isinstance(ast, Function):
        logger.debug(f"Validating: {ast.name}, {ast.function_type}, {ast.args}")
        function_signatures = belspec["functions"]["signatures"][ast.name]["signatures"]

        function_name = ast.name
        (valid_function, messages) = check_function_args(
            ast.args, function_signatures, function_name
        )
        if not valid_function:
            message = ", ".join(messages)
            bo.validation_messages.append(
                (
                    "ERROR",
                    "Invalid BEL Assertion function {} - problem with function signatures: {}".format(
                        ast.to_string(), message
                    ),
                )
            )
            bo.parse_valid = False

    # Recursively process every NSArg by processing BELAst and Functions
    if hasattr(ast, "args"):
        for arg in ast.args:
            validate_functions(arg, bo)

    return bo


def check_function_args(args, signatures, function_name):
    """Check function args - return message if function args don't match function signature

    Called from validate_functions

    We have following types of arguments to validate:
        1. Required, position_dependent arguments, e.g. p(HGNC:AKT1), NSArg HGNC:AKT1 is required and must be first argument
        2. Optional, position_dependent arguments, e.g. pmod(P, T, 308) - T and 308 are optional and position_dependent
        3. Optional, e.g. loc() modifier can only be found once, but anywhere after the position_dependent arguments
        4. Multiple, e.g. var(), can have more than one var() modifier in p() function

    Args:
        args (Union['Function', 'NSArg', 'StrArg']): AST Function arguments
        signatures (Mapping[str, Any]): function signatures from spec_dict, may be more than one per function
        function_name (str): passed in to improve error messaging

    Returns:
        Tuple[bool, List[str]]: (function_valid?, list of error messages per signature)
    """

    messages = []

    arg_types = []
    for arg in args:
        logger.info("Arg", arg=arg)
        if arg.type == "Function":
            arg_types.append((arg.name, ""))
        elif arg.type == "NSArg":
            arg_types.append((arg.type, arg.value_types))
        elif arg.type == "StrArg":
            arg_types.append((arg.type, arg.value))
    logger.info(f"Arg_types {arg_types}")

    matched_signature_idx = -1
    valid_function = False
    for sig_argset_idx, sig_argset in enumerate(signatures):
        sig_req_args = sig_argset["req_args"]  # required position_dependent arguments
        sig_pos_args = sig_argset["pos_args"]  # optional position_dependent arguments
        sig_opt_args = sig_argset["opt_args"]  # optional arguments
        sig_mult_args = sig_argset["mult_args"]  # multiple arguments

        logger.debug(f"{sig_argset_idx} Req: {sig_req_args}")
        logger.debug(f"{sig_argset_idx} Pos: {sig_pos_args}")
        logger.debug(f"{sig_argset_idx} Opt: {sig_opt_args}")
        logger.debug(f"{sig_argset_idx} Mult: {sig_mult_args}")

        # Check required arguments
        reqs_mismatch_flag = False
        for sig_idx, sig_req in enumerate(sig_req_args):
            if len(arg_types) > sig_idx:
                logger.debug(
                    "Req args: arg_type {} vs sig_req {}".format(arg_types[sig_idx][0], sig_req)
                )
                if arg_types[sig_idx][0] not in sig_req:
                    reqs_mismatch_flag = True
                    msg = f"Missing required arguments for {function_name} signature: {sig_argset_idx}"
                    messages.append(msg)
                    logger.debug(msg)
                    break

        if reqs_mismatch_flag:
            continue  # test next argset

        # Check position_dependent optional arguments
        pos_dep_arg_types = arg_types[len(sig_req_args) :]
        logger.debug(f"Optional arg types {pos_dep_arg_types}")
        logger.debug(f"{sig_argset_idx} Pos: {sig_pos_args}")
        pos_mismatch_flag = False
        for sig_pos_idx, sig_pos in enumerate(sig_pos_args):
            if sig_pos_idx == len(pos_dep_arg_types):
                break  # stop checking position dependent arguments when we run out of them vs signature optional position dependent arguments
            if pos_dep_arg_types[sig_pos_idx][0] not in sig_pos:
                pos_mismatch_flag = True
                msg = f"Missing position_dependent arguments for {function_name} signature: {sig_argset_idx}"
                messages.append(msg)
                logger.debug(msg)
                break
        if pos_mismatch_flag:
            continue  # test next argset

        reqpos_arglen = len(sig_req_args) + len(sig_pos_args)
        optional_arg_types = arg_types[reqpos_arglen:]

        # Remove function args that are found in the mult_args signature
        optional_types = [
            (opt_type, opt_val)
            for opt_type, opt_val in optional_arg_types
            if opt_type not in sig_mult_args
        ]
        logger.debug(f"Optional types after sig mult args removed {optional_types}")

        # Check if any remaining function args are duplicated and therefore not unique opt_args
        if len(optional_types) != len(set(optional_types)):
            msg = f"Duplicate optional arguments {optional_types} for {function_name} signature: {sig_argset_idx}"
            messages.append(msg)
            logger.debug(msg)
            continue

        optional_types = [
            (opt_type, opt_val)
            for opt_type, opt_val in optional_types
            if opt_type not in sig_opt_args
        ]
        if len(optional_types) > 0:
            msg = f"Invalid arguments {optional_types} for {function_name} signature: {sig_argset_idx}"
            messages.append(msg)
            logger.debug(msg)
            continue

        matched_signature_idx = sig_argset_idx
        messages = []  # reset messages if signature is matched
        valid_function = True
        break

    # Add NSArg and StrArg value types (e.g. Protein, Complex, ec)
    if matched_signature_idx > -1:
        # Shouldn't have single optional NSArg arguments - not currently checking for that
        logger.debug(f'AST1, Sigs {signatures[matched_signature_idx]["arguments"]}  Args: {args}')
        for arg_idx, arg in enumerate(args):
            logger.debug(f"Arg type {arg.type}")
            for sig_idx, sig_arg in enumerate(signatures[matched_signature_idx]["arguments"]):
                if arg.type == "Function" or sig_arg["type"] in ["Function", "Modifier"]:
                    pass  # Skip Function arguments
                elif sig_arg.get("position", None):
                    if sig_arg["position"] == arg_idx:
                        logger.debug("1Adding value_types", arg=arg, value_type=sig_arg["values"])
                        arg.add_value_types(sig_arg["values"])
                        logger.debug(f'AST2  {arg} {sig_arg["values"]}')
                elif arg.type in ["NSArg", "StrArg", "StrArgNSArg"]:
                    logger.debug("2Adding value_types", arg=arg, value_type=sig_arg["values"])
                    arg.add_value_types(sig_arg["values"])
                    logger.debug(f'AST2  {arg} {sig_arg["values"]}')

    for arg in args:
        if arg.__class__.__name__ in ["NSArg", "StrArg"]:
            logger.debug(f"Arg: {arg.to_string()} Value_types: {arg.value_types}")

    return (valid_function, messages)


def validate_arg_values(ast, bo):
    """Recursively validate arg (NSArg and StrArg) values

    Check that NSArgs are found in BELbio API and match appropriate entity_type.
    Check that StrArgs match their value - either default namespace or regex string

    Generate a WARNING if not.

    Args:
        bo: bel object

    Returns:
        bel object
    """

    logger.debug(f"AST: {ast}")

    belspec = bo.ast.belspec

    # Test NSArg terms
    if isinstance(ast, NSArg):

        term_id = str(ast.entity)

        value_types = ast.value_types
        logger.debug(f"Value types: {value_types}  AST value: {ast.entity.id}")
        # Default namespaces are defined in the bel_specification file
        if ast.entity.namespace == "DEFAULT":  # may use the DEFAULT namespace or not
            for value_type in value_types:
                default_namespace = [
                    ns["name"] for ns in belspec["namespaces"][value_type]["info"]
                ] + [ns["abbreviation"] for ns in belspec["namespaces"][value_type]["info"]]

                if ast.entity.id in default_namespace:
                    logger.debug("Default namespace valid term: {}".format(term_id))
                    break
            else:  # if for loop doesn't hit the break, run this else
                logger.debug("Default namespace invalid term: {}".format(term_id))
                bo.validation_messages.append(("WARNING", f"Default Term: {term_id} not found"))

        # Process normal, non-default-namespace terms
        else:
            terms = bel.terms.terms.get_terms(term_id)
            if len(terms) > 0:
                term = terms[0]
            else:
                term = {}

            # Check that entity types match
            if len(set(ast.value_types).intersection(term.get("entity_types", []))) == 0:
                logger.debug(
                    f"Invalid Term - Assertion term {term_id} allowable entity types: {ast.value_types} do not match API term entity types: {term.get('entity_types', [])}"
                )

                bo.validation_messages.append(
                    (
                        "WARNING",
                        f"Invalid Term - Assertion term {term_id} allowable entity types: {ast.value_types} do not match API term entity types: {term.get('entity_types', [])}",
                    )
                )

                if term_id in term.get("obsolete_keys", []):
                    bo.validation_messages.append(
                        ("WARNING", f'Obsolete term: {term_id}  Current term: {term["id"]}')
                    )

    # Process StrArgs
    if isinstance(ast, StrArg):
        logger.debug(f"  Check String Arg: {ast.value}  {ast.value_types}")
        for value_type in ast.value_types:
            # Is this a regex to match against
            if re.match("/", value_type):
                value_type = re.sub("^/", "", value_type)
                value_type = re.sub("/$", "", value_type)
                match = re.match(value_type, ast.value)
                if match:
                    break
            if value_type in belspec["namespaces"]:
                default_namespace = [
                    ns["name"] for ns in belspec["namespaces"][value_type]["info"]
                ] + [ns["abbreviation"] for ns in belspec["namespaces"][value_type]["info"]]
                if ast.value in default_namespace:
                    break
        else:  # If for loop doesn't hit the break, no matches found, therefore for StrArg value is bad
            bo.validation_messages.append(
                (
                    "WARNING",
                    f"String value {ast.value} does not match default namespace value or regex pattern: {ast.value_types}",
                )
            )

    # Recursively process every NSArg by processing BELAst and Functions
    if hasattr(ast, "args"):
        for arg in ast.args:
            validate_arg_values(arg, bo)

    return bo
