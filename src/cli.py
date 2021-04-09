import argparse
import os
import time
from typing import Optional, List, Any, Dict, Set

from yadisk.exceptions import PathNotFoundError

from src.disk_wrapper import YandexDiskUploaderAbstract, YandexDiskWrapper, YandexDiskUploaderOverwrite, \
    YandexDiskUploaderSkipExisting
from src.utils import get_file_size


class GlobalStateHolder:
    is_finish = False
    files_to_upload: List[str] = []
    uploaded = 0
    files_to_upload_len = 0

    files_to_rename: Dict[str, str] = dict()
    exists_same: Set[str] = set()

    uploader: Optional[YandexDiskUploaderAbstract] = None
    disk_wrapper: Optional[YandexDiskWrapper] = None

    source_dir = 'upload'
    destination_dir = 'from_python'


def get_sys_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='YandexDisk Uploader',
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('token',
                        metavar='Token',
                        type=str,
                        help='YandexDisk OAuth Token')
    parser.add_argument('destination_dir',
                        nargs='?',
                        default='from_python',
                        metavar='DestDir',
                        type=str,
                        help='Destination folder')
    parser.add_argument('source_dir',
                        nargs='?',
                        default='upload',
                        metavar='SourceDir',
                        type=str,
                        help='Source folder')

    parser.add_argument('--force',
                        nargs='?',
                        dest='force',
                        const=True,
                        default=False,
                        type=bool,
                        help='No user interactions')
    parser.add_argument('--no-collision',
                        nargs='?',
                        dest='no_collision',
                        const=True,
                        default=False,
                        type=bool,
                        help='Throw an error, if at least one of files already exists in YandexDisk')
    parser.add_argument('--skip-existing',
                        nargs='?',
                        dest='uploader_cls',
                        const=YandexDiskUploaderSkipExisting,
                        default=YandexDiskUploaderOverwrite,
                        type=bool,
                        help='Skip existing on yandex disk files')

    args: argparse.Namespace = parser.parse_args()

    return args


def get_files_to_upload() -> List[str]:
    source_dir = GlobalStateHolder.source_dir

    all_files = []
    for root, dirs, files in os.walk(source_dir, followlinks=True):
        root_from_source = root[len(source_dir) + 1:]
        all_files.extend([os.path.join(root_from_source, filename) for filename in files])

    return all_files


def initialize_wrapper(token: str):
    wrapper = YandexDiskWrapper(token=token)

    if wrapper.yadisk.check_token():
        print('Token is valid, OK')
    else:
        raise RuntimeError('Token is invalid')

    return wrapper


def print_progress(percent):
    """
    :deprecated
    :param percent:
    :return:
    """
    progress_bar_amount = 20
    progress_bar_fill: int = round(percent / 100 * progress_bar_amount)
    progress_bar = f'[{"=" * progress_bar_fill}{" " * (progress_bar_amount - progress_bar_fill)}] {percent * 100:02}%'

    print(f'Files: {GlobalStateHolder.uploaded: <3} / {GlobalStateHolder.files_to_upload_len: <3}', progress_bar)
    time.sleep(0.6)


def get_progress():
    while not GlobalStateHolder.is_finish:
        progress_bar = f'Wait...'
        if GlobalStateHolder.uploader:
            percent = GlobalStateHolder.uploader.get_progress()
            progress_bar_amount = 40
            progress_bar_fill: int = round(percent * progress_bar_amount)
            progress_bar = f'[{"=" * progress_bar_fill}{" " * (progress_bar_amount - progress_bar_fill)}] ' \
                           f'{percent * 100:02.2f}%'

        print(f'Files: {GlobalStateHolder.uploaded: <3} / {GlobalStateHolder.files_to_upload_len: <3}', progress_bar)
        time.sleep(1.5)


def upload_file(filename: str, uploader_cls):
    wrapper = GlobalStateHolder.disk_wrapper
    source_dir = GlobalStateHolder.source_dir
    destination_dir = GlobalStateHolder.destination_dir

    wrapper.mkdir_if_not_exists(destination_dir)
    source = f'{source_dir}/{filename}'
    origin_destination = f'{destination_dir}/{filename}'
    destination = origin_destination

    # File sizes equals => no changes
    if source in GlobalStateHolder.exists_same:
        print(f'File "{source}" already exists wil the same size. Skipped')
        return

    if destination.endswith(('.zip', '.tar', '.xz', '.rar', '.gz')):
        GlobalStateHolder.files_to_rename[destination + '.txt'] = destination
        destination += '.txt'
        print(f'File "{source}" will be uploaded to "{destination}" and renamed in next step')

    GlobalStateHolder.uploader = uploader_cls(wrapper,
                                              source,
                                              destination)

    GlobalStateHolder.uploader.upload()


def upload_all_files(uploader_cls):
    for file in GlobalStateHolder.files_to_upload:
        print(f'Uploading: {file}')
        upload_file(file, uploader_cls)

        GlobalStateHolder.uploaded += 1
        print(f'Uploaded:  {file}')

    GlobalStateHolder.is_finish = True


def compare_files_with_destination() -> List[Dict[str, Any]]:
    collisions: List[Dict[str, Any]] = []
    for file in GlobalStateHolder.files_to_upload:
        source_file = f'{GlobalStateHolder.source_dir}/{file}'
        destination_file = f'{GlobalStateHolder.destination_dir}/{file}'

        try:
            size = GlobalStateHolder.disk_wrapper.get_size(destination_file)
        except PathNotFoundError:
            continue

        source_size = get_file_size(source_file)
        collisions.append(dict(source_file=source_file,
                               destination_file=destination_file,
                               source_size=source_size,
                               destination_size=size, ))
        if source_size == size:
            # Do not upload files with the same size
            GlobalStateHolder.exists_same.add(source_file)

    if collisions:
        print('\nConflict files:')
        print(f'{"Source": ^70} | {"Size": ^16} || {"Destination": ^70} | {"Size": ^16}')
        print(f'{"-" * 70} | {"-" * 16} || {"-" * 70} | {"-" * 16}')

        for file in collisions:
            print(f'{file["source_file"]: <70} | '
                  f'{file["source_size"]: <16} || '
                  f'{file["destination_file"]: <70} | '
                  f'{file["destination_size"]: <16}')

    return collisions


def rename_all_files():
    for source in GlobalStateHolder.files_to_rename:
        destination = GlobalStateHolder.files_to_rename[source]
        GlobalStateHolder.disk_wrapper.yadisk.move(source,
                                                   destination)
