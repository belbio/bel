"""Enhance the BEL Specification YAML file for easier use by BEL package"""
# Standard Library
import copy
import re
from typing import Any, List, Mapping

# Third Party
# Local Imports
import bel.core.settings as settings

# Third Party Imports
from loguru import logger


def create_enhanced_specification(specification) -> dict:
    """Enhance BEL specification"""

    enhanced_spec = copy.deepcopy(specification)

    # add relation keys list, to_short, to_long
    add_relations(enhanced_spec)

    # add function keys list, to_short, to_long
    add_functions(enhanced_spec)

    # add namespace keys list, list_short, list_long, to_short, to_long
    add_namespaces(enhanced_spec)

    enhance_function_signatures(enhanced_spec)

    add_function_signature_help(enhanced_spec)

    return enhanced_spec


def add_function_signature_help(specification: dict) -> dict:
    """Add function signature help

    Simplify the function signatures for presentation to BEL Editor users
    """
    for f in specification["functions"]["signatures"]:
        for argset_idx, argset in enumerate(
            specification["functions"]["signatures"][f]["signatures"]
        ):
            args_summary = ""
            args_list = []
            for arg in specification["functions"]["signatures"][f]["signatures"][argset_idx][
                "arguments"
            ]:
                if arg["type"] in ["Function", "Modifier"]:
                    vals = [
                        specification["functions"]["to_short"].get(
                            val, specification["functions"]["to_short"].get(val)
                        )
                        for val in arg["values"]
                    ]
                    args_summary += "|".join(vals) + "()"

                    if arg.get("optional", False) and arg.get("multiple", False) is False:
                        args_summary += "?"
                        text = f'Zero or one of each function(s): {", ".join([val for val in arg["values"]])}'
                    elif arg.get("optional", False):
                        args_summary += "*"
                        text = f'Zero or more of each function(s): {", ".join([val for val in arg["values"]])}'
                    else:
                        text = f'One of following function(s): {", ".join([val for val in arg["values"]])}'

                elif arg["type"] in ["NSArg", "StrArg", "StrArgNSArg"]:
                    args_summary += f'{arg["type"]}'
                    if arg.get("optional", False) and arg.get("multiple", False) is False:
                        args_summary += "?"
                        if arg["type"] in ["NSArg"]:
                            text = f'Zero or one namespace argument of following type(s): {", ".join([val for val in arg["values"]])}'
                        elif arg["type"] == "StrArgNSArg":
                            text = f'Zero or one namespace argument or default namespace argument (without prefix) of following type(s): {", ".join([val for val in arg["values"]])}'
                        else:
                            text = f'Zero or one string argument of following type(s): {", ".join([val for val in arg["values"]])}'
                    elif arg.get("optional", False):
                        args_summary += "*"
                        if arg["type"] in ["NSArg"]:
                            text = f'Zero or more namespace arguments of following type(s): {", ".join([val for val in arg["values"]])}'
                        elif arg["type"] == "StrArgNSArg":
                            text = f'Zero or more namespace arguments or default namespace arguments (without prefix) of following type(s): {", ".join([val for val in arg["values"]])}'
                        else:
                            text = f'Zero or more of string arguments of following type(s): {", ".join([val for val in arg["values"]])}'
                    else:
                        if arg["type"] in ["NSArg"]:
                            text = f'Namespace argument of following type(s): {", ".join([val for val in arg["values"]])}'
                        elif arg["type"] == "StrArgNSArg":
                            text = f'Namespace argument or default namespace argument (without prefix) of following type(s): {", ".join([val for val in arg["values"]])}'
                        else:
                            text = f'String argument of following type(s): {", ".join([val for val in arg["values"]])}'

                args_summary += ", "
                args_list.append(text)

            args_summary = re.sub(", $", "", args_summary)
            specification["functions"]["signatures"][f]["signatures"][argset_idx][
                "argument_summary"
            ] = f"{f}({args_summary})"
            specification["functions"]["signatures"][f]["signatures"][argset_idx][
                "argument_help_listing"
            ] = args_list

    return specification


