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

.. image:: https://badge.fury.io/py/bel.svg
   :target: https://badge.fury.io/py/bel
   :alt: PyPi Latest

.. image:: https://readthedocs.org/projects/bel/badge/?version=latest
   :target: https://readthedocs.org/projects/bel/?badge=latest
   :alt: Documentation Status

Informational badges
-----------------------
.. image:: https://badge.waffle.io/belbio/project.svg?columns=all
   :target: https://waffle.io/belbio/project
   :alt: 'Waffle.io - Columns and their card count'


.. image:: https://api.codeclimate.com/v1/badges/3fdfec7ee96fc639bb09/maintainability
   :target: https://codeclimate.com/github/belbio/bel/maintainability
   :alt: Maintainability


BEL Language
----------------

Initial Plans
---------------

An approach is to use an EBNF template for BEL and a JSON-based data file to create a fully-specified EBNF input for a parsing generator that will allow us to process a potential full or partial BEL statement, convert it to an AST and be able to convert an AST back to a BEL Statement.

Goals
------------

* Read a standard language descriptor file (e.g. EBNF) for parser generation
* Use configuration files for creating a BEL V.x parser/validator/autocomplete engine
* Allow full or partial BEL Statements
* Identify syntax issues in the statement and provide suggestions on fixing them
* Identify semantic issues in the statement and provide suggestions on fixing them
* Identify unknown Namespaces or Namespace values
* Read a Nanopub and validate the full Nanopub, e.g. the BEL statement, Annotations, Citation, etc
* Provide location-based parser state information (e.g. location 10 is in the required arg part of a protein abundance - e.g. the protein value)
* Provide autocompletion suggestions given a location in the BEL Statement
* Convert BEL statements into an AST and then back into a BEL Statement

Install
---------------

    pip install git+https://github.com/belbio/bel@v<RELEASE>#egg=bel-<RELEASE>

Development Notes
-------------------

We will develop a makefile to handle updating the BEL versions, creating EBNF files,
updating the version, running tests and deploying the package to PyPi.


Setting up bel for local development
-------------------------------------------

1. `git clone git@github.com:belbio/bel.git`
1. `cd bel`
1. Setup Virtual Environment `python3.6 -m venv .venv --prompt bel`
1. Install python packages needed `pip install -r requirements.txt`
1. Install local bel `pip install -e .`

Updating version
------------------

Use one of the following commands depending on what part of the semantic version you
want to increase.

    bumpversion major
    bumpversion minor
    bumpversion patch

These commands use the .bumpversion.cfg file to determine in which files to update the
semantic version.

BEL Nanopub processing library.  The performs the following functions:

* BEL Nanopub validation (in development)

  * Nanopub JSONschema validation
  * BEL statement validation
  * BEL context validation

* BEL Nanopub -> Edge conversion (BEL Pipeline)
* CLI scripts to convert BEL Nanopubs to BEL Edges and perform validation


