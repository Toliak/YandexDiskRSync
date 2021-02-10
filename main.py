import sys
import threading
import time
from typing import Optional

import asyncio
import yadisk
import json

from yadisk.exceptions import PathNotFoundError
from yadisk.objects import DiskInfoObject

from src.disk_wrapper import YandexDiskWrapper, YandexDiskUploaderAbstract, YandexDiskUploaderOverwrite


#
# progress = threading.Thread(target=get_progress)
# upload = threading.Thread(target=main_upload)
#
# progress.start()
# upload.start()
#
# upload.join()

if __name__ == '__main__':
    print(sys.argv)