def add_relations(specification: Mapping[str, Any]) -> Mapping[str, Any]:
    """Add relation keys to specification

    Args:
        specification (Mapping[str, Any]): bel specification dictionary

    Returns:
        Mapping[str, Any]: bel specification dictionary with added relation keys
    """

    # Class 'Mapping' does not define '__setitem__', so the '[]' operator cannot be used on its instances
    specification["relations"]["list"] = []
    specification["relations"]["list_short"] = []
    specification["relations"]["list_long"] = []
    specification["relations"]["to_short"] = {}
    specification["relations"]["to_long"] = {}

    for relation_name in specification["relations"]["info"]:

        abbreviated_name = specification["relations"]["info"][relation_name]["abbreviation"]
        specification["relations"]["list"].extend((relation_name, abbreviated_name))
        specification["relations"]["list_long"].append(relation_name)
        specification["relations"]["list_short"].append(abbreviated_name)

        specification["relations"]["to_short"][relation_name] = abbreviated_name
        specification["relations"]["to_short"][abbreviated_name] = abbreviated_name

        specification["relations"]["to_long"][abbreviated_name] = relation_name
        specification["relations"]["to_long"][relation_name] = relation_name

    specification["relations"]["list"] = list(set(specification["relations"]["list"]))

    return specification


def add_functions(specification: Mapping[str, Any]) -> Mapping[str, Any]:
    """Add function keys to specification

    Args:
        specification (Mapping[str, Any]): bel specification dictionary

    Returns:
        Mapping[str, Any]: bel specification dictionary with added function keys
    """

    # Class 'Mapping' does not define '__setitem__', so the '[]' operator cannot be used on its instances
    specification["functions"]["list"] = []
    specification["functions"]["list_long"] = []
    specification["functions"]["list_short"] = []

    specification["functions"]["primary"] = []
    specification["functions"]["primary_list_long"] = []
    specification["functions"]["primary_list_short"] = []

    specification["functions"]["modifier"] = []
    specification["functions"]["modifier_list_long"] = []
    specification["functions"]["modifier_list_short"] = []

    specification["functions"]["to_short"] = {}
    specification["functions"]["to_long"] = {}

    for func_name in specification["functions"]["info"]:

        abbreviated_name = specification["functions"]["info"][func_name]["abbreviation"]

        specification["functions"]["list"].extend((func_name, abbreviated_name))

        specification["functions"]["list_long"].append(func_name)
        specification["functions"]["list_short"].append(abbreviated_name)

        if specification["functions"]["info"][func_name]["type"] == "primary":
            specification["functions"]["primary"].append(func_name)
            specification["functions"]["primary"].append(abbreviated_name)
            specification["functions"]["primary_list_long"].append(func_name)
            specification["functions"]["primary_list_short"].append(abbreviated_name)
        else:
            specification["functions"]["modifier"].append(func_name)
            specification["functions"]["modifier"].append(abbreviated_name)
            specification["functions"]["modifier_list_long"].append(func_name)
            specification["functions"]["modifier_list_short"].append(abbreviated_name)

        specification["functions"]["to_short"][abbreviated_name] = abbreviated_name
        specification["functions"]["to_short"][func_name] = abbreviated_name

        specification["functions"]["to_long"][abbreviated_name] = func_name
        specification["functions"]["to_long"][func_name] = func_name

    specification["functions"]["list"] = list(set(specification["functions"]["list"]))

    return specification


def add_namespaces(specification):
    """Add namespace convenience keys, list, list_{short|long}, to_{short|long}"""

    for ns in specification["namespaces"]:
        specification["namespaces"][ns]["list"] = []
        specification["namespaces"][ns]["list_long"] = []
        specification["namespaces"][ns]["list_short"] = []

        specification["namespaces"][ns]["to_short"] = {}
        specification["namespaces"][ns]["to_long"] = {}

        for obj in specification["namespaces"][ns]["info"]:
            specification["namespaces"][ns]["list"].extend([obj["name"], obj["abbreviation"]])
            specification["namespaces"][ns]["list_short"].append(obj["abbreviation"])
            specification["namespaces"][ns]["list_long"].append(obj["name"])

            specification["namespaces"][ns]["to_short"][obj["abbreviation"]] = obj["abbreviation"]
            specification["namespaces"][ns]["to_short"][obj["name"]] = obj["abbreviation"]

            specification["namespaces"][ns]["to_long"][obj["abbreviation"]] = obj["name"]
            specification["namespaces"][ns]["to_long"][obj["name"]] = obj["name"]

            # For AminoAcid namespace
            if "abbrev1" in obj:
                specification["namespaces"][ns]["to_short"][obj["abbrev1"]] = obj["abbreviation"]
                specification["namespaces"][ns]["to_long"][obj["abbrev1"]] = obj["name"]


