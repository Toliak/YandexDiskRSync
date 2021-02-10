import abc

from yadisk import YaDisk
from yadisk.exceptions import PathNotFoundError
from yadisk.objects import ResourceObject

from src.utils import get_file_size
from src.yandex_disk_upload import prepare_file_adapter


class YandexDiskUploaderAbstract(metaclass=abc.ABCMeta):
    # class ExistingResolve(enum.Enum):
    #     OVERWRITE = 'Overwrite'  # Overwrite file
    #     ERROR = 'Error'  # Throw an error
    #     COMPARE_HASH = 'CompareHash'  # Overwrite, if SHA256 does not match
    #     SKIP = 'Skip'  # Skip existing file

    def __init__(self,
                 wrapper: 'YandexDiskWrapper',
                 source_path,
                 dist_path):
        self.wrapper = wrapper
        self.yadisk = wrapper.yadisk

        self.source_path = source_path
        self.dist_path = dist_path
        self.current_percent = 0

        self.percent_callback = lambda x: self.set_current_percent(x)

    def set_current_percent(self, value: float):
        self.current_percent = value

    @abc.abstractmethod
    def upload(self):
        pass

    def get_uploaded_size(self) -> int:
        return self.wrapper.get_size(self.dist_path)

    def get_progress(self) -> float:
        return self.current_percent


class YandexDiskUploaderOverwrite(YandexDiskUploaderAbstract):
    def upload(self):
        self.yadisk.upload(prepare_file_adapter(self.source_path, self.percent_callback),
                           self.dist_path,
                           overwrite=True)


class YandexDiskUploaderWithError(YandexDiskUploaderAbstract):
    def upload(self):
        self.yadisk.upload(prepare_file_adapter(self.source_path, self.percent_callback),
                           self.dist_path)


class YandexDiskWrapper:
    def __init__(self, **kwargs):
        self.yadisk = YaDisk(**kwargs)

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
