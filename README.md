# YandexDisk Uploader

Uploads all files from source directory to destination directory. Also shows files conflicts and requires to confirm uploading.

## Run with docker

How to get Yandex Disk OAuth token: [Link](https://oauth.yandex.ru/authorize?response_type=token&client_id=d44df5a42807427b85868c00845cccee)

(Do not share the token)

```shell
export YTOKEN=Your_yandex_disk_oauth_token
docker run -it --rm -v $PWD/upload:/uploader/upload/:ro uploader $YTOKEN
```

## Help

Help command

```shell
docker run -it --rm uploader -h
```
