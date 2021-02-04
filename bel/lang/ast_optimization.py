# Standard Library
from typing import TYPE_CHECKING

# Local
from bel.lang.ast_utils import compare_fn_args

if TYPE_CHECKING:
    # Local
    from bel.lang.ast import Function

# TODO - Add rxn() to tloc() and tloc() -> sec() or surf()


def optimize_rxn(rxn: "Function") -> "Function":
    """Transform reaction into more optimal BEL"""

    parent = rxn.parent
    reactants = rxn.args[0]
    products = rxn.args[1]
    if reactants.name != "reactants" or products.name != "products":
        return rxn

    # Convert reactants(A, B) -> products(complex(A, B))  SHOULD BE complex(A, B)

    if products.args[0].name == "complexAbundance" and compare_fn_args(
        reactants.args, products.args[0].args, ignore_locations=True
    ):
        rxn = products.args[0]
        rxn.parent = parent

    return rxn


def optimize_function(fn: "Function") -> "Function":
    """Optimize function to best practice BEL"""

    fn = optimize_rxn(fn)

    return fn
