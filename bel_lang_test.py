import bel_lang
import pytest
import pprint

VERSION = '2.0.0'
ENDPOINT = 'http://example.com/endpoint'
statement_to_parse = 'act(complex(ABC:123), ma(ABC))'
# statement_to_parse = 'complex(ABC:123)'

bel_instance = bel_lang.BEL(VERSION, ENDPOINT)
parse_obj = bel_instance.parse(statement_to_parse)

# bad_stmts = bel_instance._create(100, 3)
#
# for s in bad_stmts:
#     print(s.string_form)
#     print()

comp = bel_instance.computed(parse_obj.ast)
print()
print()
print()
print(comp)

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
