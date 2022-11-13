import argparse
import dataclasses
import enum
import os
from pathlib import Path
from typing import List, Callable, Dict, Optional

from yandex_disk_rsync.config import get_available_config_path, deserialize_yaml
from yandex_disk_rsync.data import YdInfo, \
    yd_listdir, \
    local_listdir, \
    FileBriefData, \
    yd_mkdir_recursive
from yandex_disk_rsync.log import logger
from yandex_disk_rsync.utils import runtime_path, ask_to_continue, mkdir_p_from_file
from yandex_disk_rsync import ydcmd


class ArgsTarget(enum.Enum):
    Disk = 'disk'
    Local = 'local'


@dataclasses.dataclass
class Args:
    config: Optional[Path]
    local_path: Path
    yd_path: Path
    target: ArgsTarget
    delete: bool

    def __init__(self, args):
        self.config = runtime_path() / args.config if args.config else None
        self.local_path = runtime_path() / args.local_path
        self.yd_path = runtime_path() / args.yd_path
        self.target = ArgsTarget(args.target)
        self.delete = args.delete

    def __str__(self):
        return f'''Config path : {str(self.config)}
        Local path  : {str(self.local_path)}
        Disk path   : {self.yd_path}
        Target      : {self.target.value}
        Can delete  : {self.delete}'''


def __arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--config',
        '-c',
        type=str,
        required=False,
        dest='config',
    )
    parser.add_argument(
        '--local-path',
        '-l',
        type=str,
        required=True,
        dest='local_path',
    )
    parser.add_argument(
        '--yd-path',
        '-d',
        type=str,
        required=True,
        dest='yd_path',
    )
    parser.add_argument(
        '--target',
        '-t',
        help='Target (editable)',
        type=str,
        required=False,
        choices=['disk', 'local'],
        default='local',
        dest='target',
    )
    parser.add_argument(
        '--delete',
        help='Can delete files',
        action='store_true',
        default=False,
        required=False,
        dest='delete',
    )
    return parser


class SyncType(enum.Enum):
    Add = 'Add',
    Change = 'Change',
    Delete = 'Delete'

    def as_one_char(self) -> str:
        return {
            SyncType.Add: '+',
            SyncType.Change: '*',
            SyncType.Delete: '-',
        }[self]


@dataclasses.dataclass
class SyncData:
    type: SyncType
    relative_path: str


def print_sync_data_list(data: List[SyncData], printer: Callable) -> None:
    for item in data:
        printer(f'[ {item.type.as_one_char()} ] {item.relative_path}')


def compare_before_sync(
        data_original: Dict[str, FileBriefData],
        data_target: Dict[str, FileBriefData],
        can_add: bool = False,
        can_change: bool = False,
        can_delete: bool = False,
) -> List[SyncData]:
    result: List[SyncData] = []

    for key, item in data_original.items():
        if can_add and key not in data_target:
            result += [
                SyncData(
                    type=SyncType.Add,
                    relative_path=item.path,
                )
            ]
            continue

        if can_change and data_target[key].md5 != data_original[key].md5:
            result += [
                SyncData(
                    type=SyncType.Change,
                    relative_path=item.path,
                )
            ]
            continue

    if can_delete:
        for key, item in data_target.items():
            if key in data_original:
                continue

            result += [
                SyncData(
                    type=SyncType.Delete,
                    relative_path=item.path,
                )
            ]

    return result


def apply_sync(
        options,
        local_sync_list: List[SyncData],
        remote_sync_list: List[SyncData],
        local_root_path: Path,
        remote_root_path: str,
):
    local_root_path = local_root_path.resolve()

    # Download to the local storage
    for data in local_sync_list:
        if data.type in {SyncType.Add, SyncType.Change}:
            disk_url = f'{remote_root_path}/{data.relative_path}'
            local_path = local_root_path / data.relative_path
            local_path.parent.mkdir(parents=True, exist_ok=True)

            logger.info(f"Copy from {disk_url} to {local_path}")
            ydcmd.yd_get(
                options,
                disk_url,
                str(local_path),
            )
            continue

        if data.type == SyncType.Delete:
            local_path = local_root_path / data.relative_path
            logger.warning(f"Removing {local_path}")

            ask_to_continue()
            local_path.unlink()
            continue

        logger.error(f"Unknown SyncData type: {data.type}")

    # Download into the disk
    for data in remote_sync_list:
        if data.type in {SyncType.Add, SyncType.Change}:
            disk_url = f'{remote_root_path}/{data.relative_path}'
            local_path = local_root_path / data.relative_path

            disk_url_path = Path(disk_url)
            if len(disk_url_path.parents) - 1 > 0:
                yd_mkdir_recursive(options, disk_url_path.parent)

            logger.info(f"Copy from {local_path} to disk:{disk_url}")
            ydcmd.yd_put(
                options,
                str(local_path),
                disk_url
            )
            continue

        if data.type == SyncType.Delete:
            disk_url = f'{remote_root_path}/{data.relative_path}'
            logger.warning(f"Removing disk:{disk_url}")

            ask_to_continue()
            ydcmd.yd_delete(options, disk_url)
            continue

        logger.error(f"Unknown SyncData type: {data.type}")


def cli_main():
    parser = __arg_parser()
    args = Args(parser.parse_args())
    return main(args)


def main(args: Args):
    logger.info("Arguments:")
    logger.info(args)

    options = deserialize_yaml(get_available_config_path(args.config))
    if not options.token:
        logger.warning(f'No token provided')

    info = YdInfo.deserialize(ydcmd.yd_info(options))
    logger.info("YaDisk info:")
    logger.info(info)

    if not args.local_path.exists():
        os.mkdir(args.local_path)

    if not args.local_path.is_dir():
        raise RuntimeError(f"{args.local_path} is not a directory")

    # collect local hashsums
    local_stats = {
        entry.path: entry
        for entry in local_listdir(options, args.local_path)
    }
    logger.info(f"Collected {len(local_stats)} local files")

    # collect remote hashsums
    disk_root_path = args.yd_path.as_posix()
    remote_stats = {
        entry.path: entry
        for entry in yd_listdir(options, disk_root_path)
    }
    logger.info(f"Collected {len(remote_stats)} remote files")

    # compare
    can_change_local = args.target == ArgsTarget.Local
    can_change_disk = args.target == ArgsTarget.Disk
    not_in_local = compare_before_sync(
        remote_stats,
        local_stats,
        can_add=can_change_local,
        can_change=can_change_local,
        can_delete=can_change_local and args.delete
    )
    not_in_remote = compare_before_sync(
        local_stats,
        remote_stats,
        can_add=can_change_disk,
        can_change=can_change_disk,
        can_delete=can_change_disk and args.delete
    )

    logger.info("=========   Not in local    =========")
    print_sync_data_list(not_in_local, logger.info)

    logger.info("=========   Not in remote   =========")
    print_sync_data_list(not_in_remote, logger.info)

    logger.info("-------------------------------------")
    ask_to_continue()

    # Sync
    apply_sync(
        options,
        not_in_local,
        not_in_remote,
        args.local_path,
        disk_root_path
    )
