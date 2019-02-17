# Compute Edges related code

import copy
from typing import List, Any, Mapping, MutableSequence

from bel.lang.ast import BELAst, Function, NSArg

from structlog import get_logger
log = get_logger()

# Typings
Edges = MutableSequence[Mapping[str, Any]]
BELSpec = Mapping[str, Any]
ComputeRules = List[str]

locations = {'extracellular': NSArg('GO', "extracellular space"), 'cellsurface': NSArg('GO', "cell surface")}


def compute_edges(ast: BELAst, spec: BELSpec) -> Edges:
    """Compute edges"""

    edges = []
    if ast.bel_object.__class__.__name__ == 'BELAst':
        edges.append(ast.bel_object)

    process_ast(edges, ast, spec)
    return edges


def process_ast(edges, ast, spec):

    if isinstance(ast, BELAst):
        pass

    # TODO composite is not being addressed right now
    # TODO
    elif isinstance(ast, Function):
        if ast.name in ('complex', 'complexAbundance'):
            for arg in ast.args:
                edges.append(BELAst(ast, 'hasComponent', arg, spec))

        elif ast.name in ('act', 'activity'):
            subject = ast.args[0]
            edge = BELAst(subject, 'hasActivity', ast, spec)
            edges.append(edge)

        elif ast.name in ('pmod', 'proteinModification'):
            parent = ast.parent_function
            src_abundance = Function(parent.name, spec)
            src_abundance.add_argument(parent.args[0])
            edges.append(BELAst(src_abundance, 'hasModification', parent, spec))

        elif ast.name in ('var', 'variant'):
            parent = ast.parent_function
            src_abundance = Function(parent.name, spec)
            src_abundance.add_argument(parent.args[0])
            edges.append(BELAst(src_abundance, 'hasVariant', parent, spec))

        elif ast.name in ('frag', 'fragment'):
            parent = ast.parent_function
            src_abundance = Function(parent.name, spec)
            src_abundance.add_argument(parent.args[0])
            edges.append(BELAst(src_abundance, 'hasFragment', parent, spec))

        elif ast.name in ('loc', 'location'):
            parent = ast.parent_function
            src_abundance = Function(parent.name, spec)
            src_abundance.add_argument(parent.args[0])
            edges.append(BELAst(src_abundance, 'hasLocation', parent, spec))

        elif ast.name in ('tloc', 'translocation'):
            src_abundance = ast.args[0]
            from_abundance = copy.deepcopy(src_abundance)
            from_loc = Function('loc', spec)
            from_loc.add_argument(ast.args[1].args[0])
            from_abundance.add_argument(from_loc)

            to_abundance = copy.deepcopy(src_abundance)
            to_loc = Function('loc', spec)
            to_loc.add_argument(ast.args[2].args[0])
            to_abundance.add_argument(to_loc)

            edges.append(BELAst(ast, 'decreases', from_abundance, spec))
            edges.append(BELAst(ast, 'increases', to_abundance, spec))
            edges.append(BELAst(src_abundance, 'hasLocation', from_abundance, spec))
            edges.append(BELAst(src_abundance, 'hasLocation', to_abundance, spec))

        elif ast.name in ('sec', 'cellSecretion', 'surf', 'cellSurfaceExpression'):
            target_loc = locations['extracellular']
            if ast.name in ('surf', 'cellSurfaceExpression'):
                target_loc = locations['cellsurface']

            src_abundance = ast.args[0]
            to_abundance = copy.deepcopy(src_abundance)
            to_loc = Function('loc', spec)
            to_loc.add_argument(target_loc)
            to_abundance.add_argument(to_loc)
            edges.append(BELAst(ast, 'increases', to_abundance, spec))
            edges.append(BELAst(src_abundance, 'hasLocation', to_abundance, spec))

        elif ast.name in ('deg', 'degradation'):
            edges.append(BELAst(ast, 'directlyDecreases', ast.args[0], spec))

        elif ast.name in ('fus', 'fusion'):
            parent = ast.parent_function

            src_abundance = Function(parent.name, spec)
            src_abundance.add_argument(ast.args[0])
            edges.append(BELAst(src_abundance, 'hasFusion', parent, spec))

            src_abundance = Function(parent.name, spec)
            src_abundance.add_argument(ast.args[2])
            edges.append(BELAst(src_abundance, 'hasFusion', parent, spec))

        elif ast.name in ('reactants', 'products'):
            parent = ast.parent_function

            relation = 'hasProduct'
            if ast.name == 'reactants':
                relation = 'hasReactant'

            for arg in ast.args:
                edges.append(BELAst(parent, relation, arg, spec))

        elif ast.name in ('product', 'fusion'):
            parent = ast.parent_function

            src_abundance = Function(parent.name, spec)
            src_abundance.add_argument(ast.args[0])
            edges.append(BELAst(src_abundance, 'hasFusion', parent, spec))

            src_abundance = Function(parent.name, spec)
            src_abundance.add_argument(ast.args[2])
            edges.append(BELAst(src_abundance, 'hasFusion', parent, spec))

    # Recursively process every element by processing BELAst and Functions
    if hasattr(ast, 'args'):
        for arg in ast.args:
            process_ast(edges, arg, spec)


