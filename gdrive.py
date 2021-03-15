#!/usr/bin/env python3

"""A script to interact with your Google Drive files using the terminal"""

import os
import io
import pickle
import mimetypes
import threading
import time
from argparse import ArgumentParser
from os.path import expanduser, join
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError

class GoogleCredentials():
    """Handles the local Credentials file for the Google Drive API"""
    HOME = expanduser("~")
    GDRIVE_PATH = join(HOME, '.gdrive')
    CREDENTIALS_PATH = join(GDRIVE_PATH, 'credentials.json')
    TOKEN_PATH = join(GDRIVE_PATH, 'token.pickle')
    SCOPES = [
        'https://www.googleapis.com/auth/drive',
        'https://www.googleapis.com/auth/drive.metadata'
    ]

    def __init__(self):
        self.__creds = None

    def build(self):
        self.load_credentials()
        if not self.is_credentials_valid():
            self.prepare_credentials()
        return self.__creds

    def prepare_credentials(self):
        if self.__creds and self.is_credentials_outdated():
            self.__creds.refresh(Request())
        else:
            self.create_credentials()
        self.save_credentials()

    def load_credentials(self):
        self.__creds = None
        if os.path.exists(self.TOKEN_PATH):
            with open(self.TOKEN_PATH, 'rb') as token:
                self.__creds = pickle.load(token)

    def is_credentials_valid(self):
        return self.__creds is not None and self.__creds.valid

    def is_credentials_outdated(self):
        return self.__creds.expired and self.__creds.refresh_token

    def create_credentials(self):
        if os.path.exists(self.CREDENTIALS_PATH):
            flow = InstalledAppFlow.from_client_secrets_file(self.CREDENTIALS_PATH, self.SCOPES)
            self.__creds = flow.run_local_server(port=0)
        else:
            print('Credentials not found at %s' % self.CREDENTIALS_PATH)
            exit()

    def save_credentials(self):
        with open(self.TOKEN_PATH, 'wb') as token:
            pickle.dump(self.__creds, token)


class GoogleService():
    """Encapsulates Google Drive API, provides usability methods and keeps API-side configurations"""
    UPLOAD_CHUNK_SIZE = 1024 * 1024 * 128 # 128MB
    DOWNLOAD_CHUNK_SIZE = 1024 * 1024 * 128 # 128MB

    def __init__(self):
        creds = GoogleCredentials().build()
        self.__google = build('drive', 'v3', credentials=creds)

    def is_valid(self):
        return self.__google is not None

    def drive(self):
        # Google Drive resource is dynamically populated
        # pylint: disable=maybe-no-member
        return self.__google.files()

    def get_file_metadata(self, file_id):
        try:
            fields = 'id, name, size, modifiedTime, modifiedByMeTime, owners'
            return self.drive().get(fileId=file_id, fields=fields).execute()
        except HttpError:
            return None

    def search_filename(self, filename=None, page_size=1, page_token=''):
        query = ''
        if filename is not None:
            # Could also be name = '%s' for an exact search
            query = "name contains '%s'" % filename
        fields = ('nextPageToken, files/id, files/name, files/size, '
                'files/modifiedTime, files/modifiedByMeTime, files/owners')
        search = self.drive().list(
            q=query,
            orderBy='modifiedByMeTime desc',
            fields=fields,
            pageSize=page_size,
            pageToken=page_token
        ).execute()
        files_found = search.get('files', [])
        if files_found and page_size == 1:
            return files_found[0], None
        next_page = search.get('nextPageToken', None)
        return files_found, next_page

    def get_last_modified_file(self):
        file, _ = self.search_filename(None)
        return file

    def download(self, file_id, file_name):
        request = self.drive().get_media(fileId=file_id)
        file_handler = io.FileIO(file_name, 'wb')
        return MediaIoBaseDownload(file_handler, request, chunksize=self.DOWNLOAD_CHUNK_SIZE)

    def upload(self, filepath, mime_type):
        filename = filepath.split('/')[-1]
        file_metadata = {'name': filename}
        print('Uploading the file: %s' % filename)
        media = MediaFileUpload(
            filepath,
            mimetype=mime_type,
            resumable=True,
            chunksize=self.UPLOAD_CHUNK_SIZE
        )
        return self.drive().create(
            body=file_metadata,
            media_body=media,
            fields='id'
        )


