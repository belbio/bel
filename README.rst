BEL package
=================

.. image:: https://travis-ci.org/belbio/bel.svg?branch=master
   :target: https://travis-ci.org/belbio/bel
   :alt: Travis Build/Testing

.. CodeClimate code coverage
.. .. image:: https://api.codeclimate.com/v1/badges/3fdfec7ee96fc639bb09/test_coverage
..    :target: https://codeclimate.com/github/belbio/bel/test_coverage
..    :alt: Test Coverage

.. image:: https://codecov.io/gh/belbio/bel/branch/master/graph/badge.svg
  :target: https://codecov.io/gh/belbio/bel
  :alt: Test Coverage

.. image:: https://readthedocs.org/projects/bel/badge/?version=latest
   :target: https://readthedocs.org/projects/bel/?badge=latest
   :alt: Documentation Status

Informational badges
-----------------------

.. image:: https://badge.fury.io/py/bel.svg
   :target: https://badge.fury.io/py/bel
   :alt: PyPi Latest

.. image:: https://img.shields.io/pypi/l/bel.svg
    :target: https://pypi.python.org/pypi/bel
    :alt: BEL License

.. image:: https://img.shields.io/pypi/pyversions/bel.svg
    :target: https://pypi.python.org/pypi/bel
    :alt: Python Versions Supported

.. image:: https://badge.waffle.io/belbio/project.svg?columns=all
   :target: https://waffle.io/belbio/project
   :alt: 'Waffle.io - Columns and their card count'


.. image:: https://api.codeclimate.com/v1/badges/3fdfec7ee96fc639bb09/maintainability
   :target: https://codeclimate.com/github/belbio/bel/maintainability
   :alt: Maintainability


BEL Python Package
---------------------

Main documentation is at `<http://bel.readthedocs.io/en/latest/>`.

Currently handles BEL 2.0.0, but it is easily extensible to new versions of BEL.

Planned features
---------------------

* [Done] Allow multiple BEL Specification files for different BEL versions (including experimental versions)
* [Done] Provide a standard EBNF file for parser generation for each BEL Specification
* [Done] Identify syntax issues in the statement and provide suggestions on fixing them
* [Done] Identify semantic issues in the statement and provide suggestions on fixing them
* [Done] Identify unknown Namespaces or Namespace values
* [Done] Convert BEL statements into an AST and then back into a BEL Statement
* Provide autocompletion suggestions given a location in the BEL Statement
* Read a Nanopub and validate the full Nanopub, e.g. the BEL statement, Annotations, Citation, etc
* BEL Pipeline - Process new Nanopubs in NanopubStore into Edges and load in EdgeStore
* [Done] Convert BELScript into BEL Nanopubs
* Command line interface (partially done)

Install
---------------

    pip install bel


