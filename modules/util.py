import mimetypes
import os
import sys

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


def describe_files(*metadatas):
    """Print files metadata"""

    def describe():
        print("Name: %s" % metadata["name"])
        print("Owner: %s" % metadata["owners"][0]["displayName"])
        if 'size' in metadata:
            print("Size: %s" % to_human_readable(float(metadata["size"])))
        if 'modifiedByMeTime' in metadata:
            print("Modified by Me: %s" % metadata["modifiedByMeTime"])
        else:
            print("Modified: %s" % metadata["modifiedTime"])
        print("ID: %s\n" % metadata["id"])

    for metadata in metadatas:
        describe()


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