class Command():
    """Commands handle their own argument parser and use GoogleService to execute operations"""
    TYPE = None
    HELP = None

    def __init__(self, args):
        self.args = args
        self.google = GoogleService()

    @staticmethod
    def add_to_subparser(subparsers):
        """Configures ArgParser for the command"""
        pass

    def execute(self):
        pass

    def is_service_started(self):
        return self.google.is_valid()

    def conclude_operation_while_logging(self, operation, title):
        logger = ProgressLogger(title)
        try:
            result = None
            while not result:
                status, result = operation.next_chunk()
                if status:
                    logger.send(status)
            logger.close()
            return result
        except Exception as err:
            print('An error happened while %s' % title)
            print(err)
            logger.close()


class Download(Command):
    TYPE = "download"
    HELP = "Download a file from Google Drive through ID or Filename. Use -l to download the last modified file."

    @staticmethod
    def add_to_subparser(subparsers):
        parser = subparsers.add_parser(
            Download.TYPE,
            help=Download.HELP
        )
        parser.set_defaults(command=Download)
        parser.add_argument(
            'file',
            metavar='FILE',
            nargs='*',
            help="Name or ID of the file to Download. If not specified, will try as ID then as Name."
        )
        name_or_id = parser.add_mutually_exclusive_group()
        name_or_id.add_argument(
            '--name',
            '-n',
            help='Will use FILE as a filename to search',
            action='store_true'
        )
        name_or_id.add_argument(
            '--id',
            '-i',
            help='Will use FILE as a file ID to download',
            action='store_true'
        )
        parser.add_argument(
            '--last',
            '-l',
            help="Downloads the last modified file",
            action='store_true'
        )

    def execute(self):
        if self.args.last:
            return self.download_last_uploaded_file()
        if not self.args.file:
            print('Please inform the ID or name of the file you want to download. Exiting...')
            return
        self.file = " ".join(self.args.file)
        if self.args.name:
            return self.download_filename()
        if self.args.id:
            return self.download_id()
        return self.try_download_id_then_name()

    def download_last_uploaded_file(self):
        last_file = self.google.get_last_modified_file()
        if not last_file:
            print("Could not find any file")
            return
        self.download_from_metadata(last_file)

    def download_filename(self):
        file_found, _ = self.google.search_filename(self.file)
        if not file_found:
            print("Could not find any file that contains '%s' on the name" % self.file)
            return
        return self.download_from_metadata(file_found)

    def download_id(self):
        file_found = self.google.get_file_metadata(self.file)
        if not file_found:
            print("Could not find file with '%s' as ID" % self.file)
            return
        return self.download_from_metadata(file_found)

    def try_download_id_then_name(self):
        file_id_found = self.google.get_file_metadata(self.file)
        if file_id_found:
            return self.download_from_metadata(file_id_found)
        self.download_filename()

    def download_from_metadata(self, metadata):
        if metadata is None:
            print('Could not find file to download')
            return
        file_name = metadata["name"] or "Unknown filename"
        Utils.describe_file(metadata)
        self.download(metadata["id"], file_name)

    def download(self, file_id, file_name):
        try:
            downloader = self.google.download(file_id, file_name)
            print("Downloading 0%", end='\r')
            self.conclude_operation_while_logging(downloader, "Downloading")
            print("Downloaded 100% ")
        except Exception as err:
            print('An error happened while downloading the file.')
            print(err)


