import bel_lang.Config as Config


def test_config():

    config = Config.load_configuration()
    assert config['bel_api']['servers']['api_url'] == 'https://api.bel.bio/v1'
    assert config['bel_lang']['version'] >= '0.5.0'


def test_merge_config():

    config = Config.load_configuration()
    override_config = {'bel_api': {'servers': {'server_type': 'DEV2'}}}
    new_config = Config.merge_config(config, override_config=override_config)

    assert config['bel_api']['servers']['server_type'] == 'DEV'
    assert new_config['bel_api']['servers']['server_type'] == 'DEV2'
