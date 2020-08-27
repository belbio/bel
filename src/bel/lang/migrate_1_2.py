#!/usr/bin/env python
# -*- coding: utf-8 -*-


# Migrate BEL from 1 to 2.0.0
#

# Standard Library
import json

# Third Party Imports
from loguru import logger

# Local Imports
import bel.belspec.crud
import bel.core.settings as settings
from bel.lang.belobj import BEL
from bel.belspec.crud import get_enhanced_belspec
from bel.lang.ast import BELAst, Function, NSArg, StrArg


version = bel.belspec.crud.get_latest_version()
bo = BEL("", version=version)
belspec = get_enhanced_belspec(bo.version)


def migrate(belstr: str) -> str:
    """Migrate BEL 1 to 2.0.0

    Args:
        bel: BEL 1

    Returns:
        bel: BEL 2
    """

    bo.parse(belstr)

    return migrate_ast(bo.ast).to_string()


def migrate_into_triple(belstr: str) -> str:
    """Migrate BEL1 assertion into BEL 2.0.0 SRO triple"""

    bo.parse(belstr)

    return migrate_ast(bo.ast).to_triple()


def migrate_ast(ast: BELAst) -> BELAst:

    # Process Subject
    bo.ast.subject = convert(bo.ast.subject)

    if bo.ast.object:
        if bo.ast.object.type == "BELAst":
            bo.ast.object.subject = convert(bo.ast.object.subject)
            if bo.ast.object.object:
                bo.ast.object.object = convert(bo.ast.object.object)
        else:
            bo.ast.object = convert(bo.ast.object)

    return bo.ast


def convert(ast):
    """Convert BEL1 AST Function to BEL2 AST Function"""

    if ast and ast.type == "Function":
        # Activity function conversion
        if (
            ast.name != "molecularActivity"
            and ast.name in belspec["namespaces"]["Activity"]["list"]
        ):
            print("name", ast.name, "type", ast.type)
            ast = convert_activity(ast)
            return ast  # Otherwise - this will trigger on the BEL2 molecularActivity

        # translocation conversion
        elif ast.name in ["tloc", "translocation"]:
            ast = convert_tloc(ast)

        fus_flag = False
        for idx, arg in enumerate(ast.args):
            if arg.__class__.__name__ == "Function":

                # Fix substitution -> variation()
                if arg.name in ["sub", "substitution"]:
                    ast.args[idx] = convert_sub(arg)

                elif arg.name in ["trunc", "truncation"]:
                    ast.args[idx] = convert_trunc(arg)

                elif arg.name in ["pmod", "proteinModification"]:
                    ast.args[idx] = convert_pmod(arg)

                elif arg.name in ["fus", "fusion"]:
                    fus_flag = True

                # Recursively process Functions
                ast.args[idx] = convert(ast.args[idx])

        if fus_flag:
            ast = convert_fus(ast)

    return ast


def convert_tloc(ast):
    """Convert BEL1 tloc() to BEL2"""

    from_loc_arg = ast.args[1]
    to_loc_arg = ast.args[2]
    from_loc = Function("fromLoc", version=version, parent=ast)
    from_loc.add_argument(NSArg(from_loc_arg.namespace, from_loc_arg.value, parent=from_loc))
    to_loc = Function("toLoc", version=version, parent=ast)
    to_loc.add_argument(NSArg(to_loc_arg.namespace, to_loc_arg.value, parent=to_loc))

    ast.args[1] = from_loc
    ast.args[2] = to_loc

    return ast


def convert_activity(ast):
    """Convert BEL1 activities to BEL2 act()"""

    if len(ast.args) > 1:
        logger.error(f"Activity should not have more than 1 argument {ast.to_string()}")

    p_arg = ast.args[0]  # protein argument
    print("p_arg", p_arg)
    ma_arg = Function("ma", version=version)
    ma_arg.add_argument(StrArg(ast.name, ma_arg))
    p_arg.change_parent_fn(ma_arg)
    ast = Function("activity", version=version)
    p_arg.change_parent_fn(ast)
    ast.add_argument(p_arg)
    ast.add_argument(ma_arg)

    return ast


