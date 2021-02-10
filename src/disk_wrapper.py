import abc
import enum

import yadisk
from yadisk.exceptions import PathNotFoundError
from yadisk.objects import ResourceObject

from src.utils import get_file_size


class YandexDiskUploaderAbstract(metaclass=abc.ABCMeta):
    # class ExistingResolve(enum.Enum):
    #     OVERWRITE = 'Overwrite'  # Overwrite file
    #     ERROR = 'Error'  # Throw an error
    #     COMPARE_HASH = 'CompareHash'  # Overwrite, if SHA256 does not match
    #     SKIP = 'Skip'  # Skip existing file

    def __init__(self,
                 wrapper: 'YandexDiskWrapper',
                 source_path,
                 dist_path, ):
        self.wrapper = wrapper
        self.yadisk = wrapper.yadisk

        self.source_path = source_path
        self.dist_path = dist_path

    @abc.abstractmethod
    def upload(self):
        pass

    def get_uploaded_size(self) -> int:
        return self.wrapper.get_size(self.dist_path)

    def get_progress(self) -> float:
        uploaded = self.get_uploaded_size()
        original = get_file_size(self.source_path)

        return uploaded / original


class YandexDiskUploaderOverwrite(YandexDiskUploaderAbstract):
    def upload(self):
        self.yadisk.upload(self.source_path, self.dist_path, overwrite=True)


class YandexDiskUploaderWithError(YandexDiskUploaderAbstract):
    def upload(self):
        self.yadisk.upload(self.source_path, self.dist_path)


class YandexDiskWrapper:
    def __init__(self, **kwargs):
        self.yadisk = yadisk.YaDisk(**kwargs)

    def mkdir_if_not_exists(self, path):
        try:
            self.yadisk.get_type(path)
        except PathNotFoundError:
            self.yadisk.mkdir(path)

    def get_hash(self, path) -> str:
        meta: ResourceObject = self.yadisk.get_meta(path)
        return meta['sha256']

    def get_size(self, path) -> int:
        meta: ResourceObject = self.yadisk.get_meta(path)
        return meta['size']
