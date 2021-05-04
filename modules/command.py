from argparse import ArgumentParser

from modules import extractor, logger, config
from modules.chunks import Chunks
from modules.googleservice import GoogleService
from modules.progresslogger import ProgressLogger, Progress
from modules.util import current_is_python36, find_last_modified_file, guess_mimetype, move_cursor_up, \
    delete_lines, for_lines, files_descriptions, print_files_descriptions, describe_files


class Command:
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

    async def execute(self):
        pass

    def is_service_started(self) -> bool:
        return self.google.is_valid()


class Download(Command):
    TYPE = "download"
    HELP = "Download a file from Google Drive through ID or Filename."

    def __init__(self, args):
        super().__init__(args)
        self.file = " ".join(self.args.file)

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
            '-n',
            '--name',
            help='Will use FILE as a filename to search',
            action='store_true'
        )
        name_or_id.add_argument(
            '-i',
            '--id',
            help='Will use FILE as a file ID to download',
            action='store_true'
        )
        parser.add_argument(
            '-l',
            '--last',
            help="Downloads the last modified file",
            action='store_true'
        )
        parser.add_argument(
            '-e',
            '--extract',
            help='Tries to extract the downloaded file',
            action='store_true'
        )

    async def execute(self):
        extract = self.args.extract
        if self.args.last:
            await self.download_last_uploaded_file(extract)
        elif not self.args.file:
            print('Please inform the ID or name of the file you want to download. Exiting...')
            return
        elif self.args.name:
            await self.download_filename(extract)
        elif self.args.id:
            await self.download_id(extract)
        else:
            await self.try_download_id_then_name(extract)

    async def download_last_uploaded_file(self, extract):
        last_file = self.google.get_last_modified_file()
        if not last_file:
            print("Could not find any file")
            return
        await self.download_from_metadata(last_file, extract)

    async def download_filename(self, extract):
        file_found, _ = self.google.search_filename(self.file)
        if not file_found:
            print("Could not find any file that contains '%s' on the name" % self.file)
            return
        await self.download_from_metadata(file_found, extract)

    async def download_id(self, extract):
        file_found = self.google.get_file_metadata(self.file)
        if not file_found:
            print("Could not find file with '%s' as ID" % self.file)
            return
        await self.download_from_metadata(file_found, extract)

    async def try_download_id_then_name(self, extract):
        file_id_found = self.google.get_file_metadata(self.file)
        if file_id_found:
            await self.download_from_metadata(file_id_found, extract)
        else:
            await self.download_filename(extract)

    async def download_from_metadata(self, metadata, extract):
        if metadata is None:
            print('Could not find file to download')
            return
        file_name = metadata["name"] or "Unknown filename"
        describe_files(metadata)
        try:
            await self.download(metadata)
            if extract:
                extractor.extract(file_name)
        except BaseException as e:
            logger.d("Failed downloading or extracting")
            logger.d(e)
            raise

    async def download(self, metadata):
        file_downloader = self.google.get_file_downloader(metadata)
        file_id, file_name, file_size = metadata["id"], metadata["name"], int(metadata["size"])
        chunks = Chunks(file_name, file_size, config.DOWNLOAD_CHUNK_SIZE, file_downloader)
        file_name = metadata['name']
        try:
            print(f"Downloading the file: {file_name}")
            print("Downloading 0%", end='\r')
            await self._conclude_operation_while_logging(chunks, "Downloading")
            print('\x1b[2K', end='\r')
            print("Download finished.")
        except BaseException as err:
            print(f'An error happened while downloading the file {file_name}.')
            logger.d(f'Error:')
            logger.d(err)
            logger.stacktrace()
            chunks.cancel()
            raise

    @staticmethod
    async def _conclude_operation_while_logging(chunks: Chunks, title: str):
        try:
            with ProgressLogger(title) as progress_logger:
                async for progress in chunks.progresses():
                    logger.d(f"Sending progress {progress} to ProgressLogger")
                    await progress_logger.send(progress)

            # Demonstrates what we would need to do to await all printing. But we don't need to:
            # If download is done, it is done, we shouldn't wait for a slow ProgressLogger.
            #
            # logger.d(f"We are done sending all status, now await the printing")
            # if current_is_python36():
            #     await progress_logger.await_it()
            # else:
            #     await progress_logger

            # Ensure final file was written
            if current_is_python36():
                # 3.7, and user defined coroutines in 3.6
                await chunks.await_it()
            else:
                await chunks
        except BaseException as e:
            print('\x1b[2K', end='\r')
            logger.d(f'An error happened while running operation {title}')
            logger.d(e)
            # traceback.print_exc()
            raise


class Upload(Command):
    TYPE = "upload"
    HELP = "Upload a file to Google Drive. Accepts wildcards and can find the last modified file."

    def __init__(self, args):
        super().__init__(args)

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

    async def execute(self):
        self.upload()

    def get_filepath(self):
        files = self.args.file
        if self.args.last and len(files) > 1:
            print('Found %s files' % len(files))
            return find_last_modified_file(*files)
        else:
            return files[0]

    @staticmethod
    def _conclude_operation_while_logging(task, title):
        try:
            with ProgressLogger(title) as progress_logger:
                result = None
                while not result:
                    status, result = task.next_chunk()
                    if status:
                        progress = Progress(status.resumable_progress, status.total_size)
                        progress_logger.send(progress)
                return result
        except BaseException as err:
            print('\x1b[2K', end='\r')
            print(f'An error happened while running operation {title}')
            logger.d(err)

    def upload(self):
        try:
            filepath = self.get_filepath()
            mimetype = guess_mimetype(filepath)
            upload_task = self.google.upload(filepath, mimetype)
            print("Uploading 0%", end='\r')
            response = self._conclude_operation_while_logging(upload_task, "Uploading")
            if not response:
                return
            print("Upload finished.")
            print('File ID: %s\n' % response.get('id'))
        except BaseException as err:
            print('An error occurred while uploading the file.')
            logger.d(err)


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

    async def execute(self):
        self.list_files()

    def list_files(self):
        num_printed_lines = 0
        for files_found in self.search():
            for_lines(num_printed_lines, move_cursor_up, delete_lines, move_cursor_up)
            descs = files_descriptions(*files_found)
            print_files_descriptions(*descs)
            if input(">>> Press Enter for the next results\n"):
                break
            num_printed_lines = len(descs) + sum(map(len, descs)) + 2  # last 2 lines are input text + newline

    def search(self):
        yield from self.google.search_filename(self.args.file, self.FILES_PER_PAGE)


class CommandParser:
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

    async def execute_command(self):
        if not self.is_command_valid():
            self.parser.print_help()
            return
        command = self.build_command()
        if not command.is_service_started():
            print("Google Drive Service failed to start")
            return
        await command.execute()

    def is_command_valid(self):
        try:
            return self.args and self.args.command  # TODO this probably doesn't do what we think it does
        except AttributeError:
            return False

    def build_command(self) -> Command:
        return self.args.command(self.args)
