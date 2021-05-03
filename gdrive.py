#!/usr/bin/env python3

"""A script to interact with your Google Drive files using the terminal"""

from modules import logger
from modules.backports import asyncio_run_compat
from modules.command import CommandParser
from modules.util import current_python_version_supported, min_python_version_str, current_python_version_str


async def main():
    await CommandParser().execute_command()


if __name__ == '__main__':
    if not current_python_version_supported():
        print(f"Python version is {current_python_version_str()}, minimum is {min_python_version_str()}.")
        exit(-1)

    try:
        asyncio_run_compat(main())
    except KeyboardInterrupt as e:
        logger.d(e)
    except BaseException as e:
        logger.stacktrace()
        raise e
