'''common "frontend" functions'''
import os
import subprocess
import re
import hashlib
from PIL import Image, ImageOps
from PIL import ImageFile
# prevent OSError: image file is truncated
ImageFile.LOAD_TRUNCATED_IMAGES = True

from datetime import datetime
#from pytz import timezone

import config
# --> shouldn't flask current_app config be used here ???

# --> not using atm...
#def get_tzname(date_norm, time_norm):
#    '''get the timezone name for given date/time,
#needed for daylight saving time e.g.: CET/CEST'''
#    date_str = date_norm + " " + time_norm
#    date_obj = datetime.strptime(date_str, "%Y-%m-%d %H:%M")
#
#    tz_obj = timezone(config.PYTZ_TIMEZONE)
#
#    loc_dt = tz_obj.localize(date_obj)
#
#    return loc_dt.strftime('%z')

def gen_href(row):
    '''generate href for different page types'''
    if row['type'] == 'article':
        return os.path.join('/articles', row['date_norm'], row['ref'])
    elif row['type'] == 'special':
        return os.path.join('/special', row['ref'])
    elif row['type'] == 'note':
        return os.path.join('/notes', row['ref'])
    else:
        return "NOT_DEFINED"

def pandoc_pipe(content, opts):
    '''create a pandoc pipe reading from a variable and returning the output'''

    pandoc_command = [ 'pandoc' ] + opts

    proc = subprocess.Popen( pandoc_command,
                             stdin=subprocess.PIPE,
                             stdout=subprocess.PIPE )
    input = content.encode()
    out, err = proc.communicate(input=input)
    output = out.decode('utf-8')

    return output

def copy_file(in_path, out_dir):
    '''call copy w/o preset directories
(not recursive)'''
    if not os.path.isfile(in_path):
        print("Warning: File not found:", in_path)
        return

    if not os.path.isdir(out_dir):
        os.makedirs(out_dir)

    # using cp -u
    # --> shutil.copy could be used for this
    cp_command = ['cp', '-u', in_path, out_dir]
    exitcode = subprocess.call(cp_command)

# --> used ??
def make_thumb(img_in_path_abs, out_dir):
    '''generate thumbnail for image'''
    in_filename = os.path.basename(img_in_path_abs)
    out_filename = os.path.splitext(in_filename)[0] + "_thumb.png"

    out_thumbpath_abs = os.path.join(out_dir, out_filename)

    # leave if already there
    if os.path.isfile(out_thumbpath_abs):
        return

    image = Image.open(img_in_path_abs)
    thumb = ImageOps.fit(image, (256, 256), Image.ANTIALIAS)
    thumb.save(out_thumbpath_abs, "PNG")

# --> are this _and_ above function both needed ??
#     evtl. make one function ???
def make_thumb_samename(img_in_path_abs, out_dir):
    '''generate thumbnail for image using the same name
(out_dir has to be a different directory)
'''
    in_filename = os.path.basename(img_in_path_abs)
    out_filepath_abs = os.path.join(out_dir, in_filename)

    # check in-file
    if not os.path.isfile(img_in_path_abs):
        return

    # leave if already there
    if os.path.isfile(out_filepath_abs):
        return

    if not os.path.isdir(out_dir):
        os.mkdir(out_dir)

    image = Image.open(img_in_path_abs)
    thumb = ImageOps.fit(image, (256, 256), Image.ANTIALIAS)
    thumb.save(out_filepath_abs)

# DEPRECATED
# (used in old importer)
#
#def date_obj(str):
#    try:
#        date_obj = datetime.strptime(
#            str,
#            config.DATE_FORMAT
#        )
#    except ValueError:
#        try:
#            date_obj = datetime.strptime(
#                str,
#                config.DATETIME_FORMAT
#            )
#        except ValueError:
#            date_obj = None
#    return date_obj

def url_encode_str(string):
    '''convert a string to be usable in a url'''
    # 1) convert spaces to dashes
    dashed = re.sub(r'[\ ]', '-', string)
    # 2) only accept [^a-zA-Z0-9-]
    #    replace everything else by %
    alnum_dashed = re.sub(r'[^a-zA-Z0-9-]', '-', dashed)
    # 3) lowercase
    return alnum_dashed.lower()

# --> deprecate, don't use this anymore
#     currently it's still in import-page
def get_md5sum(str):
    '''generate md5sum from string'''
    return hashlib.md5(str.encode()).hexdigest()

# DEPRECATED
# in favor of below single functions
# (used in importer)
#
#def date_norm( date_str,
#               datetime_fmt=config.DATETIME_FORMAT,
#               date_fmt=config.DATE_FORMAT ):
#    '''return normed date, time and datetime strings
#from a date string that has format defined in config'''
#    try:
#        date_obj = datetime.strptime( date_str,
#                                      datetime_fmt )
#        date_norm = date_obj.strftime("%Y-%m-%d")
#        time_norm = date_obj.strftime("%H:%M")
#        datetime_norm = date_obj.strftime("%Y-%m-%d %H:%M")
#    except ValueError:
#        try:
#            date_obj = datetime.strptime( date_str,
#                                          date_fmt )
#            date_norm = date_obj.strftime("%Y-%m-%d")
#            time_norm = "NOT SET"
#            datetime_norm = date_obj.strftime("%Y-%m-%d %H:%M")
#        except ValueError:
#            date_norm = "ERRONEOUS_DATE"
#            time_norm = "NOT SET"
#            datetime_norm = "ERRONEOUS_DATE"
#    return date_norm, time_norm, datetime_norm

def date_norm2(date_str, date_fmt=config.DATETIME_FORMAT):
    try:
        date_obj = datetime.strptime(date_str, date_fmt)
        return date_obj.strftime("%Y-%m-%d")
    except ValueError:
        return False

def datetime_norm(datetime_str, datetime_fmt=config.DATETIME_FORMAT):
    try:
        date_obj = datetime.strptime(datetime_str, datetime_fmt)
        return date_obj.strftime("%Y-%m-%d %H:%M")
    except ValueError:
        return False

def datetimesec_norm(datetime_str, datetime_fmt):
    try:
        date_obj = datetime.strptime(datetime_str, datetime_fmt)
        return date_obj.strftime("%Y-%m-%d %H:%M:%S")
    except ValueError:
        return False

def time_norm(time_str, time_fmt="%H:%M"):
    try:
        date_obj = datetime.strptime(time_str, time_fmt)
        return date_obj.strftime("%H:%M")
    except ValueError:
        return False
