'''common "frontend" functions'''
import os
import subprocess
import re
import hashlib
from PIL import Image, ImageOps
from PIL import ImageFile
# (prevent OSError: image file is truncated)
ImageFile.LOAD_TRUNCATED_IMAGES = True

from datetime import datetime

import config
# --> shouldn't flask current_app config be used here ???

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

def make_thumb_samename(img_in_path_abs, out_dir):
    '''generate thumbnail for image using the same name
(out_dir has to be a different directory)
'''
    in_filename = os.path.basename(img_in_path_abs)
    out_filepath_abs = os.path.join(out_dir, in_filename)

    # leave if already there
    if os.path.isfile(out_filepath_abs):
        return

    image = Image.open(img_in_path_abs)
    thumb = ImageOps.fit(image, (256, 256), Image.ANTIALIAS)
    thumb.save(out_filepath_abs)

# deprecated (used in old importer)
def date_obj(str):
    try:
        date_obj = datetime.strptime(
            str,
            config.DATE_FORMAT
        )
    except ValueError:
        try:
            date_obj = datetime.strptime(
                str,
                config.DATETIME_FORMAT
            )
        except ValueError:
            date_obj = None
    return date_obj

def url_encode_str(string):
    '''convert a string to be usable in a url'''
    # 1) convert spaces to dashes
    dashed = re.sub(r'[\ ]', '-', string)
    # 2) only accept [^a-zA-Z0-9-]
    #    replace everything else by %
    alnum_dashed = re.sub(r'[^a-zA-Z0-9-]', '-', dashed)
    # 3) lowercase
    return alnum_dashed.lower()

def get_md5sum(str):
    '''generate md5sum from string'''
    return hashlib.md5(str.encode()).hexdigest()

def date_norm( date_str,
               datetime_fmt=config.DATETIME_FORMAT,
               date_fmt=config.DATE_FORMAT ):
    '''return normed date, time and datetime strings
from a date string that has format defined in config'''
    try:
        date_obj = datetime.strptime( date_str,
                                      datetime_fmt )
        date_norm = date_obj.strftime("%Y-%m-%d")
        time_norm = date_obj.strftime("%H:%M")
        datetime_norm = date_obj.strftime("%Y-%m-%d %H:%M")
    except ValueError:
        try:
            date_obj = datetime.strptime( date_str,
                                          date_fmt )
            date_norm = date_obj.strftime("%Y-%m-%d")
            time_norm = "NOT SET"
            datetime_norm = date_obj.strftime("%Y-%m-%d %H:%M")
        except ValueError:
            date_norm = "ERRONEOUS_DATE"
            time_norm = "NOT SET"
            datetime_norm = "ERRONEOUS_DATE"
    return date_norm, time_norm, datetime_norm

def datetime_norm(datetime_str, datetime_fmt=config.DATETIME_FORMAT):
    try:
        date_obj = datetime.strptime(datetime_str, datetime_fmt)
        return date_obj.strftime("%Y-%m-%d %H:%M")
    except ValueError:
        return False
