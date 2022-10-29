from pathlib import Path

import pytest
import yaml

import yandex_disk_rsync.config as ydr_config

from yandex_disk_rsync.config import deserialize_yaml
from yandex_disk_rsync.utils import file_text_read


@pytest.fixture
def config_1_correct():
    return Path(__file__).parent / 'test_config_1_correct.yaml'


@pytest.fixture
def config_2_wrong_fields():
    return Path(__file__).parent / 'test_config_2_wrong_fields.yaml'


def test_deserialize_yaml_correct(config_1_correct):
    options = ydr_config.deserialize_yaml(config_1_correct)
    assert options.token == 'MY_TOKEN'

    unused = ydr_config._get_config_unused_fields(
        yaml.safe_load(file_text_read(config_1_correct)),
    )
    assert unused == []


def test_deserialize_yaml_has_unused_fields(config_2_wrong_fields):
    options = deserialize_yaml(config_2_wrong_fields)
    assert options.token == 'MY_TOKEN'

    unused = ydr_config._get_config_unused_fields(
        yaml.safe_load(file_text_read(config_2_wrong_fields)),
    )
    assert set(unused) == {'this_field_does_not_exists'}
