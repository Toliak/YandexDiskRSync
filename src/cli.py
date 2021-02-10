import math
import time
from os import listdir
from os.path import isfile, join
from typing import Optional, List

from src.disk_wrapper import YandexDiskUploaderAbstract, YandexDiskWrapper, YandexDiskUploaderOverwrite


class GlobalStateHolder:
    is_finish = False
    files_to_upload: List[str] = []
    uploaded = 0
    files_to_upload_len = 0
    uploader: Optional[YandexDiskUploaderAbstract] = None
    disk_wrapper: Optional[YandexDiskWrapper] = None


def get_progress():
    while not GlobalStateHolder.is_finish:
        progress_bar = f'Wait...'
        if GlobalStateHolder.uploader:
            percent = GlobalStateHolder.uploader.get_progress()
            progress_bar_amount = 10
            progress_bar_fill: int = round(percent * progress_bar_amount)
            progress_bar = f'[{"=" * progress_bar_fill}{" " * (progress_bar_amount - progress_bar_fill)}] {percent:02}%'

        print(f'Files: {GlobalStateHolder.uploader: 3} / {GlobalStateHolder.files_to_upload_len: 3}', progress_bar)
        time.sleep(0.6)


def get_files_to_upload():
    return [f for f in listdir('upload') if isfile(join('upload', f))]


def initialize_wrapper(token: str):
    wrapper = YandexDiskWrapper(token=token)
    GlobalStateHolder.disk_wrapper = wrapper

    if wrapper.yadisk.check_token():
        print('Token is valid, OK')
    else:
        raise RuntimeError('Token is invalid')


def upload_file(filename: str):
    wrapper = GlobalStateHolder.disk_wrapper
    wrapper.mkdir_if_not_exists('upload_from_python')
    GlobalStateHolder.uploader = YandexDiskUploaderOverwrite(wrapper,
                                                             'upload/GPSS.msi',
                                                             'upload_from_python/GPSS.msi')

    GlobalStateHolder.uploader.upload()
