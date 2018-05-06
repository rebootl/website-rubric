'''config'''

DATABASE = '/somepath/website.db'

# a random key, use:
# >>> import os
# >>> os.urandom(24)
# to generate one
# acc. to flask docs http://flask.pocoo.org/docs/0.12/quickstart/#sessions
SECRET_KEY = 'development key'

# author name
AUTHOR_NAME = "Cem"
# interface user
USERNAME = 'username'
# password as sha1sum, e.g. '5baa61e4c9b93f3f0682250b6cf8331b7ee68fd8'
PASSWD_SHA1 = '448h0h4hfi...'

# program path
# (needed for image processing)
# --> improve ??
RUN_ABSPATH = '/webapp/website_rubric'

# default category id
DEFAULT_CAT_ID = 0

# types of entries and default
ENTRY_TYPES = [ 'note', 'special' ]
DEFAULT_PAGE_TYPE = 'note'

# json export file
DB_ENTRIES_JSON_DUMP = '/somepath-on-server/entries.json'


### SYSTEM STUFF

# date / datetime formats
DATE_FORMAT = "%Y-%m-%d"
DATETIME_FORMAT = "%Y-%m-%d %H:%M"

# image extensions
# (needed for exif processing)
JPEG_EXTS = [ '.jpg', '.jpeg', '.JPG' ]
IMG_EXTS = [ '.jpg', '.jpeg', '.JPG', '.png', '.PNG' ]
