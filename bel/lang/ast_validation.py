# Standard Library
import re
from typing import TYPE_CHECKING, List, Optional

# Local
from bel.lang.ast_utils import compare_fn_args, intersect, match_signatures
from bel.schemas.bel import (
    AssertionStr,
    BelEntity,
    FunctionSpan,
    Key,
    NsArgSpan,
    NsVal,
    Pair,
    Span,
    ValidationError,
)
from bel.schemas.constants import strarg_validation_lists

if TYPE_CHECKING:
    # Local
    from bel.lang.ast import Function


def check_str_arg(value: str, check_values: List[str]) -> Optional[str]:
    """Check StrArg value"""

    regex_flag = False
    for check_value in check_values:
        if re.match("/", check_value):
            # TODO - figure out how to make this work
            # regex_flag = True
            # print("Check value", check_value)
            # match = re.match(r""+check_value, value)
            # if match:
            #     break
            regex_flag = True
            break

        elif (
            check_value in strarg_validation_lists and value in strarg_validation_lists[check_value]
        ):
            break

    else:
        if regex_flag:
            return f"String Argument {value} doesn't match required format: {repr(check_values)}"
        else:
            return f"String Argument {value} not found in {check_values} default BEL namespaces"

    return None


def validate_function(
    fn: "Function", errors: List[ValidationError] = None
) -> List[ValidationError]:
    """Validate function"""

    # logger.debug(f"Validating function name {fn.name}, len: {len(fn.args)}")

    if errors is None:
        errors = []

    # Check for completely missing arguments
    if len(fn.args) == 0:
        errors.append(
            ValidationError(
                type="Assertion",
                severity="Error",
                msg=f"No arguments in function: {fn.name}",
                visual_pairs=[(fn.span.start, fn.span.end)],
                index=fn.span.start,
            )
        )
        return errors

    signatures = fn.function_signature["signatures"]

    # Select signature from signatures
    if len(signatures) > 1:
        signature = match_signatures(fn.args, signatures)
    else:
        signature = signatures[0]

    if not signature:
        errors.append(
            ValidationError(
                type="Assertion",
                severity="Error",
                msg=f"Could not match function: {fn.name} arguments to BEL Specification",
                visual_pairs=[(fn.span.start, fn.span.end)],
                index=fn.span.start,
            )
        )
        return errors

    # 1 past the last positional element (including optional elements if they exist)
    post_positional = 0

    # First pass - check required positional arguments
    fn_max_args = len(fn.args) - 1
    for argument in signature["arguments"]:
        if argument["position"] is not None and argument["optional"] == False:
            position = argument["position"]

            # Arg type mis-match
            if position > fn_max_args:
                errors.append(
                    ValidationError(
                        type="Assertion",
                        severity="Error",
                        msg=f"Missing required argument - type: {argument['type']}",
                        visual_pairs=[(fn.span.start, fn.span.end)],
                        index=fn.span.start,
                    )
                )

            # elif (
            #     fn.args[position]
            #     and fn.args[position].type == "Function"
            #     and fn.args[position].function_type not in argument["type"]
            # ):
            #     errors.append(
            #         ValidationError(
            #             type="Assertion",
            #             severity="Error",
            #             msg=f"Incorrect function type '{fn.args[position].type}' at position: {position} for function: {fn.name}, should be one of {argument['type']}",
            #             visual_pairs=[(fn.args[position].span.start, fn.args[position].span.end)],
            #             index=fn.args[position].span.start,
            #         )
            #     )

            # Function name mis-match
            elif (
                fn.args[position]
                and fn.args[position].type == "Function"
                and not (fn.args[position].name in argument["values"])
            ):
                errors.append(
                    ValidationError(
                        type="Assertion",
                        severity="Error",
                        msg=f"Incorrect function for argument '{fn.args[position].name}' at position: {position} for function: {fn.name}",
                        visual_pairs=[(fn.args[position].span.start, fn.args[position].span.end)],
                        index=fn.args[position].span.start,
                    )
                )

            # Wrong [non-function] argument type
            elif (
                fn.args[position]
                and fn.args[position].type != "Function"
                and fn.args[position].type not in argument["type"]
            ):
                errors.append(
                    ValidationError(
                        type="Assertion",
                        severity="Error",
                        msg=f"Incorrect argument type '{fn.args[position].type}' at position: {position} for function: {fn.name}, should be one of {argument['type']}",
                        visual_pairs=[(fn.args[position].span.start, fn.args[position].span.end)],
                        index=fn.args[position].span.start,
                    )
                )

            post_positional = position + 1

    # Checking optional positional arguments - really just adjusting post_positional value
    for argument in signature["arguments"]:
        if argument["position"] is not None and argument["optional"] == True:
            position = argument["position"]

            if position > fn_max_args:
                break

            if argument["type"] == ["StrArgNSArg"]:
                argument["type"].extend(["NSArg", "StrArg"])

            if (  # Function match
                fn.args[position].type == "Function"
                and fn.args[position].name in argument["values"]
            ) or (  # NSArg/StrArg type match
                fn.args[position].type in ["NSArg", "StrArg"]
                and fn.args[position].type in argument["type"]
            ):
                post_positional = position + 1

    # Second pass optional, single arguments (e.g. loc(), ma())
    opt_args = signature["opt_args"]
    check_opt_args = {}
    problem_opt_args = set()
    for fn_arg in fn.args[post_positional:]:
        if fn_arg.type == "Function" and fn_arg.name in opt_args:
            if fn_arg.name in check_opt_args:
                problem_opt_args.add(fn_arg.name)
            else:
                check_opt_args[fn_arg.name] = 1

    problem_opt_args = list(problem_opt_args)
    if len(problem_opt_args) > 0:
        errors.append(
            ValidationError(
                type="Assertion",
                severity="Error",
                msg=f"Can only have at most one {problem_opt_args} in function arguments",
                visual_pairs=[(fn.span.start, fn.span.end)],
                index=fn.span.start,
            )
        )

    # Third pass - non-positional (primary/modifier) args that don't show up in opt_args or mult_args
    opt_and_mult_args = opt_args + signature["mult_args"]
    for fn_arg in fn.args[post_positional:]:
        if fn_arg.type == "Function" and fn_arg.name not in opt_and_mult_args:
            errors.append(
                ValidationError(
                    type="Assertion",
                    severity="Error",
                    msg=f"Function {fn_arg.name} is not allowed as an optional or multiple argument",
                    visual_pairs=[(fn.span.start, fn.span.end)],
                    index=fn.span.start,
                )
            )

        # This handles complex(NSArg, p(X)) validation and virtual namespaces
        elif (
            fn_arg.type == "NSArg"
            and fn_arg.entity.entity_types
            and not intersect(fn_arg.entity.entity_types, opt_and_mult_args)
        ):
            errors.append(
                ValidationError(
                    type="Assertion",
                    severity="Error",
                    msg=f"BEL Entity: {fn_arg.entity.nsval} with entity_types {fn_arg.entity.entity_types} are not allowed for function {fn_arg.parent.name} as an optional or multiple argument",
                    visual_pairs=[(fn.span.start, fn.span.end)],
                    index=fn.span.start,
                )
            )

        elif fn_arg.type == "NSArg" and (
            fn_arg.entity.entity_types is None or fn_arg.entity.entity_types == []
        ):
            errors.append(
                ValidationError(
                    type="Assertion",
                    severity="Warning",
                    msg=f"Unknown BEL Entity {fn_arg.entity.nsval.key_label} - cannot determine if this matches function signature",
                    visual_pairs=[(fn.span.start, fn.span.end)],
                    index=fn.span.start,
                )
            )

    # Fourth pass - positional NSArg entity_types checks
    for argument in signature["arguments"]:
        if argument["position"] is not None:
            position = argument["position"]

            if position > fn_max_args:
                break

            if (
                fn.args[position].type == "NSArg"
                and argument["type"] in ["NSArg", "StrArgNSArg"]
                and not fn.args[position].entity.namespace_metadata
            ):
                errors.append(
                    ValidationError(
                        type="Assertion",
                        severity="Warning",
                        msg=f"Unknown BEL Entity '{fn.args[position].entity.nsval.key_label}' for the {fn.name} function at position {fn.args[position].span.namespace.start}",
                        visual_pairs=[
                            (
                                fn.args[position].span.namespace.start,
                                fn.args[position].span.namespace.end,
                            )
                        ],
                        index=fn.args[position].span.namespace.start,
                    )
                )

            elif (
                fn.args[position].type == "NSArg"
                and argument["type"] in ["NSArg", "StrArgNSArg"]
                and not (
                    intersect(
                        fn.args[position].entity.get_entity_types(), argument["values"] + ["All"]
                    )
                )
            ):

                if fn.args[position].entity.term:
                    error_msg = f"Wrong entity type for BEL Entity at argument position {position} for function {fn.name} - expected {argument['values']}, actual: entity_types: {fn.args[position].entity.entity_types}"
                else:
                    error_msg = f"Unknown BEL Entity at argument position {position} for function {fn.name} - cannot determine if correct entity type."

                errors.append(
                    ValidationError(
                        type="Assertion",
                        severity="Warning",
                        msg=error_msg,
                        visual_pairs=[(fn.args[position].span.start, fn.args[position].span.end)],
                        index=fn.args[position].span.start,
                    )
                )

    # Fifth pass - positional StrArg checks
    for argument in signature["arguments"]:
        if argument["position"] is not None:
            position = argument["position"]

            if position > fn_max_args:
                break

            if fn.args[position].type == "StrArg" and argument["type"] in ["StrArg", "StrArgNSArg"]:
                str_error = check_str_arg(fn.args[position].value, argument["values"])

                if str_error is not None:
                    errors.append(
                        ValidationError(
                            type="Assertion",
                            severity="Error",
                            msg=str_error,
                            visual_pairs=[
                                (fn.args[position].span.start, fn.args[position].span.end)
                            ],
                            index=fn.args[position].span.start,
                        )
                    )
    # Sixth pass - non-positional StrArgs are errors
    for idx, arg in enumerate(fn.args):
        if arg.type == "StrArg" and (
            idx > len(signature["arguments"]) - 1 or signature["arguments"][idx]["position"] is None
        ):
            errors.append(
                ValidationError(
                    type="Assertion",
                    severity="Error",
                    msg="String argument not allowed as an optional or multiple argument. Probably missing a namespace.",
                    visual_pairs=[(arg.span.start, arg.span.end)],
                    index=arg.span.start,
                )
            )

    # Check for obsolete namespaces
    for arg in fn.args:
        if (
            arg.type == "NSArg"
            and arg.entity.term
            and arg.entity.original_nsval.key in arg.entity.term.obsolete_keys
        ):
            errors.append(
                ValidationError(
                    type="Assertion",
                    severity="Warning",
                    msg=f"BEL Entity name is obsolete - please update to {arg.entity.term.key}!{arg.entity.term.label}",
                    visual_pairs=[(arg.span.start, arg.span.end)],
                    index=fn.args[position].span.start,
                )
            )

    # Check for bad reactions
    # 1. reactants = products -> error
    # 2. reactants = products(complex(reactants)) = warning to replace with just the complex

    if fn.name == "reaction":
        errors.extend(validate_rxn_semantics(fn))

    # Modifier function with wrong parent function
    if (
        fn.function_signature["func_type"] == "Modifier"
        and fn.parent
        and fn.parent.name not in fn.function_signature["primary_function"]
    ):
        errors.append(
            ValidationError(
                type="Assertion",
                severity="Error",
                msg=f"Missing parent for modifier function or wrong parent function for {fn.name}",
                visual_pairs=[(fn.span.start, fn.span.end)],
                index=fn.span.start,
            )
        )

    return errors


