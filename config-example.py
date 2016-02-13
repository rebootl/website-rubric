'''config'''

DEBUG = True
DATABASE = 'website.db'
SECRET_KEY = 'development key'
USERNAME = 'noname'
PASSWORD = 'blablabla123'

MEDIA_DIR = "/home/cem/Scripts/rubric-dyn/media"
FONT_DIR = "/home/cem/Scripts/rubric-dyn/localfont"

DATE_FORMAT = "%Y-%m-%d"
DATETIME_FORMAT = "%Y-%m-%d %H:%M"

### import/export stuff

# --> make this a cli argument
CONTENT_DIRS = [ "/home/cem/website_rubric/layout",
                 "/home/cem/Drawings",
                 "/home/cem/Articles",
                 "/home/cem/Astro/2015-02-19",
                 "/home/cem/Astro/2015-02-20",
                 "/home/cem/Astro/2014-12-09_moon",
                 "/home/cem/Astro/2015-02-14_tele",
                 "/home/cem/Astro/2015-08-13",
                 "/home/cem/Astro/2015-12-25",
                 "/home/cem/Fotos_DCAM/2016-01-05",
                 "/home/cem/Astro/2015-12-26" ]

META_DEFAULTS = { 'files': [],
                  'type': "special",
                  'title': "NO TITLE SET",
                  'date': "NO DATE SET",
                  'author': "NO AUTHOR SET" }

PAGE_EXT = ".page"

EXPORT_DIR = "/home/cem/Scripts/rubric-dyn/export"
