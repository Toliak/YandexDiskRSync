# Yandex Disk RSync

**Yandex Disk RSync** is the app that provides minimalistic CLI interface 
for local and [Yandex Disk](https://disk.yandex.ru/) storage synchronization.

The application is the wrapper over [ydcmd](https://github.com/abbat/ydcmd)
project and uses its SDK.

# Requirements

- OS Windows / Linux / macOS
- Python 3.7 or above

# Installation

## Linux / macOS into global scope

```bash
# 1. Clone the repository into the temporary directory
cd /tmp
git clone https://github.com/Toliak/YandexDiskRSync

# 2. Install the application
cd YandexDiskRSync
python setup.py install

# 3. Add startup script
YDR_PATH=$( python -c "import yandex_disk_rsync; print(yandex_disk_rsync.__path__[0])" )
cat > /usr/local/bin/ydsync <<EOF
#! /bin/sh
exec python "$YDR_PATH" "\$@"
EOF
chmod 755 /usr/local/bin/ydsync

# 4. Test the app
ydsync -h
```

## Linux / macOS with local scope (+venv)

```bash
# 1. Clone the repository
cd /usr/share/
git clone https://github.com/Toliak/YandexDiskRSync
cd YandexDiskRSync

# 2. Initialize venv and install requirements
python -m venv venv
source ./venv/bin/activate
pip install -r requirements.txt
python setup.py build
deactivate

# 3. Add startup script
cat > /usr/local/bin/ydsync <<EOF
#! /bin/sh
exec /usr/share/YandexDiskRSync/ydsync "\$@"
EOF
chmod 755 /usr/local/bin/ydsync

# 4. Test the app
ydsync -h
```

## Windows

In Progress

# Configuration

The application configuration stored in the YAML format.

Configuration file `yandex_disk_rsync.yaml` possible locations:
- The file in the current directory
(`$PWD/yandex_disk_rsync.yaml`)
- The hidden file (named `.yandex_disk_rsync.yaml`) in the current directory
- The hidden file in the user's home directory (`$HOME/.yandex_disk_rsync.yaml`)

Required configuration field is `token`.
Token creation guide described
[here](https://yandex.ru/dev/direct/doc/start/token.html#token__token_how_get).

```yaml
token: __YOUR_TOKEN_HERE__
verbose: true
debug: true
retries: 2
progress: true
```

Full configuration description located at the
[ydcmd README](https://github.com/abbat/ydcmd#%D0%BA%D0%BE%D0%BD%D1%84%D0%B8%D0%B3%D1%83%D1%80%D0%B0%D1%86%D0%B8%D1%8F).

Default configuration described in the [source code](https://github.com/abbat/ydcmd/blob/2716c42d0a02b9b88bc600b5ee0955ee71c66d27/ydcmd.py#L462-L494).

# Usage

```text
usage: yandex_disk_rsync [-h] [--config CONFIG] --local-path LOCAL_PATH
                         --yd-path YD_PATH [--target {disk,local}] [--delete]

optional arguments:
  -h, --help            show this help message and exit
  --config CONFIG, -c CONFIG
  --local-path LOCAL_PATH, -l LOCAL_PATH
  --yd-path YD_PATH, -d YD_PATH
  --target {disk,local}, -t {disk,local}
                        Target (editable)
  --delete              Can delete files
```

Target option specifies the target location of data flow: local or disk storage.
If the local is chosen, the files synchronized from disk into local.

| Case                   | Target is local      | Target is disk      |
|------------------------|----------------------|---------------------|
| No file in local       | Download from disk   | Delete`*` from disk |
| No file in disk        | Delete`*` from local | Upload to disk      |
| File checksum mismatch | Download from disk   | Upload to disk      |
| Same file              | No changes           | No changes          |

`*` works only if `delete` argument has been passed.

After preparing changes summary,
the app will print them and ask a user for confirmation.

```text
2022-11-13 13:17:29,406 - YandexDiskRSync - INFO - Collected 31 remote files (__init__.py:258)
2022-11-13 13:17:29,407 - YandexDiskRSync - INFO - =========   Not in local    ========= (__init__.py:278)
2022-11-13 13:17:29,407 - YandexDiskRSync - INFO - =========   Not in remote   ========= (__init__.py:281)
2022-11-13 13:17:29,407 - YandexDiskRSync - INFO - [ + ] new_dir/test_file (__init__.py:112)
2022-11-13 13:17:29,407 - YandexDiskRSync - INFO - ------------------------------------- (__init__.py:284)
Continue? [y/n]
```

# Known issues

## CA file

Windows users may be concerned with the HTTPS CA problem.
The solution is:
1. Download [GlobalSign CA certificate](http://secure.globalsign.com/cacert/gsrsaovsslca2018.crt)
2. Specify `ca-file` with path to the certificate in the configuration file
