#!/usr/bin/env python3
import json
import mimetypes
import os
from argparse import ArgumentParser
from json import JSONDecodeError

from modules import logger, config

_attrs_str = 'attrs'
_configs_str = 'configs'
_encoding_str = 'encoding'
_ext_str = 'ext'
_result_str = 'result'
_message_str = 'message'
_error_str = 'error'
_error_code_str = 'error_code'
_prog_str = 'prog'


def extract(filename):
    print("Will try to extract file:", filename)
    ext, encoding = _guess_type(filename)
    if not ext and not encoding:
        print("Could not guess filetype. Cannot extract")
        return None
    config_result = _check_extension(ext, encoding)
    logger.d('ExtractorConfig:', config_result)
    if config_result[_error_str]:
        print("Cannot extract at this moment")
        return None

    result = config_result[_result_str]
    if not result[_result_str]:
        # Need to create file
        logger.d("create file for configurations")
        _create_configuration_file()

    prog_config = result[_prog_str]
    if not prog_config:
        # Add configuration for this extension
        logger.d('add config for this extension', ext, encoding)
        print('We are going to need to add a new config for', filename)
        prog_config = _configure_new_item(ext, encoding)
        if not prog_config:
            print('Could not extract for this type of file at this moment.')
            logger.d('User did not enter a new configuration')
            return

    logger.d('Found config:', prog_config)

    try:
        prog_command = prog_config[_prog_str]
    except KeyError:
        print('Could not extract')
        return None

    prog = _Program(prog_command)
    prog.execute(prog_config[_attrs_str], filename)


def _error_builder(error_code, error_message):
    return {_error_code_str: error_code, _message_str: error_message}


def _result_builder(result_status, prog_for_ext):
    return {_result_str: result_status, _prog_str: prog_for_ext}


def _response_builder(error_obj, result_obj, message):
    return {_error_str: error_obj, _result_str: result_obj, _message_str: message}


def _check_extension(ext, encoding):
    logger.d(f'check_extension, (ext, encoding) = ({ext},{encoding})')
    if not ext and not encoding:
        msg = 'Invalid extension and encoding'
        logger.d(msg)
        err = _error_builder(1, msg)
        return _response_builder(err, None, err[_message_str])

    if not os.path.isfile(config.EXTRACTOR_CONFIG_FILE):
        logger.d('No configuration file', config.EXTRACTOR_CONFIG_FILE)
        return _response_builder(None, _result_builder(False, None), 'No configuration file')

    with open(config.EXTRACTOR_CONFIG_FILE, 'r') as f:
        try:
            json_data = json.load(f)
        except JSONDecodeError:
            logger.d('Could not load configurations')
            err = _error_builder(2, 'File is not json')
            return _response_builder(err, None, err[_message_str])

    logger.d(f'file content: {json_data}')

    try:
        configs = json_data[_configs_str]
    except KeyError:
        msg = 'File with different json object than expected'
        logger.d(msg)
        err = _error_builder(3, msg)
        return _response_builder(err, None, msg)

    if not configs:
        msg = 'No configuration for extension' + ext
        return _response_builder(None, _result_builder(False, None), msg)

    for cfg in configs:
        ext_cfg = cfg[_ext_str]
        encoding_cfg = cfg[_encoding_str]
        if not ext:
            if encoding == encoding_cfg and not ext_cfg:
                return _response_builder(None, _result_builder(True, cfg), 'Found configuration')
            continue

        if ext == ext_cfg and encoding == encoding_cfg:
            return _response_builder(None, _result_builder(True, cfg), 'Found configuration')

    return _response_builder(None, _result_builder(True, None), 'Did not find a configuration')


def _create_configuration_file():
    data = {_configs_str: []}

    with open(config.EXTRACTOR_CONFIG_FILE, 'w') as outfile:
        json.dump(data, outfile, indent=2)


def _add_config(extension, encoding, prog, attrs):
    logger.d('add_config called:', extension, encoding, prog, attrs)

    with open(config.EXTRACTOR_CONFIG_FILE, 'r') as f:
        try:
            json_data = json.load(f)
        except JSONDecodeError:
            logger.d('add_config exception')
            print('Could not add a new configuration to your file')
            return None

    item = {
        _ext_str: extension,
        _encoding_str: encoding,
        _prog_str: prog,
        _attrs_str: attrs
    }

    json_data[_configs_str].append(item)

    with open(config.EXTRACTOR_CONFIG_FILE, 'w') as outfile:
        json.dump(json_data, outfile, indent=2)
    return item


def _configure_new_item(extension, encoding):
    prog = input('What\'s the program? (No options) ') or None
    opts = input('Options? ') or None
    return _add_config(extension, encoding, prog, opts) if prog else None


def _guess_type(filename):
    return mimetypes.guess_type(filename, False)


class _Program:

    def __init__(self, prog):
        self._prog = prog

    def execute(self, attrs, filename):
        if not filename:
            print("Could not get the name of your file")
            return None
        if not attrs:
            attrs = ''
        full_command = self._prog + ' ' + attrs + ' ' + filename
        logger.d('execute:', full_command)
        os.system(full_command)


def _test():
    parser = ArgumentParser()
    parser.add_argument('filename')
    args = parser.parse_args()
    extract(args.filename)


if __name__ == '__main__':
    _test()
