import datetime as dt
import logging
import os
import re
import shutil
import subprocess
import sys

from src import __name__ as nm
from src import __version__ as vrs

ROOT_DIR = os.path.dirname(__file__)


def last_release_version() -> str:
    release_dir = os.path.join(ROOT_DIR, 'release')
    release_files = [f for f in os.listdir(release_dir) if os.path.isfile(os.path.join(release_dir, f))]

    if len(release_files) == 0:
        return '1.0.0'
    else:
        last_release_file = max(release_files, key=lambda f: os.path.getmtime(os.path.join(release_dir, f)))

        pattern = nm + r'-(\d{1,3}(?:\.\d{1,3}){0,2})\.tar\.gz'
        match = re.search(pattern, last_release_file)

        if match:
            return match.group(1)
        else:
            err_msg = f"file '{last_release_file}' does not match the expected regex"
            logging.critical(err_msg)
            raise RuntimeError(err_msg)


def verify_release() -> bool:
    curr_version = vrs
    last_version = last_release_version()

    logging.info(f'Old version: {last_version}')
    logging.info(f'New version: {curr_version}')
    if last_version != curr_version:
        return True
    else:
        err_msg = 'No release to build, build canceled'
        logging.critical(err_msg)
        raise SystemExit(err_msg)


def update_requirements():
    cmd_txt = f'pipreqs --force --savepath {ROOT_DIR}/requirements.txt {ROOT_DIR}/src'
    result = subprocess.run(cmd_txt, shell=True, capture_output=False, text=True)

    cmd_txt = 'git diff --name-only'
    result = subprocess.run(cmd_txt, shell=True, capture_output=True, text=True)

    if result.returncode != 0:
        err_msg = f"command '{cmd_txt}' failed, build canceled"
        logging.critical(err_msg)
        raise RuntimeError(err_msg)
    else:
        if 'requirements.txt' in result.stdout.strip():
            _ = input('requirements.txt has changes that need to be committed before creating a new release, press any key to exit')
            logging.critical('Uncommited requirements.txt update, build canceled')
            raise SystemExit


def main():
    log_path = os.path.join(ROOT_DIR, 'logs')
    if not os.path.isdir(log_path):
        os.mkdir(log_path)

    dte = dt.datetime.now().strftime('%Y%m%d%H%M%S')
    log_name = f'BUILD_{nm}_{dte}.log'
    log_file = os.path.join(log_path, log_name)
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s\t%(funcName)s\t%(levelname)s\t%(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )

    logging.info('Build started')

    if verify_release():
        update_requirements()

        build_cmd = 'py setup.py sdist'
        result = subprocess.run(build_cmd, shell=True, capture_output=True, text=True)

        if result.returncode != 0:
            err_msg = f"command '{build_cmd}' failed, build canceled"
            logging.critical(err_msg)
            raise RuntimeError(err_msg)
        else:
            logging.info('Build successful, cleaning up...')
            shutil.rmtree(os.path.join(ROOT_DIR, 'automation.egg-info'))

            release_dir = os.path.join(ROOT_DIR, 'dist')
            new_release_files = [f for f in os.listdir(release_dir) if os.path.isfile(os.path.join(release_dir, f))]
            for f in new_release_files:
                shutil.copy(os.path.join(release_dir, f), os.path.join(ROOT_DIR, 'release'))

            shutil.rmtree(release_dir)

            logging.info('Build complete')


if __name__ == '__main__':
    main()
