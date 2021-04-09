# Standard Library
import copy
from typing import TYPE_CHECKING, Optional, Tuple

# Third Party
from loguru import logger

# Local
from bel.lang.ast_utils import compare_fn_args
from bel.schemas.bel import BelEntity

if TYPE_CHECKING:
    # Local
    from bel.lang.ast import Function

# TODO - tloc() -> sec() or surf()


def get_loc(entity) -> Tuple[Optional[BelEntity], Optional[BelEntity]]:
    """Get location entity nsarg and loc entities"""

    nsarg = entity.args[0]
    for arg in entity.args:
        if hasattr(arg, "name") and arg.name == "location":
            return nsarg, arg.args[0]

    return None, None


def optimize_rxn(fn: "Function") -> "Function":
    """Transform reaction into more optimal BEL

    1. reactants(A, B) -> products(complex(A, B))  SHOULD BE complex(A, B)
    1. reactants(A, loc(X)) -> products(A, loc(Y)) CONVERTED TO tloc(A, fromLoc(X), toLoc(Y))

    """

    # Local
    from bel.lang.ast import Function

    if not hasattr(fn, "name") or fn.name != "reaction":
        return fn

    if len(fn.args) != 2:
        logger.error(f"RXN args count error: {fn.args}")
        return fn

    parent = fn.parent
    reactants = fn.args[0]
    products = fn.args[1]
    if reactants.name != "reactants" or products.name != "products":
        return fn

    # Convert reactants(A, B) -> products(complex(A, B))  SHOULD BE complex(A, B)
    if hasattr(products.args[0], "args"):
        same = compare_fn_args(reactants.args, products.args[0].args, ignore_locations=True)
        if products.args[0].name == "complexAbundance" and same:
            fn = products.args[0]
            fn.parent = parent

    # Convert rxn(reactants(A, loc(1)), products(A, loc(2))) TO tloc(A, fromLoc(1), toLoc(2))
    if len(reactants.args) == 1 and len(products.args) == 1:
        reactant = reactants.args[0]
        product = products.args[0]

        (reactant_nsarg, reactant_loc) = get_loc(reactant)
        (product_nsarg, product_loc) = get_loc(product)

        if str(reactant_nsarg) == str(product_nsarg) and str(reactant_loc) != str(product_loc):
            tloc_target_fn_name = reactant.name

            tloc = Function("translocation")
            tloc_target = Function(tloc_target_fn_name)
            tloc_target.args.append(reactant_nsarg)

            tloc_from = Function("fromLoc")
            tloc_from.args.append(reactant_loc)
            tloc_to = Function("toLoc")
            tloc_to.args.append(product_loc)

            tloc.args = [tloc_target, tloc_from, tloc_to]

            fn = tloc

    return fn


def optimize_tloc(fn: "Function") -> "Function":
    """Convert tloc to sec() or surf() if matches

    1. tloc(A, fromLoc(X), toLoc(extracellular region)) CONVERTED TO sec(A)
    1. tloc(A, fromLoc(X), toLoc(plasma membrane)) CONVERTED TO surf(A)
    """

    # Local
    from bel.lang.ast import Function

    secretion_matches = ["extracellular"]
    surface_matches = ["plasma membrane"]

    if not hasattr(fn, "name") or fn.name != "translocation":
        return fn

    for arg in fn.args:
        if hasattr(arg, "name") and arg.name == "toLoc":
            to_arg_str = str(arg.args[0])
            if "extracellular" in to_arg_str:
                sec_fn = Function("cellSecretion")
                sec_fn.args.append(fn.args[0])
                fn = sec_fn
                break
            if "plasma membrane" in to_arg_str:
                surf_fn = Function("cellSurfaceExpression")
                surf_fn.args.append(fn.args[0])
                fn = surf_fn
                break

    return fn


def optimize_function(fn: "Function") -> "Function":
    """Optimize function to best practice BEL"""

    fn = optimize_rxn(fn)
    fn = optimize_tloc(fn)  # Has to come after optimize_rxn()

    return fn