def convert_pmod(pmod):
    """Update BEL1 pmod() protein modification term"""

    if pmod.args[0].value in belspec["bel1_migration"]["protein_modifications"]:
        pmod.args[0].value = belspec["bel1_migration"]["protein_modifications"][pmod.args[0].value]

    return pmod


def convert_fus(ast):
    """Convert BEL1 fus() to BEL2 fus()"""

    parent_fn_name = ast.name_short
    prefix_list = {"p": "p.", "r": "r.", "g": "c."}
    prefix = prefix_list[parent_fn_name]

    fus1_ns = ast.args[0].namespace
    fus1_val = ast.args[0].value

    arg_fus = ast.args[1]
    fus_args = [None, "?", "?"]
    for idx, arg in enumerate(arg_fus.args):
        fus_args[idx] = arg

    fus2_ns = fus_args[0].namespace
    fus2_val = fus_args[0].value

    if fus_args[1] == "?":
        fus1_range = fus_args[1]
    else:
        fus1_range = f'"{prefix}1_{fus_args[1].value}"'

    if fus_args[2] == "?":
        fus2_range = fus_args[2]
    else:
        fus2_range = f'"{prefix}{fus_args[2].value}_?"'

    fus = Function("fus", version=version, parent=ast)
    fus.args = [
        NSArg(fus1_ns, fus1_val, fus),
        StrArg(fus1_range, fus),
        NSArg(fus2_ns, fus2_val, fus),
        StrArg(fus2_range, fus),
    ]

    # Remove BEL
    ast_args = ast.args
    ast_args.pop(0)
    ast_args.pop(0)

    if ast_args == [None]:
        ast_args = []

    ast.args = []
    ast.add_argument(fus)

    if len(ast_args) > 0:
        ast.args.extend(ast_args)

    return ast


def convert_sub(sub):
    """Convert BEL1 sub() to BEL2 var()"""

    args = sub.args
    (ref_aa, pos, new_aa) = args

    parent_fn_name = sub.parent_function.name_short
    prefix_list = {"p": "p.", "r": "r.", "g": "c."}
    prefix = prefix_list[parent_fn_name]

    new_var_arg = f'"{prefix}{belspec["namespaces"]["AminoAcid"]["to_short"][ref_aa.value]}{pos.value}{belspec["namespaces"]["AminoAcid"]["to_short"][new_aa.value]}"'

    new_var = Function("var", version=version)

    new_var.add_argument(StrArg(new_var_arg, new_var))

    return new_var


def convert_trunc(trunc):
    """Convert BEL1 trunc() to BEL2 var()"""

    parent_fn_name = trunc.parent_function.name_short
    prefix_list = {"p": "p.", "r": "r.", "g": "c."}
    prefix = prefix_list[parent_fn_name]

    new_var_arg = f'"truncated at {trunc.args[0].value}"'

    new_var = Function("var", version=version)

    new_var.add_argument(StrArg(new_var_arg, new_var))

    return new_var


def main():

    import bel.lang.migrate_1_2

    bel1 = "kin(p(HGNC:BRAF))"

    bel1 = "p(HGNC:PIK3CA, sub(E, 545, K))"
    # bel2 = 'p(HGNC:PIK3CA, var(p.Glu545Lys))'

    bel1 = "r(HGNC:BCR, fus(HGNC:JAK2, 1875, 2626), pmod(P))"
    bel2 = 'r(fus(HGNC:BCR, "r.1_1875", HGNC:JAK2, "r.2626_?"), pmod(Ph))'

    # bel1 = 'p(HGNC:MAPK1, pmod(P, Thr, 185))'
    # bel2 = 'p(HGNC:MAPK1, pmod(Ph, Thr, 185))'

    # bel1 = 'tloc(p(HGNC:EGFR), MESHCL:Cytoplasm, MESHCL:"Cell Nucleus")'
    # bel2 = 'tloc(p(HGNC:EGFR), fromLoc(MESHCL:Cytoplasm), toLoc(MESHCL:"Cell Nucleus"))'

    # bel1 = 'p(HGNC:ABCA1, trunc(1851))'
    # bel2 = 'p(HGNC:ABCA1, var("truncated at 1851"))'

    bel2 = bel.lang.migrate_1_2.migrate(bel1)

    print("BEL2", bel2)


if __name__ == "__main__":
    main()
