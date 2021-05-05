import os
import pickle

# noinspection PyPackageRequirements
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
# noinspection PyProtectedMember
from googleapiclient import _auth
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload

from modules import config


class GoogleCredentials:
    """Handles the local Credentials file for the Google Drive API"""

    SCOPES = [
        'https://www.googleapis.com/auth/drive',
        'https://www.googleapis.com/auth/drive.metadata'
    ]

    def __init__(self):
        self._creds = None

    def build(self):
        self.load_credentials()
        if not self.is_credentials_valid():
            self.prepare_credentials()
        return self._creds

    def prepare_credentials(self):
        if self._creds and self.is_credentials_outdated():
            self._creds.refresh(Request())
        else:
            self.create_credentials()
        self.save_credentials()

    def load_credentials(self):
        self._creds = None
        if os.path.exists(config.TOKEN_PATH):
            with open(config.TOKEN_PATH, 'rb') as token:
                self._creds = pickle.load(token)

    def is_credentials_valid(self):
        return self._creds is not None and self._creds.valid

    def is_credentials_outdated(self):
        return self._creds.expired and self._creds.refresh_token

    def create_credentials(self):
        if os.path.exists(config.CREDENTIALS_PATH):
            flow = InstalledAppFlow.from_client_secrets_file(config.CREDENTIALS_PATH, self.SCOPES)
            self._creds = flow.run_local_server(port=0)
        else:
            print('Credentials not found at %s' % config.CREDENTIALS_PATH)
            exit()

    def save_credentials(self):
        with open(config.TOKEN_PATH, 'wb') as token:
            pickle.dump(self._creds, token)


class GoogleService:
    """Encapsulates Google Drive API, provides usability methods and keeps API-side configurations"""

    def __init__(self):
        self.creds = GoogleCredentials().build()
        self._google = build('drive', 'v3', credentials=self.creds)

    def is_valid(self):
        return self._google is not None

    def drive(self):
        # Google Drive resource is dynamically populated
        # pylint: disable=maybe-no-member
        # noinspection PyUnresolvedReferences
        return self._google.files()

    def create_http(self):
        return _auth.authorized_http(self.creds)

    def get_file_metadata(self, file_id):
        try:
            fields = 'id, name, size, modifiedTime, modifiedByMeTime, owners'
            return self.drive().get(fileId=file_id, fields=fields).execute(http=self.create_http())
        except HttpError:
            return None

    def search_filename(self, filename=None, page_size=1, page_token=''):
        query = ''
        if filename is not None:
            # Could also be name = '%s' for an exact search
            query = "name contains '%s'" % filename
        fields = ','.join(
            ('nextPageToken',) +
            tuple(map(lambda x: 'files/' + x, ('id', 'name', 'size', 'modifiedTime', 'modifiedByMeTime', 'owners')))
        )
        http = self.create_http()
        while True:
            search = self.drive().list(
                q=query,
                orderBy='modifiedByMeTime desc',
                fields=fields,
                pageSize=page_size,
                pageToken=page_token
            ).execute(http=http)
            files_found = search.get('files', [])
            page_token = search.get('nextPageToken', None)
            yield files_found
            if page_token is None:
                break

    def get_last_modified_file(self):
        try:
            return next(self.search_filename())[0]
        except KeyError:
            return None

    def get_file_downloader(self, metadata):
        def file_downloader(start: int, end: int) -> bytes:
            request.headers['Range'] = f"bytes={start}-{end}"
            return request.execute(http=self.create_http())

        file_id, file_name, file_size = metadata["id"], metadata["name"], int(metadata["size"])
        request = self.drive().get_media(fileId=file_id)
        return file_downloader

    def upload(self, filepath, mime_type):
        filename = filepath.split('/')[-1]
        file_metadata = {'name': filename}
        print('Uploading the file: %s' % filename)
        media = MediaFileUpload(
            filepath,
            mimetype=mime_type,
            resumable=True,
            chunksize=config.UPLOAD_CHUNK_SIZE
        )
        return self.drive().create(
            body=file_metadata,
            media_body=media,
            fields='id'
        )
