import bel_lang
import pytest
import pprint
import json


class Colors:
    PINK = '\033[95m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

VERSION = '2.0.0'
ENDPOINT = 'http://example.com/endpoint'
bel_instance = bel_lang.BEL(VERSION, ENDPOINT)

# statement_to_parse = 'tloc(p(HGNC:NFE2L2), fromLoc(MESHCL:Cytoplasm), toLoc(MESHCL:"Cell Nucleus"))'
# statement_to_parse = 'act(p(SFAM:"MAPK p38 Family"), ma(GO:"kinase activity")) decreases deg(p(HGNC:HBP1))'
statement_to_parse = 'p(HGNC:AKT1) increases p(HGNC:EGF)'
print('{}STATEMENT TO PARSE: {}{}'.format(Colors.RED, statement_to_parse, Colors.END))

parse_obj = bel_instance.parse(statement_to_parse)
comp = bel_instance.computed(parse_obj.ast)

print()
print('{}ALL COMPUTED STATEMENTS: {}'.format(Colors.RED, Colors.END))
for num, computed, in enumerate(comp, start=1):
    print('{}. {}'.format(num, computed))

# print('list of computed edges:\n')
# for c in comp:
#     print('\t', c)

# stmts = B.load('dev/bel2_test_statements.txt', loadn=1, preprocess=True)
#
# for s in stmts:
#     print('\n\n\n\n')
#
#     p = B.parse(s)
#     ast = p.ast
#
#     pprint.pprint(ast)
#     exit()
#
#     c = B.computed(ast)
#
#
# statement = 'p(fus(HGNC:BCR, "p.1_426", HGNC:JAK2, "p.812_1132"))'
# expected = ['p(HGNC:BCR) hasFusion p(fus(HGNC:BCR, "p.1_426", HGNC:JAK2, "p.812_1132"))',
#             'p(HGNC:JAK2) hasFusion p(fus(HGNC:BCR, "p.1_426", HGNC:JAK2, "p.812_1132"))']
# ast = B.parse(statement).ast
# l = B.computed(ast)
#
# pprint.pprint(l)
#
# # assert expected == l
