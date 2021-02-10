import hashlib
import os


def get_local_hash(local_path: str) -> str:
    buffer_size = 65536
    sha256 = hashlib.sha256()

    with open(local_path, 'rb') as f:
        while True:
            data = f.read(buffer_size)
            if not data:
                break
            sha256.update(data)

    return sha256.hexdigest().lower()


def get_file_size(local_path: str) -> int:
    return os.path.getsize(local_path)
