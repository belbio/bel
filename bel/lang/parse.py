#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Standard Library
import copy
import itertools
import json
import re
from typing import Any, List, Mapping, Optional, Tuple, Union

# Third Party
import boltons.iterutils
import cachetools
from loguru import logger
from pydantic import BaseModel, Field

# Local
import bel.belspec.specifications
from bel.belspec.specifications import additional_computed_relations
from bel.core.utils import html_wrap_span, nsarg_pattern
from bel.lang.ast import Arg, BELAst, Function, NSArg, Relation, StrArg
from bel.schemas.bel import FunctionSpan, NsArgSpan, Pair, Span, ValidationError


def mask(string: str, start: int, end: int, replacement_char="#"):
    """Mask part of a string with replacement char"""

    return string[:start] + replacement_char * (end - start) + string[end:]


def parse_info(assertion_str: str, version: str = "latest"):
    """Create parse info for AST to use in parsing Assertion String"""

    errors = []
    (matched_quotes, errors) = find_matching_quotes(assertion_str, errors)
    (matched_parens, errors) = find_matching_parens(assertion_str, matched_quotes, errors)
    (commas, errors) = find_commas(assertion_str, matched_quotes, errors)
    (relations, errors) = find_relations(assertion_str, matched_quotes, errors, version)
    (functions, errors) = find_functions(
        assertion_str, matched_quotes, matched_parens, errors, version
    )
    nsargs = find_nsargs(assertion_str)

    components = relations + functions + nsargs

    # Find str arguments and floating strings after masking all other components
    strings = find_strings(assertion_str, components)
    components += strings

    # Add parens for function boundaries (AFTER processing string arguments)
    for parens in matched_parens:
        if parens.start:
            components.append(
                Span(start=parens.start, end=parens.start + 1, span_str="(", type="start_paren")
            )
        if parens.end:
            components.append(
                Span(start=parens.end, end=parens.end + 1, span_str=")", type="end_paren")
            )

    components.sort(key=lambda x: x.start)

    return {
        "matched_quotes": matched_quotes,
        "matched_parens": matched_parens,
        "commas": commas,
        "components": components,
        "errors": errors,
    }


def intersect(pos: int, spans: List[Optional[Span]]) -> bool:
    """Check to see if pos intersects the provided spans - e.g. quotes"""

    if spans:
        for span in spans:

            if span.start and span.end and span.start < pos < span.end:
                return True

    return False


def ordered_pairs(left: List[int], right: List[int]) -> List[Union[int, None]]:
    """Return ordered pairs such that every left, right pair has left < right"""

    alt = {"left": "right", "right": "left"}

    pairs = [("left", item) for item in left] + [("right", item) for item in right]
    pairs.sort(key=lambda x: x[1])

    # Must have left, right alternation - insert placeholders for left, left or right, right entries
    new_pairs = []
    for idx, pair in enumerate(pairs):
        next_idx = idx + 1
        # Trying to match two lefts together: pair[0] == pairs[idx + 1][0]?
        if (next_idx < len(pairs) and pair[0] == pairs[idx + 1][0]) or (
            next_idx >= len(pairs) and pair[0] == "left"
        ):
            new_pairs.append(pair)
            new_pairs.append((alt[pair[0]], None))

        elif idx == 0 and pair[0] == "right":
            new_pairs.append((alt[pair[0]], None))
            new_pairs.append(pair)

        else:
            new_pairs.append(pair)

    matched_quotes = [
        Pair(start=new_pairs[i][1], end=new_pairs[i + 1][1]) for i in range(0, len(new_pairs), 2)
    ]

    return matched_quotes


def find_matching_quotes(
    assertion_str: str, errors: List[ValidationError]
) -> Tuple[List[Pair], List[ValidationError]]:
    """Find matching quotes using BEL Assertion syntax"""

    quote_matches_left = re.compile(r"[\,\:\!\(]+\s*(\")")
    quote_matches_right = re.compile(r"(\")\s*[\!\)\,]")

    iter_left = re.finditer(quote_matches_left, assertion_str)
    iter_right = re.finditer(quote_matches_right, assertion_str)
    left_quotes = [m.span(1)[0] for m in iter_left]
    right_quotes = [m.span(1)[0] for m in iter_right]

    matched_quotes = ordered_pairs(left_quotes, right_quotes)

    # TODO suggest where the missing quote should be placed
    for idx, pair in enumerate(matched_quotes):
        if pair.start is None and idx == 0:
            errors.append(
                ValidationError(
                    type="Assertion",
                    severity="Error",
                    msg=f"Missing left quote before right quote at position {pair.end}",
                    visual=html_wrap_span(assertion_str, [(pair.end, pair.end + 1)]),
                    index=pair.end,
                )
            )
        elif pair.start is None:
            errors.append(
                ValidationError(
                    type="Assertion",
                    severity="Error",
                    msg=f"Missing left quote between right quotes at positions {matched_quotes[idx-1].end} and {pair.end}",
                    visual=html_wrap_span(
                        assertion_str, [(matched_quotes[idx - 1].end, pair.end + 1)]
                    ),
                    index=matched_quotes[idx - 1].end,
                )
            )
        elif pair.end is None and idx == len(matched_quotes):
            errors.append(
                ValidationError(
                    type="Assertion",
                    severity="Error",
                    msg=f"Missing right quote after left quote at position {pair.start}",
                    visual=html_wrap_span(assertion_str, [(pair.start, pair.start + 1)]),
                    index=pair.start,
                )
            )
        elif pair.end is None:

            next_pair_idx = idx + 1
            if next_pair_idx < len(matched_quotes):
                span_end = matched_quotes[next_pair_idx].start
            else:
                span_end = len(assertion_str)

            errors.append(
                ValidationError(
                    type="Assertion",
                    severity="Error",
                    msg=f"Missing right quote after left quote at position {pair.start} and before position {span_end}",
                    visual=html_wrap_span(assertion_str, [(pair.start, span_end)]),
                    index=pair.start,
                )
            )

    return (matched_quotes, errors)


