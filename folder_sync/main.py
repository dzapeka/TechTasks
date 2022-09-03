import argparse
import filecmp
import logging
import os
import shutil
import sys
import time
from filecmp import dircmp
from logging.handlers import RotatingFileHandler

LOG = logging.getLogger("directory_syncer")
LOG.setLevel(logging.INFO)
formatter = logging.Formatter("%(message)s")
file_handler = RotatingFileHandler(
    filename="directory_syncer.log",
    maxBytes=50 * 1024 * 1024,
    backupCount=2
)
file_handler.setFormatter(formatter)
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
LOG.addHandler(file_handler)
LOG.addHandler(console_handler)


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--source-dir",
                        required=True,
                        help="Source directory",
                        type=str)
    parser.add_argument("-d", "--destination-dir",
                        required=True,
                        help="Replica directory",
                        type=str)
    parser.add_argument("-i", "--interval",
                        required=True,
                        help="Synchronization interval (in seconds)",
                        type=int)
    return parser.parse_args()


def sync_folders(src_dir, dst_dir):
    dcmp = dircmp(src_dir, dst_dir)
    filecmp.clear_cache()
    _, mismatch, _ = filecmp.cmpfiles(src_dir,
                                      dst_dir,
                                      dcmp.common_files,
                                      shallow=False)
    if mismatch:
        for file_name in mismatch:
            src_file_path = os.path.join(src_dir, file_name)
            dst_file_path = os.path.join(dst_dir, file_name)
            LOG.info(f"UPDATE: '{src_file_path}' --> '{dst_file_path}'")
            shutil.copy2(src_file_path, dst_file_path)

    for file_entry in dcmp.right_only:
        full_path = os.path.join(dcmp.right, file_entry)
        try:
            LOG.info(f"REMOVE '{full_path}'")
            if os.path.isfile(full_path):
                os.remove(full_path)
            elif os.path.isdir(full_path):
                shutil.rmtree(full_path)
        except PermissionError:
            LOG.info(f"File '{full_path}' can not be deleted "
                     f"because it is being used by another proces")
        except Exception as e:
            LOG.exception(e)

    for file_entry in dcmp.left_only:
        src_file_path = os.path.join(src_dir, file_entry)
        dst_file_path = os.path.join(dst_dir, file_entry)

        LOG.info(f"COPY '{src_file_path}' --> {dst_file_path}")
        if os.path.isfile(src_file_path):
            shutil.copy2(src_file_path, dst_file_path)
        elif os.path.isdir(src_file_path):
            shutil.copytree(src_file_path, dst_file_path)

    for sub_dir in dcmp.subdirs:
        new_src_dir = os.path.join(src_dir, sub_dir)
        new_dst_dir = os.path.join(dst_dir, sub_dir)
        sync_folders(new_src_dir, new_dst_dir)


def main():
    args = get_args()
    src_dir = args.source_dir
    dst_dir = args.destination_dir
    interval = args.interval

    if not os.path.isdir(src_dir):
        sys.exit("Source directory does not exist.")
    if not os.path.isdir(dst_dir):
        try:
            os.makedirs(dst_dir)
        except Exception as e:
            sys.exit(f"Destination directory can not be created: {dst_dir}")

    while True:
        sync_folders(src_dir, dst_dir)
        time.sleep(interval)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)

