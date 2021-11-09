import os
import yaml


def get_config():
    config_path = "%s/config/config.yaml" % os.path.dirname(__file__)
    with open(config_path, 'r', encoding='utf-8') as config:
        config = yaml.safe_load(config)
    return config
