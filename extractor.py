#!/usr/bin/env python3

from argparse import ArgumentParser
import mimetypes
import os

DEBUG = False

class Program:
    _tar_type = 'application/x-tar'
    _gzip_type = 'gzip'
    _zip_type = 'application/zip'
    _7z_type = 'application/x-7z-compressed'

    _tar_ext = '.tar'
    _targz_ext = '.tar.gz'
    _gzip_ext = '.gz'
    _zip_ext = '.zip'
    _7z_ext = '.7z'

    _tar_prog = 'tar'
    _targz_prog = 'tar'
    _gzip_prog = 'guzip'
    _zip_prog = 'unzip'
    _7z_prog = '7z'
    
    _tar_attr = 'xvf'
    _targz_attr = 'xzvf'
    _gzip_attr = ''
    _zip_attr = ''
    _7z_attr = 'x'

    exts = {
            _tar_type: _tar_ext,
            _gzip_type: _gzip_ext,
            _zip_type: _zip_ext,
            _7z_type: _7z_ext,
    }

    progs = {
            _tar_ext: _tar_prog,
            _targz_ext: _targz_prog,
            _gzip_ext: _gzip_prog,
            _zip_ext: _zip_prog,
            _7z_ext: _7z_prog,
    }

    attrs = {
            _tar_ext: _tar_attr,
            _targz_ext: _targz_attr,
            _gzip_ext: _gzip_attr,
            _zip_ext: _zip_attr,
            _7z_ext: _7z_attr,
    }

    def get_full_command(self, prog, ext, filename):
        if not prog:
            print("Could not define which program we should use to extract your file");
            return None
        if not ext:
            print("Could not define the extension of your file");
            return None
        if not filename:
            print("Could not get the name of your file")
            return None
        return prog + ' ' + self.attrs[ext] + ' ' + filename

    def get_proper_ext(self, extension):
        if not extension:
            return None
        if len(extension) > 2:
            print("We don't support this extension.")
            return None
        if extension[0] is None:
            if extension[1] is None:
                print("We don't support this extension.")
                return None
            return self.exts[extension[1]]
        else:
            if extension[1] is None:
                return self.exts[extension[0]]
            _ext0 = self.exts[extension[0]]
            _ext1 = self.exts[extension[1]]
            appended_ext = _ext0 + _ext1
            return appended_ext

    def get_prog(self, _ext):
        if not _ext:
            print("Invalid extension")
            return None
        _prog = self.progs[_ext]
        if not _prog:
            print("We don't support this file type")
            return None
        return _prog

class Extractor:

    def get_prog(self, extensions):
        if not extensions:
            return None

    def build_command(self, program, filename):
        if not program:
            return None
        if not filename:
            return None

    def guess_type(self, filename):
        ext = mimetypes.guess_type(filename, False)
        if not ext:
            return None
        if DEBUG:
            print(ext)
        return ext

    def extract(self, filename):
        print("Will try to extract file:", filename)
        ext = self.guess_type(filename)
        if not ext:
            print("Could not guess filetype. Cannot extract")
            return None
        prog = Program()
        _ext = prog.get_proper_ext(ext)
        if not _ext:
            print("Cannot extract at this moment")
            return None

        _prog = prog.get_prog(_ext)

        _command = prog.get_full_command(_prog, _ext, filename)
        if DEBUG:
            print(_command)
        if not _command:
            return

        os.system(_command)

def main():
    parser = ArgumentParser()
    parser.add_argument("filename")
    args = parser.parse_args()
    Extractor().extract(args.filename)

if __name__ == '__main__':
    main()