def validate_rxn_semantics(rxn: "Function") -> List[ValidationError]:
    """Validate Reactions

    Check for bad reactions
    1. reactants = products -> error
    2. reactants = products(complex(reactants)) = warning to replace with just the complex

    """

    errors = []

    reactants = rxn.args[0]
    products = rxn.args[1]

    if reactants.name != "reactants" or products.name != "products":
        return errors

    # ERROR reactants(A, B) -> products(complex(A, B))  SHOULD BE complex(A, B)
    if products.args[0].name == "complexAbundance" and compare_fn_args(
        reactants.args, products.args[0].args
    ):
        errors.append(
            ValidationError(
                type="Assertion",
                severity="Error",
                msg=f"Reaction should be replaced with just the product complex: {products.args[0].to_string()}",
                visual_pairs=[(rxn.span.start, rxn.span.end)],
                index=rxn.span.start,
            )
        )

    # ERROR reactants(A, B) SHOULD NOT EQUAL products(A, B)
    elif compare_fn_args(reactants.args, products.args):
        errors.append(
            ValidationError(
                type="Assertion",
                severity="Error",
                msg=f"Reaction should not have equivalent reactants and products",
                visual_pairs=[(rxn.span.start, rxn.span.end)],
                index=rxn.span.start,
            )
        )

    return errors
