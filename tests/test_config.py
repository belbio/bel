import bel.Config as Config


def test_config():

    config = Config.load_configuration()
    assert config['bel']['version'] >= '0.10.0'


def test_merge_config():

    config = Config.load_configuration()
    override_config = {'bel_api': {'servers': {'server_type': 'DEV2'}}}
    new_config = Config.merge_config(config, override_config=override_config)

    assert config['bel_api']['servers']['server_type'] != new_config['bel_api']['servers']['server_type']
