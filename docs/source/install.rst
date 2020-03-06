Installation
==================

Users
--------

*bel* works on Python versions 3.6+.  Is is supported on OSX and Linux and works (but tested less frequently) on Windows.

Installing is simple.

    pip install bel

Developers
--------------

If you are a developer, please see the :doc:`link_contributing` first and then:

    git clone <your forked version of bel>

The following commands sets up a virtual environment, installs *bel* as an editable package and then pip installs the requirements.txt packages.

    make dev_install

To run the tests

    make tests