def find_commas(
    assertion_str: str, matched_quotes: List[Span], errors: List[ValidationError]
) -> Tuple[List[int], List[ValidationError]]:
    """Find commas in chars list that are not in quoted strings"""

    if errors is None:
        errors = []

    commas: List[int] = []

    for idx, char in enumerate(assertion_str):
        if intersect(idx, matched_quotes):
            continue
        elif char == ",":
            commas.append(idx)

    return (sorted(commas), errors)


def find_matching_parens(
    assertion_str, matched_quotes, errors: List[ValidationError]
) -> Tuple[List[Pair], List[ValidationError]]:
    """Find and return the location of the matching parentheses pairs in s.

    Given a string, s, return a dictionary of start: end pairs giving the
    indexes of the matching parentheses in s. Suitable exceptions are
    raised if s contains unbalanced parentheses.

    """

    # The indexes of the start parentheses are stored in a stack, implemented as a list
    stack: List[int] = []
    matched_parens: List[Pair] = []

    for idx, char in enumerate(assertion_str):
        if char == "(" and not intersect(idx, matched_quotes):
            stack.append(idx)
        elif char == ")" and not intersect(idx, matched_quotes):
            if len(stack) > 0:
                matched_parens.append(Pair(start=stack.pop(), end=idx))
            else:
                errors.append(
                    ValidationError(
                        type="Assertion",
                        severity="Error",
                        msg=f"Too many close parentheses at index {idx}",
                        visual=html_wrap_span(assertion_str, [(idx, idx + 1)]),
                        index=idx,
                    )
                )
    if stack:
        for idx in stack:
            errors.append(
                ValidationError(
                    type="Assertion",
                    severity="Error",
                    msg=f"No matching close parenthesis for open parenthesis at index {idx}",
                    visual=html_wrap_span(assertion_str, [(idx, idx + 1)]),
                    index=idx,
                )
            )

    return (sorted(matched_parens, key=lambda e: e.start), errors)


@cachetools.cached(cachetools.TTLCache(maxsize=1, ttl=600))
def get_relations_regex(version: str = "latest"):

    relations_list = bel.belspec.specifications.get_all_relations(version)
    relations_list += additional_computed_relations
    relations_list = list(set(relations_list))
    relations_list.sort(key=len)
    relations_regex = "|".join(relations_list)

    return relations_regex


def find_relations(
    assertion_str: str, matched_quotes: List[Pair], errors: List[ValidationError], version: str
) -> Tuple[List[Span], List[ValidationError]]:
    """Find relation(s) e.g. handle nested objects as well

    Returns:
        List[Tuple[int, int, str]] = e.g. [(2, 4, '->')]
    """

    relations_regex = get_relations_regex(version=version)

    # Regex match all potential relations TODO make \S more specific to relation chars
    potential_relations = re.compile(f"\\s({relations_regex})\\s")
    iterator = re.finditer(potential_relations, assertion_str)
    pre_spans = [m.span(1) for m in iterator]

    # Filter quoted strings - can't have a relation in a quoted string
    relations = [
        Span(start=r[0], end=r[1], span_str=assertion_str[r[0] : r[1]], type="relation")
        for r in pre_spans
        if not intersect(r[0], matched_quotes)
    ]

    if len(relations) > 2:
        intervals = [(r.start, r.end) for r in relations]
        idx = relations[0].start
        error_str = ", ".join([f"{r.span_str}[{r.start}:{r.end}]" for r in relations])

        errors.append(
            ValidationError(
                type="Assertion",
                severity="Error",
                msg=f"Too many relationships: {error_str}",
                visual=html_wrap_span(assertion_str, intervals),
                index=idx,
            )
        )

    return (sorted(relations, key=lambda e: e.start), errors)


