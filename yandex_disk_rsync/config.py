import dataclasses
from typing import Optional

import yaml
import yandex_disk_rsync.ydcmd as ydcmd
from yandex_disk_rsync.log import logger
from yandex_disk_rsync.utils import open_text_read

import collections

from pathlib import Path


def _get_ydcmd_unused_fields(content):
    """
    :type content: dict
    :rtype: list[str]
    """
    default_keys = set(ydcmd.yd_default_config().keys())
    content_keys = set(content.keys())

    wrong_keys = content_keys.difference(default_keys.intersection(content_keys))
    return list(wrong_keys)


def _deserialize_ydcmd_dict(content):
    """
    :type content: dict
    :rtype: ydcmd.ydOptions
    """
    cfg = ydcmd.yd_default_config().copy()
    for key in content:
        cfg[key] = content[key]

    options = ydcmd.ydOptions(cfg)

    return options


@dataclasses.dataclass(init=False, eq=False)
class SyncConfig:
    local_path: Optional[Path]
    yd_path: Optional[Path]
    delete: bool

    def __init__(self, local_path, yd_path, delete):
        """
        YandexDiskRSync configuration

        :param local_path: Path on local PC
        :type local_path: str | Path | None
        :param yd_path: Path on remote YandexDisk
        :type yd_path: str | Path | None
        :param delete: Can delete files
        :type delete: bool | None
        """

        self.local_path = local_path
        self.yd_path = yd_path

        self.delete = delete if delete is not None else False

        if self.local_path:
            self.local_path = Path(self.local_path)
        if self.yd_path:
            self.yd_path = Path(self.yd_path)

    __KEY_LOCAL_PATH = 'local_path'
    __KEY_YD_PATH = 'yd_path'
    __KEY_DELETE = 'delete'

    __KEYS = {
        __KEY_LOCAL_PATH,
        __KEY_YD_PATH,
        __KEY_DELETE,
    }

    @classmethod
    def get_keys(cls):
        """
        :rtype: set[str]
        """
        return cls.__KEYS

    @classmethod
    def get_unused_keys(cls, data):
        """
        :type data: dict
        :rtype: list[str]
        """

        data_keys = set(data.keys())
        class_keys = cls.get_keys()
        return data_keys.difference(class_keys.intersection(data_keys))

    @classmethod
    def deserialize(cls, data):
        """
        Deserialize raw dicts and lists into the configuration

        :type data: dict
        :rtype: SyncConfig
        """
        data = collections.defaultdict(lambda: None, data)
        return cls(
            local_path=data[cls.__KEY_LOCAL_PATH],
            yd_path=data[cls.__KEY_YD_PATH],
            delete=data[cls.__KEY_DELETE],
        )


@dataclasses.dataclass(eq=False)
class Config:
    ydcmd: ydcmd.ydOptions
    sync: SyncConfig

    __KEY_YDCMD = 'ydcmd'
    __KEY_SYNC = 'sync'
    __KEYS = {__KEY_YDCMD, __KEY_SYNC}

    @classmethod
    def get_keys(cls):
        """
        :rtype: set[str]
        """
        return cls.__KEYS

    @classmethod
    def get_unused_keys(cls, data):
        """
        :type data: dict
        :rtype: list[str]
        """
        unused_keys = []

        data_keys = set(data.keys())
        class_keys = cls.get_keys()
        unused_keys.extend(
            data_keys.difference(class_keys.intersection(data_keys))
        )

        if cls.__KEY_SYNC in data:
            unused_keys.extend([
                f'{cls.__KEY_SYNC}.{field}'
                for field in SyncConfig.get_unused_keys(data[cls.__KEY_SYNC])
            ])

        if cls.__KEY_YDCMD in data:
            unused_keys.extend([
                f'{cls.__KEY_YDCMD}.{field}'
                for field in _get_ydcmd_unused_fields(data[cls.__KEY_YDCMD])
            ])

        return unused_keys

    @classmethod
    def deserialize(cls, data):
        """
        Deserialize raw dicts and lists into the configuration

        :type data: dict
        :rtype: Config
        """
        data = collections.defaultdict(lambda: dict(), data)

        return cls(
            ydcmd=_deserialize_ydcmd_dict(data[cls.__KEY_YDCMD]),
            sync=SyncConfig.deserialize(data[cls.__KEY_SYNC]),
        )


def deserialize_yaml(file_path):
    """
    :type file_path: Path | str
    :rtype: Config
    """
    with open_text_read(file_path) as file:
        dict_content = yaml.safe_load(file)

    for field in Config.get_unused_keys(dict_content):
        logger.warning(f'Field "{field}" in config is unused')

    return Config.deserialize(dict_content)


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
