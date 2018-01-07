BEL CLI
==========

The BEL CLI commands are installed by pip install bel. These are nested commands
for which you can review the help at each nested level by:

*belc* stands for BEL CLI (Command Line Interface)

.. code-block:: bash

    belc --help
    belc stmt --help
    belc stmt canonicalize --help


.. click:: bel.scripts:belc
   :prog: belc
   :show-nested:


.. Readthedocs hasn't updated to python 3.6 yet so the f expressions are breaking the sphinx-click extension output
