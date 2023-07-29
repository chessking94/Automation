import os
import re
import shutil

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
            raise RuntimeError(f"file '{last_release_file}' does not match the expected regex")


def verify_release() -> bool:
    curr_version = vrs
    last_version = last_release_version()

    if curr_version != last_version:
        return True
    else:
        return False


def main():
    if not verify_release():
        raise SystemExit('no release to build')
    else:
        build_cmd = 'py setup.py sdist'
        os.system('cmd /C ' + build_cmd)

        shutil.rmtree(os.path.join(ROOT_DIR, 'automation.egg-info'))

        # move file from dist to release
        release_dir = os.path.join(ROOT_DIR, 'dist')
        new_release_files = [f for f in os.listdir(release_dir) if os.path.isfile(os.path.join(release_dir, f))]
        for f in new_release_files:
            shutil.copy(os.path.join(release_dir, f), os.path.join(ROOT_DIR, 'release'))

        shutil.rmtree(release_dir)


if __name__ == '__main__':
    main()