# TODO - not used anymore - review to see if we want to take notes on the approach
def process_rule(edges: Edges, ast: Function, rule: Mapping[str, Any], spec: BELSpec):
    """Process computed edge rule

    Recursively processes BELAst versus a single computed edge rule

    Args:
        edges (List[Tuple[Union[Function, str], str, Function]]): BEL Edge ASTs
        ast (Function): BEL Function AST
        rule (Mapping[str, Any]: computed edge rule
    """
    ast_type = ast.__class__.__name__
    trigger_functions = rule.get('trigger_function', [])
    trigger_types = rule.get('trigger_type', [])
    rule_subject = rule.get('subject')
    rule_relation = rule.get('relation')
    rule_object = rule.get('object')

    log.debug(f'Running {rule_relation}  Type: {ast_type}')

    if isinstance(ast, Function):
        function_name = ast.name
        args = ast.args
        parent_function = ast.parent_function

        if function_name in trigger_functions:
            if rule_subject == 'trigger_value':
                subject = ast

            if rule_object == 'args':
                for arg in args:
                    log.debug(f'1: {subject} {arg}')
                    edge_ast = BELAst(subject, rule_relation, arg, spec)
                    edges.append(edge_ast)
            elif rule_object == 'parent_function' and parent_function:
                log.debug(f'2: {subject} {parent_function}')
                edge_ast = BELAst(subject, rule_relation, parent_function, spec)
                edges.append(edge_ast)

        elif ast_type in trigger_types:
            if rule_subject == 'trigger_value':
                subject = ast

            if rule_object == 'args':
                for arg in args:
                    log.debug(f'3: {subject} {arg}')
                    edge_ast = BELAst(subject, rule_relation, arg, spec)
                    edges.append(edge_ast)
            elif rule_object == 'parent_function' and parent_function:
                log.debug(f'4: {subject} {parent_function}')
                edge_ast = BELAst(subject, rule_relation, parent_function, spec)
                edges.append(edge_ast)

    if isinstance(ast, NSArg):
        term = "{}:{}".format(ast.namespace, ast.value)
        parent_function = ast.parent_function

        if ast_type in trigger_types:
            if rule_subject == 'trigger_value':
                subject = term

            if rule_object == 'args':
                for arg in args:
                    log.debug(f'5: {subject} {arg}')
                    edge_ast = BELAst(subject, rule_relation, arg, spec)
                    edges.append(edge_ast)
            elif rule_object == 'parent_function' and parent_function:
                log.debug(f'6: {subject} {parent_function}')
                edge_ast = BELAst(subject, rule_relation, parent_function, spec)
                edges.append(edge_ast)

    # Recursively process every element by processing BELAst and Functions
    if hasattr(ast, 'args'):
        for arg in ast.args:
            process_rule(edges, arg, rule, spec)

