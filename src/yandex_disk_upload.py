import os
import sys


# https://stackoverflow.com/questions/13909900/progress-of-python-requests-post
class upload_in_chunks(object):
    def __init__(self, filename, callback, chunksize=1 << 13):
        self.filename = filename
        self.chunksize = chunksize
        self.callback = callback
        self.totalsize = os.path.getsize(filename)
        self.readsofar = 0

    def __iter__(self):
        with open(self.filename, 'rb') as file:
            while True:
                data = file.read(self.chunksize)
                if not data:
                    sys.stderr.write("\n")
                    break
                self.readsofar += len(data)

                progress = self.readsofar / self.totalsize
                self.callback(progress)

                yield data

    def __len__(self):
        return self.totalsize


class IterableToFileAdapter:
    def __init__(self, iterable):
        self.iterator = iter(iterable)
        self.length = len(iterable)

    def read(self, size=-1):  # TBD: add buffer for `len(data) > size` case
        # print('read!')
        return next(self.iterator, b'')

    def tell(self) -> int:
        return 0

    def seek(self, *args):
        pass

    def __len__(self):
        return self.length


def prepare_file_adapter(local_path: str, callback):
    it = upload_in_chunks(local_path, callback, 100000)
    return IterableToFileAdapter(it)