class Upload(Command):
    TYPE = "upload"
    HELP = "Upload a file to Google Drive. Accepts wildcards and can find the last modified file."

    @staticmethod
    def add_to_subparser(subparsers):
        parser = subparsers.add_parser(
            Upload.TYPE,
            help=Upload.HELP
        )
        parser.set_defaults(command=Upload)

        parser.add_argument(
            'file',
            metavar='FILE',
            nargs='+',
            help="Path or filename of the file to be uploaded (accepts wildcards)"
        )
        parser.add_argument(
            '--last',
            '-l',
            help="Uploads the last modified file if a wildcard is used",
            action='store_true'
        )

    def execute(self):
        self.set_filepath_for_first_arg()
        if (self.args.last and len(self.args.file) > 1):
            self.set_filepath_for_last_modified()
        self.set_mimetype()
        return self.upload()

    def set_filepath_for_first_arg(self):
        self.filepath = self.args.file[0]

    def set_filepath_for_last_modified(self):
        print('Found %s files' % len(self.args.file))
        last_modified = self.find_last_modified_file(self.args.file)
        self.filepath = last_modified

    def find_last_modified_file(self, files, last_modified_file=None, last_time=None):
        # TODO: Find a way to improve this
        try:
            if not files:
                return last_modified_file
            file = files.pop()
            time = os.stat(file).st_mtime
            if not last_time or time > last_time:
                last_time = time
                last_modified_file = file
            return self.find_last_modified_file(files, last_modified_file, last_time)
        except Exception as err:
            self.filepath = None
            print('An error occurred while handling the wildcard files.')
            print(err)

    def set_mimetype(self):
        if not self.filepath:
            return
        guessed_type = mimetypes.guess_type(self.filepath, True)
        if guessed_type is None:
            print("Wasn't able to guess mimetype")
            return
        self.mime_type = guessed_type[0]

    def upload(self):
        try:
            uploader = self.google.upload(self.filepath, self.mime_type)
            print("Uploading 0%", end='\r')
            response = self.conclude_operation_while_logging(uploader, "Uploading")
            if not response:
                return
            print("Uploaded 100% ")
            print('File ID: %s\n' % response.get('id'))
        except Exception as err:
            print('An error occurred while uploading the file.')
            print(err)


class List(Command):
    TYPE = "list"
    HELP = "Browse all files or search on Google Drive."
    FILES_PER_PAGE = 5

    @staticmethod
    def add_to_subparser(subparsers):
        parser = subparsers.add_parser(
            List.TYPE,
            help=List.HELP
        )
        parser.set_defaults(command=List)

        parser.add_argument(
            'file',
            metavar='FILE',
            nargs='?',
            help="Name of the file to be searched (leave blank to see all files)"
        )

    def execute(self):
        self.list_files()

    def list_files(self):
        files_found, next_page = self.search()
        self.describe_files(files_found)
        while next_page is not None:
            try:
                if self.input_stop_next_page():
                    break
                files_found, next_page = self.search(next_page)
                self.describe_files(files_found)
            except KeyboardInterrupt:
                return

    def search(self, next_page=None):
        search_query = self.args.file
        files_found, new_next_page = self.google.search_filename(
            search_query,
            self.FILES_PER_PAGE,
            next_page
        )
        return files_found, new_next_page

    def describe_files(self, files):
        for file in files:
            Utils.describe_file(file)

    def input_stop_next_page(self):
        # When Enter is pressed, the result is blank, thus false
        return input(">>> Press Enter for the next results\n")


class CommandParser():
    """Starts the Commands' parsers and executes a command if the arguments are valid"""
    COMMANDS = [Download, Upload, List]
    NAME = "gdrive"
    DESCRIPTION = "A script to interact with your Google Drive files"

    def __init__(self):
        self.parser = ArgumentParser(
            prog=self.NAME,
            description=self.DESCRIPTION
        )
        subparsers = self.parser.add_subparsers()
        for command in self.COMMANDS:
            command.add_to_subparser(subparsers)
        self.args = self.parser.parse_args()

    def execute_command(self):
        if not self.is_command_valid():
            self.parser.print_help()
            return
        command = self.build_command()
        if not command.is_service_started():
            print("Google Drive Service failed to start")
            return
        command.execute()

    def is_command_valid(self):
        try:
            return self.args and self.args.command
        except AttributeError:
            return False

    def build_command(self):
        return self.args.command(self.args)


