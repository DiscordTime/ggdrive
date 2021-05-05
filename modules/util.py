import mimetypes
import os
import sys
from typing import Callable, Any

from modules import logger


def to_human_readable(*values, suffix='B'):
    """Converts bytes to a more human-readable metric"""

    def convert(value):
        for unit in ['', 'K', 'M', 'G', 'T']:
            if abs(value) < 1024.0:
                return "%3.1f%s%s" % (value, unit, suffix)
            value /= 1024.0
        return None

    return tuple(convert(value) for value in values)


def get_modification_time(file):
    return os.stat(file).st_mtime


def find_last_modified_file(*files):
    try:
        return sorted(files, key=get_modification_time)[-1]
    except BaseException as err:
        print('An error occurred while handling the wildcard files.')
        logger.d(err)
        return None


def guess_mimetype(filepath):
    if not filepath:
        return
    guessed_type, encoding = mimetypes.guess_type(filepath, True)
    if guessed_type is None:
        print("Wasn't able to guess mimetype")
        return
    return guessed_type


def files_descriptions(*metadata):
    """Returns formatted string representations of files metadata"""

    def description(m):
        by_me = 'modifiedByMeTime' in m
        modified_by = m['modifiedByMeTime' if by_me else 'modifiedTime']
        desc = [
            f"Name: {m['name']}",
            f"Owner: {m['owners'][0]['displayName']}",
            "Size: {0}".format(*to_human_readable(float(m['size']))) if 'size' in m else None,
            "Modified{0}: {1}".format(" by me" if by_me else "", modified_by),
            f"ID: {m['id']}"
        ]
        return [d for d in desc if d is not None]

    return [description(m) for m in metadata]


def print_files_descriptions(*descriptions, line_sep='\n', desc_sep='\n'):
    for desc in descriptions:
        for line in desc:
            print(line, end=line_sep)
        print(end=desc_sep)


def describe_files(*metadata, line_sep='\n', desc_sep='\n'):
    print_files_descriptions(*files_descriptions(*metadata), line_sep=line_sep, desc_sep=desc_sep)


def current_python_version():
    return sys.version_info.major, sys.version_info.minor


def current_python_version_str():
    return _tuple_str(current_python_version())


def current_python_version_supported():
    return current_python_version() >= python36()


def min_python_version():
    return python36()


def min_python_version_str():
    return _tuple_str(python36())


def _tuple_str(t):
    return '.'.join(map(str, t))


def python36():
    return 3, 6


def python37():
    return 3, 7


def python38():
    return 3, 8


def python39():
    return 3, 9


def current_is_python36():
    return python36() == current_python_version()


def create_dir(*paths):
    for path in paths:
        if not os.path.exists(path):
            logger.d(f"Dir does not exist. Creating if dir {path} exists")
            try:
                os.mkdir(path)
                logger.d(f"Created chunks temp dir {path}")
            except BaseException as e:
                logger.d(f"Error creating dir {path}", e)
                raise


def remove_dir(*paths):
    for path in paths:
        try:
            logger.d(f"Trying to remove dir {path}, if empty")
            os.rmdir(path)
        except BaseException as e:
            logger.d(f"Error removing dir", e)


def remove_file(*paths):
    for path in paths:
        try:
            logger.d(f"Trying to remove file {path}")
            os.remove(path)
        except FileNotFoundError as e:
            logger.d(f"File not found {path}", e)


def copy_file_contents(dest: str, *srcs: str):
    with open(dest, 'wb') as final_file:
        for src in srcs:
            with open(src, 'rb') as partial_file:
                logger.d(f"Writing '{partial_file.name}' into '{dest}'")
                final_file.write(partial_file.read())


def delete_lines(lines: int = 1):
    for _ in range(lines):
        print('\x1b[2K', end='\n')


def move_cursor_up(lines: int = 1):
    for _ in range(lines):
        print('\x1b[1A', end='\r')


def for_lines(lines: int = 1, *funcs: Callable[[int], Any]):
    for func in funcs:
        func(lines)
