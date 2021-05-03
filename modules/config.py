from os.path import expanduser, join

HOME = expanduser("~")
GDRIVE_PATH = join(HOME, '.gdrive')
CREDENTIALS_PATH = join(GDRIVE_PATH, 'credentials.json')
TOKEN_PATH = join(GDRIVE_PATH, 'token.pickle')
EXTRACTOR_CONFIG_FILE = join(GDRIVE_PATH, 'data_config.json')
UPLOAD_CHUNK_SIZE = 1024 * 1024 * 10  # 10MB
DOWNLOAD_CHUNK_SIZE = 1024 * 1024 * 10  # 10MB
