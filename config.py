from os.path import expanduser, join

HOME = expanduser("~")
GDRIVE_PATH = join(HOME, '.gdrive')
CREDENTIALS_PATH = join(GDRIVE_PATH, 'credentials.json')
TOKEN_PATH = join(GDRIVE_PATH, 'token.pickle')
EXTRACTOR_CONFIG_FILE = join(GDRIVE_PATH, 'data_config.json')

