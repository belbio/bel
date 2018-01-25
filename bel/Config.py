#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Usage:  import bel.Config as config

Get first belbio_conf.{yml|yaml} and belbio_secrets.{yml|yaml} files in:
    current dir or parent directories starting with immediate parent of current dir
    OR
    ~/.belbio_{conf|secrets}   (dotfiles in home directory)
"""

import os
import os.path
import yaml
import copy
from typing import Mapping, Any
import functools
import collections

import logging
log = logging.getLogger(__name__)


def get_belbio_conf_files():
    """Get belbio configuration from files
    """

    home = os.path.expanduser('~')
    cwd = os.getcwd()

    home_conf_fn = '.belbio_conf'
    home_secrets_fn = '.belbio_secrets'

    conf_fns = ['belbio_conf.yml', 'belbio_conf.yaml']
    secret_fns = ['belbio_secrets.yml', 'belbio_secrets.yaml']

    belbio_conf_fp, belbio_secrets_fp = '', ''

    # Look for belbio_conf file
    test_path = cwd
    break_flag = False
    while test_path:
        for fn in conf_fns:
            if test_path == '/':
                check_fn = fn
            else:
                check_fn = f'{test_path}/{fn}'
            if os.path.exists(check_fn):
                belbio_conf_fp = check_fn
                break_flag = True
                break
        if break_flag or test_path == '/':
            break
        test_path = os.path.dirname(test_path)

    if not belbio_conf_fp and os.path.exists(f'{home}/{home_conf_fn}'):
        belbio_conf_fp = f'{home}/{home_conf_fn}'

    # Look for belbio_secrets file
    test_path = cwd
    break_flag = False
    while test_path:
        for fn in secret_fns:
            if test_path == '/':
                check_fn = fn
            else:
                check_fn = f'{test_path}/{fn}'
            if os.path.exists(check_fn):
                belbio_secrets_fp = check_fn
                break_flag = True
                break
        if break_flag or test_path == '/':
            break
        test_path = os.path.dirname(test_path)

    if not belbio_secrets_fp and os.path.exists(f'{home}/{home_secrets_fn}'):
        belbio_secrets_fp = f'{home}/{home_secrets_fn}'

    if not belbio_conf_fp:
        log.error('No belbio_conf file found.  Cannot continue')
        quit()

    if not belbio_secrets_fp:
        log.warn('No belbio_secrets file found.')

    return (belbio_conf_fp, belbio_secrets_fp)


def get_versions(config) -> dict:
    """Get versions of bel modules and tools"""

    # Collect bel package version
    try:
        import bel.__version__
        config['bel']['version'] = bel.__version__.__version__
    except KeyError:
        config['bel'] = {'version': bel.__version__.__version__}
    except ModuleNotFoundError:
        pass

    # Collect bel_resources version
    try:
        import tools.__version__
        config['bel_resources']['version'] = tools.__version__.__version__
    except KeyError:
        config['bel_resources'] = {'version': tools.__version__.__version__}
    except ModuleNotFoundError:
        pass

    # Collect bel_api version
    try:
        import __version__
        if __version__.__name__ == 'BELBIO API':
            config['bel_api']['version'] = __version__.__version__
    except KeyError:
        if __version__.__name__ == 'BELBIO API':
            config['bel_api'] = {'version': __version__.__version__}
    except ModuleNotFoundError:
        pass

    return config


def load_configuration():
    """Load the configuration"""

    (belbio_conf_fp, belbio_secrets_fp) = get_belbio_conf_files()
    log.info(f'Using conf file: {belbio_conf_fp}')
    log.info(f'Using secrets file: {belbio_secrets_fp}')

    config = {}
    if belbio_conf_fp:
        with open(belbio_conf_fp, 'r') as f:
            config = yaml.load(f)
            config['source_files'] = {}
            config['source_files']['conf'] = belbio_conf_fp

    if belbio_secrets_fp:
        with open(belbio_secrets_fp, 'r') as f:
            secrets = yaml.load(f)
            config['secrets'] = copy.deepcopy(secrets)
            if 'source_files' in config:
                config['source_files']['secrets'] = belbio_secrets_fp
            else:
                config['source_files'] = {}
                config['source_files']['secrets'] = belbio_conf_fp

    config = get_versions(config)

    return config


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
    if not os.environ['READTHEDOCS']:
        config = load_configuration()
    else:
        log.info('READTHEDOCS environment')


# Ideas for providing hierarchical settings
# https://stackoverflow.com/questions/7204805/dictionaries-of-dictionaries-merge
# def dict_merge(a, b):
#     if not isinstance(b, dict):
#         return b
#     result = copy.deepcopy(a)
#     for k, v in b.iteritems():
#         if k in result and isinstance(result[k], dict):
#                 result[k] = dict_merge(result[k], v)
#         else:
#             result[k] = copy.deepcopy(v)
#     return result


