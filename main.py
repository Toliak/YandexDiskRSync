import os
import threading

from src.cli import get_sys_arguments, GlobalStateHolder, get_files_to_upload, initialize_wrapper, \
    compare_files_with_destination, get_progress, upload_all_files, rename_all_files


def uploading_threads(uploader_cls):
    progress = threading.Thread(target=get_progress)
    upload = threading.Thread(target=lambda: upload_all_files(uploader_cls))

    progress.start()
    upload.start()

    upload.join()
    progress.join()


if __name__ == '__main__':
    args = get_sys_arguments()
    GlobalStateHolder.source_dir = args.source_dir
    GlobalStateHolder.destination_dir = args.destination_dir

    files_to_upload = get_files_to_upload()
    GlobalStateHolder.files_to_upload = files_to_upload
    GlobalStateHolder.files_to_upload_len = len(files_to_upload)

    wrapper = initialize_wrapper(args.token)
    GlobalStateHolder.disk_wrapper = wrapper

    comparison = compare_files_with_destination()
    if comparison and args.no_collision:
        print('Cannot continue due to conflicts above')
        exit(1)
    elif not comparison:
        print('No conflict files, OK')

    print(f'\nAll files from "{os.path.abspath(GlobalStateHolder.source_dir)}" '
          f'will be uploaded to "{GlobalStateHolder.destination_dir}"')
    if not args.force:
        print('Press ENTER to continue:')
        input()

    uploading_threads(args.uploader_cls)
    print('Uploading complete')

    print('Renaming archives...')
    rename_all_files()
    print('Complete, OK')

    exit(0)
