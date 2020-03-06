#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Usage:  import bel.Config as config

Get first belbio_conf.{yml|yaml} and belbio_secrets.{yml|yaml} files in:
    current dir or parent directories starting with immediate parent of current dir
    OR
    ~/.belbio_{conf|secrets}   (dotfiles in home directory)
"""

# Standard Library
import collections
import copy
import functools
import logging
import os
import re
from typing import Any, Mapping, MutableMapping

# Third Party Imports
import yaml

log = logging.getLogger(__name__)


def get_belbio_conf_files():
    """Get belbio configuration from files
    """

    home = os.path.expanduser("~")
    cwd = os.getcwd()

    belbio_conf_fp, belbio_secrets_fp = "", ""

    env_conf_dir = os.getenv("BELBIO_CONF", "").rstrip("/")

    conf_paths = [
        f"{cwd}/belbio_conf.yaml",
        f"{cwd}/belbio_conf.yml",
        f"{env_conf_dir}/belbio_conf.yaml",
        f"{env_conf_dir}/belbio_conf.yml",
        f"{home}/.belbio/conf",
    ]
    secret_paths = [
        f"{cwd}/belbio_secrets.yaml",
        f"{cwd}/belbio_secrets.yml",
        f"{env_conf_dir}/belbio_secrets.yaml",
        f"{env_conf_dir}/belbio_secrets.yml",
        f"{home}/.belbio/secrets",
    ]

    for fn in conf_paths:
        if os.path.exists(fn):
            belbio_conf_fp = fn
            break
    else:
        log.error(
            "No BELBio configuration file found - please add one (see http://bel.readthedocs.io/en/latest/configuration.html)"
        )

    for fn in secret_paths:
        if os.path.exists(fn):
            belbio_secrets_fp = fn
            break

    return (belbio_conf_fp, belbio_secrets_fp)


def load_configuration():
    """Load the configuration"""

    (belbio_conf_fp, belbio_secrets_fp) = get_belbio_conf_files()
    log.info(f"Using conf: {belbio_conf_fp} and secrets files: {belbio_secrets_fp} ")

    config = {}
    if belbio_conf_fp:
        with open(belbio_conf_fp, "r") as f:
            config = yaml.load(f, Loader=yaml.SafeLoader)
            config["source_files"] = {}
            config["source_files"]["conf"] = belbio_conf_fp

    if belbio_secrets_fp:
        with open(belbio_secrets_fp, "r") as f:
            secrets = yaml.load(f, Loader=yaml.SafeLoader)
            config["secrets"] = copy.deepcopy(secrets)
            if "source_files" in config:
                config["source_files"]["secrets"] = belbio_secrets_fp

    get_versions(config)

    # TODO - needs to be completed
    # add_environment_vars(config)

    return config


def get_versions(config) -> dict:
    """Get versions of bel modules and tools"""

    # Collect bel package version
    try:
        import bel.__version__

        config["bel"]["version"] = bel.__version__.__version__
    except KeyError:
        config["bel"] = {"version": bel.__version__.__version__}
    except ModuleNotFoundError:
        pass

    # Collect bel_resources version
    try:
        import tools.__version__

        config["bel_resources"]["version"] = tools.__version__.__version__
    except KeyError:
        config["bel_resources"] = {"version": tools.__version__.__version__}
    except ModuleNotFoundError:
        pass

    # Collect bel_api version
    try:
        import __version__

        if __version__.__name__ == "BELBIO API":
            config["bel_api"]["version"] = __version__.__version__
    except KeyError:
        if __version__.__name__ == "BELBIO API":
            config["bel_api"] = {"version": __version__.__version__}
    except ModuleNotFoundError:
        pass


# TODO - still needs to be completed
def add_environment_vars(config: MutableMapping[str, Any]):
    """Override config with environment variables

    Environment variables have to be prefixed with BELBIO_
    which will be stripped before splitting on '__' and lower-casing
    the environment variable name that is left into keys for the
    config dictionary.

    Example:
        BELBIO_BEL_API__SERVERS__API_URL=http://api.bel.bio
        1. BELBIO_BEL_API__SERVERS__API_URL ==> BEL_API__SERVERS__API_URL
        2. BEL_API__SERVERS__API_URL ==> bel_api__servers__api_url
        3. bel_api__servers__api_url ==> [bel_api, servers, api_url]
        4. [bel_api, servers, api_url] ==> config['bel_api']['servers']['api_url'] = http://api.bel.bio

    """

    # TODO need to redo config - can't add value to dictionary without recursively building up the dict
    #         check into config libraries again

    for e in os.environ:
        if re.match("BELBIO_", e):
            val = os.environ.get(e)
            if val:
                e.replace("BELBIO_", "")
                env_keys = e.lower().split("__")
                if len(env_keys) > 1:
                    joined = '"]["'.join(env_keys)
                    eval_config = f'config["{joined}"] = val'
                    try:
                        eval(eval_config)
                    except Exception as exc:
                        log.warn("Cannot process {e} into config")
                else:
                    config[env_keys[0]] = val


def merge_config(
    config: Mapping[str, Any],
    override_config: Mapping[str, Any] = None,
    override_config_fn: str = None,
) -> Mapping[str, Any]:
    """Override config with additional configuration in override_config or override_config_fn

    Used in script to merge CLI options with Config

    Args:
        config: original configuration
        override_config: new configuration to override/extend current config
        override_config_fn: new configuration filename as YAML file
    """

    if override_config_fn:
        with open(override_config_fn, "r") as f:
            override_config = yaml.load(f, Loader=yaml.SafeLoader)

    if not override_config:
        log.info("Missing override_config")

    return functools.reduce(rec_merge, (config, override_config))


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


def main():

    import json

    config = load_configuration()
    print("Config:\n", json.dumps(load_configuration(), indent=4))
    print("ns def", config["bel_resources"]["file_locations"]["namespaces_definition"])


if __name__ == "__main__":
    main()

else:
    # If building documents in readthedocs - provide empty config
    if os.getenv("READTHEDOCS", False):
        config = {}
        log.info("READTHEDOCS environment")
    else:
        config = load_configuration()


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
