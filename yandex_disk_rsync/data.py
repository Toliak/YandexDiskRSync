import dataclasses
import datetime
import os
from pathlib import Path
from typing import Dict, Generator, List

from yandex_disk_rsync import ydcmd
from yandex_disk_rsync.log import logger
from yandex_disk_rsync.utils import human_readable_size, file_md5


@dataclasses.dataclass
class YdUser:
    country: str
    login: str
    display_name: str
    uid: str

    @classmethod
    def deserialize(cls, data: dict):
        return cls(
            country=data['country'],
            login=data['login'],
            display_name=data['display_name'],
            uid=data['uid'],
        )


@dataclasses.dataclass
class YdInfo:
    max_file_size: int
    paid_max_file_size: int
    total_space: int
    trash_size: int
    is_paid: bool
    used_space: int
    system_folders: Dict[str, str]
    user: YdUser
    unlimited_autoupload_enabled: bool
    revision: datetime

    @classmethod
    def deserialize(cls, data: dict):
        return cls(
            max_file_size=data['max_file_size'],
            paid_max_file_size=data['paid_max_file_size'],
            total_space=data['total_space'],
            trash_size=data['trash_size'],
            is_paid=data['is_paid'],
            used_space=data['used_space'],
            system_folders=data['system_folders'],
            user=YdUser.deserialize(data['user']),
            unlimited_autoupload_enabled=data['unlimited_autoupload_enabled'],
            revision=datetime.datetime.fromtimestamp(data['revision'] / 1000000),
        )

    def __str__(self):
        return f'''Max file size                 : {human_readable_size(self.max_file_size)}
Paid max file size            : {human_readable_size(self.paid_max_file_size)}
Total space                   : {human_readable_size(self.total_space)}
Trash size                    : {human_readable_size(self.trash_size)}
Is paid                       : {self.is_paid}
Used space                    : {human_readable_size(self.used_space)}
System folders amount         : {len(self.system_folders)}
User                          : {self.user.display_name}
Unlimited auto-upload enabled : {self.unlimited_autoupload_enabled}
Revision                      : {self.revision.isoformat()}'''


@dataclasses.dataclass
class FileBriefData:
    path: str
    md5: str


@dataclasses.dataclass
class YdFileBriefData(FileBriefData):
    direct_url: str


def yd_listdir(
        options,
        remote_path: str,
        relative_path: str = ''
) -> Generator[YdFileBriefData, None, None]:
    disk_url = f'disk:/{remote_path}/{relative_path}' \
        if relative_path \
        else f'disk:/{remote_path}'

    logger.debug(f"Processing {disk_url}")
    file_list = ydcmd.yd_list(options, disk_url)

    for key, item in file_list.items():
        new_relative_path = f'{relative_path}/{key}' if relative_path else key
        if item.type == 'file':
            # Did not use Path due to win/linux different delimiters
            yield YdFileBriefData(
                path=new_relative_path,
                md5=item.md5,
                direct_url=item.file,
            )
            continue

        if item.type == 'dir':
            for inner_item in yd_listdir(
                    options,
                    remote_path,
                    new_relative_path
            ):
                yield inner_item

            continue

        logger.error(f"Unknown item type: {item.type}")


# Relative path must be determined and hashable
def local_listdir(options, local_path: Path, relative_path: str = ''):
    complete_path = local_path / relative_path \
        if relative_path \
        else local_path

    for path in os.listdir(complete_path):
        new_complete_path = complete_path / str(path)
        new_relative_path = f'{relative_path}/{path}' if relative_path else path
        if os.path.isfile(new_complete_path):
            yield FileBriefData(
                path=new_relative_path,
                md5=file_md5(new_complete_path),
            )
            continue

        if os.path.isdir(new_complete_path):
            for inner_item in local_listdir(
                    options,
                    local_path,
                    new_relative_path
            ):
                yield inner_item

            continue

        logger.error(f"Unknown file type: {new_complete_path}")


def yd_exists(options, remote_path):
    """
    :type remote_path: Path | str
    """
    remote_path_str = Path(remote_path).as_posix()

    try:
        ydcmd.yd_list(options, remote_path_str)
    except ydcmd.ydError as _:
        return False
    else:
        return True


def yd_mkdir_recursive(options, remote_path):
    """
    :type remote_path: Path | str
    """
    to_create: List[str] = []
    to_check: List[Path] = [
        Path(remote_path),
        *list(Path(remote_path).parents)[:-1]
    ]

    for path in to_check:
        if yd_exists(options, path.as_posix()):
            break
        to_create.append(path.as_posix())

    logger.info(f"For '{remote_path}' {len(to_create)} "
                f"directories will be created")
    for path in to_create:
        logger.debug(f"- {path}")

    for path_str in reversed(to_create):
        ydcmd.yd_create(options, path_str)
