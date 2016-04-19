'''interface helper functions (not returning a view)'''
import os
import json
from flask import current_app, flash
from rubric_dyn.common import pandoc_pipe
from rubric_dyn.ExifNice import ExifNiceStr

def create_exifs_json(files):
    '''create image info from EXIF data as json dump'''
    img_exifs = {}
    for file in files:
        if os.path.splitext(file)[1] in current_app.config['JPEG_EXTS']:
            img_filepath = os.path.join( current_app.config['RUN_ABSPATH'],
                                         'media',
                                         file )
            exif = ExifNiceStr(img_filepath)
            if exif.display_str:
                image_exif = { os.path.join( '/media',
                                             file ) : exif.display_str }
                img_exifs.update(image_exif)
    if img_exifs:
        return json.dumps(img_exifs)
    else:
        return ""

def process_meta_json(meta_json):
    '''read out meta information from json dump
and set defaults if necessary'''
    try:
        meta = json.loads(meta_json)
    except json.decoder.JSONDecodeError:
        flash("Warning: Error in JSON data, using defaults...")
        meta = {}

    # set defaults
    for key, value in current_app.config['META_DEFAULTS'].items():
            if key not in meta.keys():
                meta[key] = value

    if type == "imagepage":
        if meta['image'] == "" or meta['image'] == None:
            meta['image'] = "NO IMAGE SET"

    return meta

def process_edit(text_input, return_md=False):
    '''process text input including meta information,
also create image information for included image files

used by:
- Page
- views.interface
'''
    # escape shit ?

    # split text in json and markdown block
    meta_json, body_md = text_input.split('%%%', 1)

    meta = process_meta_json(meta_json)

    # process text through pandoc
    body_html = pandoc_pipe( body_md,
                             [ '--to=html5',
                               '--filter=rubric_dyn/filter_img_path.py' ] )

    img_exifs_json = create_exifs_json(meta['files'])

    if not return_md:
        return meta, body_html, img_exifs_json
    else:
        return meta, meta_json, img_exifs_json, body_html, body_md
