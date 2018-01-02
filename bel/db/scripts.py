#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Usage:  program.py <customer>

"""

from elasticsearch import Elasticsearch
import yaml
import logging
import logging.config
import click

import bel.db
from bel.Config import config

# Globals
server = config['bel_api']['servers']['elasticsearch']
es = bel.db.elasticsearch.get_client()



if __name__ == '__main__':
    # Setup logging
    global log

    logging.config.dictConfig(config['logging'])
    log = logging.getLogger(name='load_elasticsearch')

    main()
