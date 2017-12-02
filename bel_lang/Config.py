#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Usage:  import utils.configuration as config

This reads the belbio_conf file from either ~/bel_resources
"""

import os
import os.path
import yaml
import copy
import re
from typing import Mapping, Any
import collections
import functools

import logging
log = logging.getLogger(__name__)


def get_current_module_dir() -> str:
    """Get current module filepath"""

    cur_module_fp = os.path.dirname(os.path.realpath(__file__))
    return cur_module_fp


def get_root_filepath() -> str:
    """Get bel_resource root filepath

    root filepath is 2 levels up from where this Config.py file is located
    """

    cmd = get_current_module_dir()
    bel_resources_root = os.path.dirname(os.path.dirname(cmd))

    return bel_resources_root


def get_version() -> str:

    bel_resources_root = get_root_filepath()
    version_fp = f'{bel_resources_root}/VERSION'

    version = None
    if os.path.exists(version_fp):
        with open(version_fp, 'r') as f:
            version = f.readline().rstrip()

    return version


def get_belbio_conf_files():
    """Get first belbio_conf and belbio_secrets files in current dir or home directory

    This will look for belbio_conf.yaml or .belbio_conf in current or home directories
    It will also look for belbio_secrets.yaml or .belbio_secrets in current or parent dirs
    """

    # for root, dirs, files in os.walk(os.getcwd(), topdown=False):
    #     print('Root', root)
    #     for fn in files:
    #         print('  FN:', fn)

    home = os.path.expanduser('~')
    cwd = os.getcwd()

    belbio_conf_fp, belbio_secrets_fp = '', ''
    for path in [cwd, home]:
        if belbio_conf_fp:
            break
        for fn in ['belbio_conf.yaml', '.belbio_conf']:
            if os.path.exists(f'{path}/{fn}'):
                belbio_conf_fp = f'{path}/{fn}'
                log.info(f'Using {belbio_conf_fp} file for configuration')
                break

    for path in [cwd, home]:
        if belbio_secrets_fp:
            break
        for fn in ['belbio_secrets.yaml', '.belbio_secrets']:
            if os.path.exists(f'{path}/{fn}'):
                belbio_secrets_fp = f'{path}/{fn}'
                log.info(f'Using {belbio_secrets_fp} file for secrets configuration')
                break

    if not belbio_conf_fp:
        log.error('No belbio_conf file found.  Cannot continue')
        quit()

    if not belbio_secrets_fp:
        log.warn('No belbio_secrets file found.')

    return (belbio_conf_fp, belbio_secrets_fp)


def process_files(config):
    """"""

    root_fp = get_root_filepath()
    config['bel_resources']['file_locations']['root'] = root_fp

    for loc in config['bel_resources']['file_locations']:
        loc_val = config['bel_resources']['file_locations'][loc]
        if not re.match('/', loc_val):
            config['bel_resources']['file_locations'][loc] = f'{root_fp}/{loc_val}'

    return config


def load_configuration():
    """Load the configuration"""

    (belbio_conf_fp, belbio_secrets_fp) = get_belbio_conf_files()

    if belbio_conf_fp:
        with open(belbio_conf_fp, 'r') as f:
            config = yaml.load(f)

    if belbio_secrets_fp:
        with open(belbio_secrets_fp, 'r') as f:
            secrets = yaml.load(f)
            config['secrets'] = copy.deepcopy(secrets)

    version = get_version()
    config['bel_resources'].update({'version': version})

    config = process_files(config)

    return config


# https://stackoverflow.com/questions/7204805/dictionaries-of-dictionaries-merge
def dict_merge(a, b):
    if not isinstance(b, dict):
        return b
    result = copy.deepcopy(a)
    for k, v in b.iteritems():
        if k in result and isinstance(result[k], dict):
                result[k] = dict_merge(result[k], v)
        else:
            result[k] = copy.deepcopy(v)
    return result


# https://stackoverflow.com/questions/7204805/dictionaries-of-dictionaries-merge
def rec_merge(d1, d2):
    """ Recursively merge two dictionaries

    Update two dicts of dicts recursively,
    if either mapping has leaves that are non-dicts,
    the second's leaf overwrites the first's.

    import collections
    import functools

    e.g. functools.reduce(rec_merge, (d1, d2, d3, d4))
    """

    for k, v in d1.items():
        if k in d2:
            # this next check is the only difference!
            if all(isinstance(e, collections.MutableMapping) for e in (v, d2[k])):
                d2[k] = rec_merge(v, d2[k])
            # we could further check types and merge as appropriate here.
    d3 = d1.copy()
    d3.update(d2)
    return d3


def merge_config(config: Mapping[str, Any], override_config: Mapping[str, Any] = None, override_config_fn: str = None) -> Mapping[str, Any]:
    """Override config with additional configuration in override_config or override_config_fn

    Args:
        config: original configuration
        override_config: new configuration to override/extend current config
        override_config_fn: new configuration filename as YAML file
    """

    if override_config_fn:
        with open(override_config_fn, 'r') as f:
            override_config = yaml.load(f)

    if not override_config:
        log.info('Missing override_config')

    return functools.reduce(rec_merge, (config, override_config))


def main():

    import json
    config = load_configuration()
    print('Config:\n', json.dumps(load_configuration(), indent=4))
    print('ns def', config['bel_resources']['file_locations']['namespaces_definition'])


if __name__ == '__main__':
    main()

else:
    config = load_configuration()
