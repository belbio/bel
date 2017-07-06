# BEL Parsing package

BEL parsing python package

## Initial Plans

An approach is to use an EBNF template for BEL and a JSON-based data file to create a fully-specified EBNF input for a parsing generator that will allow us to process a potential full or partial BEL statement, convert it to an AST and be able to convert an AST back to a BEL Statement.

## Goals

* Read a standard language descriptor file (e.g. EBNF) for parser generation
* Use configuration files for creating a BEL V.x parser/validator/autocomplete engine
* Allow full or partial BEL Statements
* Identify syntax issues in the statement and provide suggestions on fixing them
* Identify semantic issues in the statement and provide suggestions on fixing them
* Identify unknown Namespaces or Namespace values
* Read a Nanopub and validate the full Nanopub, e.g. the BEL statement, Annotations, Citation, etc
* Provide location-based parser state information (e.g. location 10 is in the required parameter part of a protein abundance - e.g. the protein value)
* Provide autocompletion suggestions given a location in the BEL Statement
* Convert BEL statements into an AST and then back into a BEL Statement
