import hashlib
from pathlib import Path

from yandex_disk_rsync import ydcmd


def open_text_read(filename):
    return open(filename, 'rt', encoding='UTF-8', newline='\n')


def open_text_write(filename):
    return open(filename, 'wt', encoding='UTF-8', newline='\n')


def file_text_read(filename):
    with open_text_read(filename) as file:
        return file.read()


def project_path() -> Path:
    return Path(__file__).parent


def runtime_path() -> Path:
    return Path('.')


def human_readable_size(size: int) -> str:
    return ydcmd.yd_human(size)


def file_md5(fname):
    """
    https://stackoverflow.com/a/3431838/14142236

    :type fname: str | Path
    """
    buffer_size = 4096 * 4
    hash_md5 = hashlib.md5()
    with open(fname, "rb") as f:
        for chunk in iter(lambda: f.read(buffer_size), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def ask_to_continue() -> None:
    v = ''
    while v not in set('yn'):
        print("Continue? [y/n]")
        v = input()

    if v == 'n':
        raise RuntimeError("Aborted")


def mkdir_p_from_file(path):
    """
    :type path: Path | str
    """
    path = Path(path).resolve()
    while path.is_file():
        path = path.parent

    return path.mkdir(parents=True, exist_ok=True)
