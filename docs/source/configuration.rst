Configuration
===============

All of the BELbio tools share the same configuration files. There are separate sections for configuration that is specific to a particular application or tool (e.g. bel_api, bel_resources or bel python package).

Location
------------

Get first belbio_conf.{yml|yaml} and belbio_secrets.{yml|yaml} files in:

    1. <current dir>/belbio_{conf|secrets}.{yaml|yml}
    2. ENV['BELBIO_CONF']/belbio_{conf|secrets}.{yaml|yml}
    3. ~/.belbio/{conf|secrets}   (dotfiles in home directory)

Download example files from:

* `BELBio Conf <https://raw.githubusercontent.com/belbio/bel/master/belbio_conf.yml.example>`_
* `BELBio Secrets <https://raw.githubusercontent.com/belbio/bel/master/belbio_secrets.yml.example>`_

Main Configuration File
--------------------------

.. include:: ../../belbio_conf.yml.example
    :code: yaml

Secrets Configuration File
-----------------------------

.. include:: ../../belbio_secrets.yml.example
    :code: yaml
