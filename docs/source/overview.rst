Overview
--------


.. note::

  Namespace values (NSArg) need to be quoted if they contain whitespace, comma or ')'. This is due to how BEL is parsed. An NSArg (namespace:term, e.g. namespace argument of a BEL function) is parsed by looking for an ALLCAPS namespace prefix, colon and then a term name. The parsing continues for the term name until we find a space, comma or end parenthesis ')'. If the term contains any of those characters, it has to be quoted using double-quotes.

.. note::

  Any character except an un-escaped double quote can be in the NSArg if it is quoted including spaces, commas and ')'.
