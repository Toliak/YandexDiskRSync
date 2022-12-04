from pathlib import Path

import yaml

import yandex_disk_rsync.ydcmd as ydcmd
from yandex_disk_rsync.log import logger
from yandex_disk_rsync.utils import open_text_read


def _get_config_unused_fields(content):
    """
    :type content: dict
    :rtype: list[str]
    """
    default_keys = set(ydcmd.yd_default_config().keys())
    content_keys = set(content.keys())

    wrong_keys = content_keys.difference(default_keys.intersection(content_keys))
    return list(wrong_keys)


def _deserialize_dict(content):
    """
    :type content: dict
    :rtype: ydcmd.ydOptions
    """
    cfg = ydcmd.yd_default_config().copy()
    for key in content:
        cfg[key] = content[key]

    options = ydcmd.ydOptions(cfg)

    return options


def deserialize_yaml(file_path):
    """
    :type file_path: Path | str
    :rtype: ydcmd.ydOptions
    """
    with open_text_read(file_path) as file:
        dict_content = yaml.safe_load(file)

    options = _deserialize_dict(dict_content)
    for field in _get_config_unused_fields(dict_content):
        logger.warning(f'Field {field} in config is unused')

    return options


def default_config_paths():
    """
    :rtype: list[Path]
    """
    return [
        Path('./yandex_disk_rsync.yaml'),
        Path('./.yandex_disk_rsync.yaml'),
        Path('~/.yandex_disk_rsync.yaml'),
    ]


def get_available_config_path(args_path):
    """
    :type args_path: Path | None
    :rtype: Path
    """
    if args_path:
        args_path = args_path.resolve()
        if args_path.exists():
            logger.info(f'Using config "{args_path}"')
            return args_path
        else:
            logger.error(f'Specified config "{args_path}" does not exist')

    for cfg_path in default_config_paths():
        if cfg_path.exists():
            logger.info(f'Using config "{cfg_path}"')
            return cfg_path
        else:
            logger.debug(f'Config "{cfg_path}" does not exist')

    raise RuntimeError("Unable to find any config")
