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