class ConflatedChannel:
    """A list of size 0 or 1. When adding to a list of size=1, substitute the value"""
    def __init__(self):
        """Initialize channel"""
        self.__channel = []
        self.__open = True

    def __str__(self):
        """String representation"""
        return str(self.__channel)

    def send(self, value):
        """Adds to the channel. If full, replace value.
        If channel is closed, raise a ValueError.
        """
        if not self.is_open():
            raise ValueError("Channel is closed.")

        self.__channel.clear()
        self.__channel.append(value)

    def pop(self):
        """Returns the value in the channel, or None"""
        try:
            return self.__channel.pop()
        except:
            return None

    def is_open(self):
        """Checks if the channel is open for send()"""
        return self.__open

    def close(self):
        """Close the channel. It will not receive new values."""
        self.__open = False


class ProgressLogger():
    """Logs progress from a worker thread."""
    def __init__(self, operation):
        self.__channel = ConflatedChannel()
        self.__operation = operation
        self.__start_time = time.time()
        self.__worker = threading.Thread(target=self.__work, daemon=True)
        self.__worker.start()

    def send(self, status):
        """Try to send a new value to the channel."""
        self.__channel.send(status)

    def close(self):
        """Close the channel and join the thread."""
        self.__channel.close()
        self.__worker.join()

    def __work(self):
        """Print logs while the channel is open and receiving values."""
        last_size = 0.0
        last_time = self.__start_time
        while self.__channel.is_open():
            status = self.__channel.pop()
            if status:
                new_time = time.time()
                self.__log_progress(status, last_size, last_time)
                last_time = new_time
                last_size = status.resumable_progress
            # Limits logs to 1 per second at most
            time.sleep(1)

    def __log_progress(self, status, previous_size, previous_time):
        """Print log from status."""
        progress = int(status.progress() * 100)
        total_size = Utils.size_to_human_readable(status.total_size)
        current_size = status.resumable_progress
        size = Utils.size_to_human_readable(current_size)

        current_time = time.time()
        timer = time.strftime("%H:%M:%S", time.gmtime(current_time - self.__start_time))

        diff_size = current_size - previous_size
        diff_time = current_time - previous_time
        speed = Utils.size_to_human_readable(diff_size / diff_time)

        estimated_time = (status.total_size - current_size) / (diff_size / diff_time)
        eta = time.strftime("%H:%M:%S", time.gmtime(estimated_time))

        print("%s %d%% - %s/%s - %s/s - %s - ETA: %s             " %
              (self.__operation, progress, size, total_size, speed, timer, eta), end='\r')


class Utils:

    @staticmethod
    def describe_file(metadata):
        """Print file metadata"""
        print("Name: %s" % metadata["name"])
        print("Owner: %s" % metadata["owners"][0]["displayName"])
        if 'size' in metadata:
            print("Size: %s" % Utils.size_to_human_readable(float(metadata["size"])))
        if 'modifiedByMeTime' in metadata:
            print("Modified by Me: %s" % metadata["modifiedByMeTime"])
        else:
            print("Modified: %s" % metadata["modifiedTime"])
        print("ID: %s\n" % metadata["id"])

    @staticmethod
    def size_to_human_readable(num, suffix='B'):
        """Converts bytes to a more human-readable metric"""
        for unit in ['', 'K', 'M', 'G', 'T']:
            if abs(num) < 1024.0:
                return "%3.1f%s%s" % (num, unit, suffix)
            num /= 1024.0
        return None


def main():
    CommandParser().execute_command()

if __name__ == '__main__':
    main()
