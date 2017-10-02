import bel_lang
import pytest
import pprint

VERSION = '2.0.0'
ENDPOINT = 'http://example.com/endpoint'
statement_to_parse = 'composite(p(SFAM:"Histone H3 Family", pmod(Ac)), p(SFAM:"Histone H4 Family", pmod(Ac)))'
# statement_to_parse = 'act(p(HGNC:AKT1), ma(kin)) increases complex(p(HGNC:SKP2), p(SFAM:"FOXO Family"))'

bel_instance = bel_lang.BEL(VERSION, ENDPOINT)
parse_obj = bel_instance.parse(statement_to_parse)

# bad_stmts = bel_instance._create(100, 3)
#
# for s in bad_stmts:
#     print(s.string_form)
#     print()

comp = bel_instance.computed(parse_obj.ast)
for num, computed, in enumerate(comp, start=1):
    print('{}. {}'.format(num, computed))
# print()
# print()
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
