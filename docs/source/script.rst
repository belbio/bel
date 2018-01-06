BEL CLI
==========

The BEL CLI commands are installed by pip install bel. These are nested commands
for which you can review the help at each nested level by:

.. code-block:: bash

    bel --help
    bel stmt --help
    bel stmt canonicalize --help


.. click:: bel.scripts:bel
   :prog: bel
   :show-nested:


.. Readthedocs hasn't updated to python 3.6 yet so the f expressions are breaking the sphinx-click extension output