def find_functions(
    assertion_str: str,
    matched_quotes: List[Pair],
    matched_parens: List[Pair],
    errors: List[ValidationError],
    version: str,
) -> Tuple[List[FunctionSpan], List[ValidationError]]:
    """Find function(s)

    Returns:
        List[Tuple[int, int, str]] = e.g. [(2, 4, '->')]
    """

    functions_list = bel.belspec.specifications.get_all_functions(version)

    iterator = re.finditer("([a-zA-Z]+)\(", assertion_str)

    name_spans = []
    for m in iterator:
        matched = m.group(1)
        if matched not in functions_list:
            continue

        name_spans.append(m.span(1))

    # Filter quoted strings - can't have a relation in a quoted string
    name_spans = [r for r in name_spans if not intersect(r[0], matched_quotes)]

    functions = []
    for span in name_spans:

        name_start = span[0]
        name_end = span[1]
        name_str = assertion_str[name_start:name_end]

        # Initialize FunctionSpan with just name span
        function = FunctionSpan(
            start=name_start,
            end=name_end,
            span_str=name_str,
            type="function",
            name=Span(start=name_start, end=name_end, span_str=name_str, type="function_name"),
            args=None,
        )

        # then add the function full span and arguments span
        for parens in matched_parens:
            if name_end == parens.start:
                args_end = parens.end + 1
                function.end = args_end
                function.span_str = assertion_str[name_start:args_end]
                function.args = Span(
                    start=parens.start,
                    end=args_end,
                    span_str=assertion_str[parens.start : args_end],
                    type="function_args",
                )

        # TODO - check for relation after name_end and before end of Assertion string to bound the function
        # This covers function with missing end parenthesis
        if function.args is None:
            args_end = len(assertion_str)
            function.end = args_end
            function.span_str = assertion_str[name_start:args_end]
            function.args = Span(
                start=name_end,
                end=args_end,
                span_str=assertion_str[name_end:args_end],
                type="function_args",
            )

        functions.append(copy.deepcopy(function))

    return (sorted(functions, key=lambda e: e.start), errors)


def find_nsargs(assertion_str: str) -> List[Optional[NsArgSpan]]:
    """Namespace argument parsing

    Namespace IDs and Labels are NOT allowed to have internal double quotes.

    IDs or Labels with commas or end parenthesis in them must be quoted.

    The parser supports NS:ID!LABEL or NS : ID ! LABEL (e.g. with arbitrary whitespace between the separators)
    """

    nsarg_spans: List[NsArgSpan] = []

    for match in re.finditer(nsarg_pattern, assertion_str):

        # print("Span", match.group("ns_arg"), match.start("ns_arg"), match.end("ns_arg"))

        ns_arg_span = NsArgSpan(
            span_str=match.group("ns_arg"),
            start=match.start("ns_arg"),
            end=match.end("ns_arg"),
            type="ns_arg",
            namespace=Span(
                span_str=match.group("ns"),
                start=match.start("ns"),
                end=match.end("ns"),
                type="namespace",
            ),
            id=Span(
                span_str=match.group("id"),
                start=match.start("id"),
                end=match.end("id"),
                type="ns_id",
            ),
        )

        if match.group("label"):
            ns_arg_span.label = Span(
                span_str=match.group("label"),
                start=match.start("label"),
                end=match.end("label"),
                type="ns_label",
            )

        nsarg_spans.append(copy.deepcopy(ns_arg_span))

    return nsarg_spans


def find_strings(assertion_str, components):
    """Find str_args and unknown strings"""

    str_spans: List[Span] = []

    potential_replacement_chars = ["#", "$", "=", "@", "&"]

    for char in potential_replacement_chars:
        if char not in assertion_str:
            replacement_char = char
            break

    for comp in components:
        start = comp.start
        end = comp.end
        if comp.type == "function":  # just mask function name for functions
            start = comp.name.start
            end = comp.name.end
        assertion_str = mask(assertion_str, start, end, replacement_char)

    boundary_chars = [replacement_char, ",", ")", "("]
    space_boundary_chars = [" ", replacement_char, ",", ")", "("]
    start = None
    for idx, c in enumerate(assertion_str):
        if start is None and c not in space_boundary_chars:
            start, end = idx, idx

        elif start and c in boundary_chars:
            type_ = "string_arg"
            if c == replacement_char:
                type_ = "string"
            str_spans.append(
                Span(start=start, end=end + 1, span_str=assertion_str[start : end + 1], type=type_)
            )
            start = None

        elif start is not None and c not in space_boundary_chars:
            end = idx

    if start is not None:
        str_spans.append(
            Span(start=start, end=end + 1, span_str=assertion_str[start : end + 1], type="string")
        )

    return str_spans


def main():

    test = {}
    span = Span(start=1, end=2, span_str="H")
    test[f"{span.start}-{span.end}"] = span
    print(test)


if __name__ == "__main__":
    main()
