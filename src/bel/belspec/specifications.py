# Standard Library
import copy
from typing import Any, List, Mapping

# Third Party
# Local Imports
import bel.belspec.crud
import cachetools

# Third Party Imports
import yaml
from bel.core.utils import http_client

additional_computed_relations = [
    "hasComponent",
    "hasMember",
    "hasAssociation",
    "hasActivity",
    "hasModification",
    "hasVariant",
    "hasFragment",
    "hasLocation",
    "hasFusion",
    "hasProduct",
    "hasReactant",
]


@cachetools.cached(cachetools.TTLCache(maxsize=1, ttl=600))
def get_all_relations(version: str):
    """Get all relations - long and short"""

    belspec = bel.belspec.crud.get_enhanced_belspec(version)

    return belspec["relations"]["list"]


@cachetools.cached(cachetools.TTLCache(maxsize=1, ttl=600))
def get_all_functions(version: str):
    """Get all functions - long and short"""

    belspec = bel.belspec.crud.get_enhanced_belspec(version)
    return belspec["functions"]["list"]


@cachetools.cached(cachetools.TTLCache(maxsize=1, ttl=600))
def get_function_help(function: str, version: str):
    """Get function_help given function name

    This will get the function summary template (argument summary in signature)
    and the argument help listing.
    """

    enhanced_belspec = bel.belspec.crud.get_enhanced_belspec(version)

    function_long = enhanced_belspec["functions"]["to_long"].get(function)
    function_help = []

    if function_long:
        for signature in enhanced_belspec["functions"]["signatures"][function_long]["signatures"]:
            function_help.append(
                {
                    "function_summary": signature["argument_summary"],
                    "argument_help": signature["argument_help_listing"],
                    "description": enhanced_belspec["functions"]["info"][function_long][
                        "description"
                    ],
                }
            )

    return function_help


def _dump_belspec(belspec):
    """Dump bel specification dictionary using YAML

    Formats this with an extra indentation for lists to make it easier tbo
    use cold folding on the YAML version of the spec dictionary.
    """

    # Third Party
    import yaml

    with open("spec.yaml", "w") as f:
        yaml.dump(belspec, f, Dumper=MyDumper, default_flow_style=False)


class MyDumper(yaml.Dumper):
    def increase_indent(self, flow=False, indentless=False):
        return super(MyDumper, self).increase_indent(flow, False)
