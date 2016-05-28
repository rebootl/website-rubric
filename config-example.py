'''config'''

DATABASE = '/somepath/website.db'

# a random key, e.g.: 'bd9c0dd8620f6a49ebd7f2176552d141.asgo249'
SECRET_KEY = 'development key'

# interface user
USERNAME = 'username'
# password as sha1sum, e.g. '5baa61e4c9b93f3f0682250b6cf8331b7ee68fd8'
PASSWD_SHA1 = '448h0h4hfi...'

# (needed for image processing)
# --> improve ??
RUN_ABSPATH = '/webapp/rubric_dyn'

### SYSTEM STUFF

# date / datetime formats
# (curr. not used
#  --> use it, makes kinda sense)
DATE_FORMAT = "%Y-%m-%d"
# (used)
DATETIME_FORMAT = "%Y-%m-%d %H:%M"

# (used/useful in/for importer)
PAGE_EXT = ".page"

# (needed for exif processing)
JPEG_EXTS = [ '.jpg', '.jpeg', '.JPG' ]

# image extensions
# (needed for image processing)
IMG_EXTS = [ '.jpg', '.jpeg', '.JPG', '.png', '.PNG' ]

# DEPRECATED
#META_DEFAULTS = { 'files': [],
#                  'type': "special",
#                  'title': "NO TITLE SET",
#                  'date': "NO DATE SET",
#                  'author': "NO AUTHOR SET" }

# DEPRECATED
#PANDOC_OPTS = [ '--to=html5',
#                '--filter=/home/cem/Scripts/rubric-dyn/rubric_dyn/filter_img_path.py' ]
