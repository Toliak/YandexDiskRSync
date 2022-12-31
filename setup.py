#!/usr/bin/env python
import os.path
import shutil
import urllib.request
import setuptools

PROJECT_DIR_NAME = 'yandex_disk_rsync'


def __project_directory():
    """
    :rtype: str
    """
    return os.path.join(os.path.dirname(__file__), PROJECT_DIR_NAME)


def __pre_install():
    ydcmd_host = 'raw.githubusercontent.com'
    slug = 'abbat/ydcmd'
    file = 'ydcmd.py'
    ydcmd_commit_hash = '96e5700e3d8adf143d51fa6e7e40f88da890078e'

    ydcmd_url = 'https://%s/%s/%s/%s' % (
        ydcmd_host,
        slug,
        ydcmd_commit_hash,
        file,
    )

    with open(
            os.path.join(__project_directory(), 'ydcmd.py'),
            'wb',
    ) as py_file, \
            urllib.request.urlopen(ydcmd_url) as response:
        fp = response.fp
        shutil.copyfileobj(fp, py_file)


def __get_requirements():
    """
    :rtype:
    """

    with open(
            os.path.join(os.path.dirname(__file__), 'requirements.txt'),
            'rt',
            encoding='UTF-8',
            newline='\n'
    ) as file:
        return [
            s.strip()
            for s in file.read().split('\n')
            if s.strip()
        ]


__pre_install()

setuptools.setup(
    name='YandexDisk RSync',
    version='0.1',
    description='YDCMD wrapper with some misc improvements',
    author='Anatolii Titov',
    author_email='a@toliak.ru',
    url='https://github.com/Toliak/YandexDiskRSync',
    packages=[PROJECT_DIR_NAME],
    install_requires=__get_requirements(),
)
