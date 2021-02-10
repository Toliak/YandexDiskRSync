import argparse
import time
from os import listdir
from os.path import isfile, join
from typing import Optional, List, Any, Dict

from yadisk.exceptions import PathNotFoundError

from src.disk_wrapper import YandexDiskUploaderAbstract, YandexDiskWrapper, YandexDiskUploaderOverwrite
from src.utils import get_file_size


class GlobalStateHolder:
    is_finish = False
    files_to_upload: List[str] = []
    uploaded = 0
    files_to_upload_len = 0

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

    args: argparse.Namespace = parser.parse_args()

    return args


def get_files_to_upload():
    source_dir = GlobalStateHolder.source_dir
    return [f
            for f in listdir(source_dir)
            if isfile(join(source_dir, f))]


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


def upload_file(filename: str):
    wrapper = GlobalStateHolder.disk_wrapper
    source_dir = GlobalStateHolder.source_dir
    destination_dir = GlobalStateHolder.destination_dir

    wrapper.mkdir_if_not_exists(destination_dir)
    GlobalStateHolder.uploader = YandexDiskUploaderOverwrite(wrapper,
                                                             f'{source_dir}/{filename}',
                                                             f'{destination_dir}/{filename}')

    GlobalStateHolder.uploader.upload()


def upload_all_files():
    for file in GlobalStateHolder.files_to_upload:
        print(f'Uploading: {file}')
        upload_file(file)

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

        collisions.append(dict(source_file=source_file,
                               destination_file=destination_file,
                               source_size=get_file_size(source_file),
                               destination_size=size, ))

    if collisions:
        print('\nConflict files:')
        print(f'{"Source": ^36} | {"Size": ^16} || {"Destination": ^36} | {"Size": ^16}')
        print(f'{"-" * 36} | {"-" * 16} || {"-" * 36} | {"-" * 16}')

        for file in collisions:
            print(f'{file["source_file"]: <36} | '
                  f'{file["source_size"]: <16} || '
                  f'{file["destination_file"]: <36} | '
                  f'{file["destination_size"]: <16}')

    return collisions