def enhance_function_signatures(specification: Mapping[str, Any]) -> Mapping[str, Any]:
    """Enhance function signatures

    Add required and optional objects to signatures objects for semantic validation
    support.

    Args:
        specification (Mapping[str, Any]): bel specification dictionary

    Returns:
        Mapping[str, Any]: return enhanced bel specification dict
    """

    for func in specification["functions"]["signatures"]:

        # Add primary parent functions to modifier functions
        if specification["functions"]["signatures"][func]["func_type"] == "modifier":
            specification["functions"]["signatures"][func]["primary_function"] = specification[
                "functions"
            ]["info"][func]["primary_function"]

        for i, sig in enumerate(specification["functions"]["signatures"][func]["signatures"]):
            args = sig["arguments"]
            req_args = []
            pos_args = []
            opt_args = []
            mult_args = []

            for arg in args:
                # Multiple argument types
                if arg.get("multiple", False):
                    if arg["type"] in ["Function", "Modifier"]:
                        mult_args.extend(arg.get("values", []))
                    elif arg["type"] in ["NSArg"]:
                        # Complex and Composite signature has this
                        mult_args.extend(arg.get("values", []))
                    elif arg["type"] in ["StrArgNSArg", "StrArg"]:

                        mult_args.append(arg["type"])

                # Optional, position dependent - will be added after req_args based on order in bel_specification
                elif arg.get("optional", False) and arg.get("position", False):
                    if arg["type"] in ["Function", "Modifier"]:
                        pos_args.append(arg.get("values", []))
                    elif arg["type"] in ["StrArgNSArg", "NSArg", "StrArg"]:
                        pos_args.append(arg["type"])

                # Optional, position independent
                elif arg.get("optional", False):
                    if arg["type"] in ["Function", "Modifier"]:
                        opt_args.extend(arg.get("values", []))
                    elif arg["type"] in ["StrArgNSArg", "NSArg", "StrArg"]:
                        opt_args.append(arg["type"])

                # Required arguments, position dependent
                else:
                    if arg["type"] in ["Function", "Modifier"]:
                        req_args.append(arg.get("values", []))
                    elif arg["type"] in ["StrArgNSArg", "NSArg", "StrArg"]:
                        req_args.append(arg["type"])

            specification["functions"]["signatures"][func]["signatures"][i][
                "req_args"
            ] = copy.deepcopy(req_args)
            specification["functions"]["signatures"][func]["signatures"][i][
                "pos_args"
            ] = copy.deepcopy(pos_args)
            specification["functions"]["signatures"][func]["signatures"][i][
                "opt_args"
            ] = copy.deepcopy(opt_args)
            specification["functions"]["signatures"][func]["signatures"][i][
                "mult_args"
            ] = copy.deepcopy(mult_args)

    return specification


def create_ebnf_parser(specification):
    """Create EBNF file from BEL Specification"""

    # Standard Library
    import datetime
    import itertools

    # Third Party
    import jinja2

    ebnf_template_dir = f"{settings.appdir}/belspec"
    ebnf_template_fn = "bel.ebnf.j2"

    bel_major_version = specification["version"].split(".")[0]

    try:
        env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(ebnf_template_dir)
        )  # create environment for template
        template = env.get_template(ebnf_template_fn)  # get the template
    except Exception as e:
        return f"Could not access EBNF template - error: {str(e)}"

    # replace template placeholders with appropriate variables
    relations_list = [
        (relation, specification["relations"]["info"][relation]["abbreviation"])
        for relation in specification["relations"]["info"]
    ]
    relations_list = sorted(list(itertools.chain(*relations_list)), key=len, reverse=True)

    functions_list = [
        (function, specification["functions"]["info"][function]["abbreviation"])
        for function in specification["functions"]["info"]
        if specification["functions"]["info"][function]["type"] == "primary"
    ]
    functions_list = sorted(list(itertools.chain(*functions_list)), key=len, reverse=True)

    modifiers_list = [
        (function, specification["functions"]["info"][function]["abbreviation"])
        for function in specification["functions"]["info"]
        if specification["functions"]["info"][function]["type"] == "modifier"
    ]
    modifiers_list = sorted(list(itertools.chain(*modifiers_list)), key=len, reverse=True)

    created_time = datetime.datetime.now().strftime("%B %d, %Y - %I:%M:%S%p")

    ebnf = template.render(
        functions=functions_list,
        m_functions=modifiers_list,
        relations=relations_list,
        bel_version=specification["version"],
        bel_major_version=bel_major_version,
        created_time=created_time,
    )

    return ebnf
