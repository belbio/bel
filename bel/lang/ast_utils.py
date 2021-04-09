# Standard Library
from typing import TYPE_CHECKING

# Third Party
from loguru import logger

if TYPE_CHECKING:
    # Local
    from bel.lang.ast import Function


def args_to_string(args, fmt: str = "medium", ignore_location: bool = False) -> str:
    """Convert function arguments to string"""

    args_strings = []
    for a in args:
        arg_str = a.to_string(fmt=fmt, ignore_location=ignore_location)
        if arg_str:
            args_strings.append(arg_str)

    args_string = ", ".join(args_strings)

    return args_string


def compare_fn_args(args1, args2, ignore_locations: bool = False) -> bool:
    """If args set1 is the same as arg set2 - returns True

    This is used to see if two functions have the same set of arguments
    """

    args1 = args_to_string(args1, ignore_location=True)
    args2 = args_to_string(args2, ignore_location=True)

    return args1 == args2


def intersect(list1, list2) -> bool:
    """Do list1 and list2 intersect"""

    if len(set(list1).intersection(set(list2))) == 0:
        return False

    return True


def match_signatures(args, signatures: dict) -> dict:
    """Which signature to use"""

    for signature in signatures:
        if (
            hasattr(args[0], "function_type")
            and args[0].function_type == signature["arguments"][0]["type"]
        ) or (args[0].type == signature["arguments"][0]["type"]):
            return signature

    return {}


def sort_function_args(fn: "Function"):
    """Add sort tuple values to function arguments for canonicalization and sort function arguments"""

    signatures = fn.function_signature["signatures"]

    # Select signature from signatures
    if len(signatures) > 1:
        signature = match_signatures(fn.args, signatures)
    else:
        signature = signatures[0]

    fn_max_args = len(fn.args) - 1

    post_positional = 0
    for arg in signature["arguments"]:
        if arg["position"]:
            position = arg["position"]
            if position > fn_max_args:
                return None

            if arg["optional"] == False:
                fn.args[position].sort_tuple = (position,)
                post_positional = position + 1

            elif arg["optional"] == True:

                if arg["type"] == ["StrArgNSArg"]:
                    arg["type"].extend(["NSArg", "StrArg"])

                if (  # Function match
                    fn.args[position].type == "Function" and fn.args[position].name in arg["values"]
                ) or (  # NSArg/StrArg type match
                    fn.args[position].type in ["NSArg", "StrArg"]
                    and fn.args[position].type in arg["type"]
                ):
                    fn.args[position].sort_tuple = (position,)
                    post_positional = position + 1

    # non-positional elements
    primary_func_index = (
        post_positional + 1
    )  # Sort primary functions after non-function post-positional
    modifier_func_index = post_positional + 2  # Sort modifier functions after
    for fn_arg in fn.args[post_positional:]:
        if fn_arg.type == "StrArg":
            fn_arg.sort_tuple = (post_positional, "StrArg", fn_arg.value)

        elif fn_arg.type == "NSArg":
            fn_arg.sort_tuple = (post_positional, "NSArg", str(fn_arg.entity))

        # Sort by modifier function name, then position of modification and
        #     then by type of modification if available
        elif fn_arg.name == "proteinModification":
            pmod_args_len = len(fn_arg.args)

            if fn.args[0].type == "NSArg":
                modification_type_value = str(fn.args[0].entity)
            else:
                modification_type_value = fn_arg.args[0].value

            if pmod_args_len == 3:
                fn_arg.sort_tuple = (
                    modifier_func_index,
                    fn_arg.name,
                    fn_arg.args[2].value,
                    modification_type_value,
                )
            else:  # Add position of modification = -1
                fn_arg.sort_tuple = (
                    modifier_func_index,
                    fn_arg.name,
                    "-1",
                    modification_type_value,
                )

        elif fn_arg.name == "fragment":
            fn_arg.sort_tuple = (modifier_func_index, fn_arg.name, fn_arg.args[0])

        elif fn_arg.name == "variant":
            # TODO use https://github.com/biocommons/hgvs to sort by variant position
            fn_arg.sort_tuple = (modifier_func_index, fn_arg.name, str(fn_arg))

        elif fn_arg.function_type == "Modifier":
            fn_arg.sort_tuple = (modifier_func_index, fn_arg.name, str(fn_arg))

        elif fn_arg.type == "Function":
            fn_arg.sort_tuple = (primary_func_index, fn_arg.name, str(fn_arg))

        else:
            logger.error(f"Adding sort tuples - no sort_tuple added for {fn_arg}")

    fn.args = sorted(fn.args, key=lambda x: x.sort_tuple)
