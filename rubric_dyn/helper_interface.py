'''interface helper functions (not returning a view)'''
import os
import json
import re
from flask import current_app, flash, render_template
from rubric_dyn.common import pandoc_pipe, date_norm2, time_norm, \
    url_encode_str
from rubric_dyn.ExifNice import ExifNice, ExifNiceStr

def process_image(image_file, image_dir, ref):
    '''process image data
- exif information
- insert image in db
- create thumbnail
'''
    image_file_abspath = os.path.join(image_dir, image_file)

    # extract exif into json
    if os.path.splitext(image_file)[1] in current_app.config['JPEG_EXTS']:
        img_exif = ExifNice(image_file_abspath)
        if img_exif.has_exif:
            exif_json = img_exif.get_json()
            datetime_norm = datetimesec_norm( img_exif.datetime,
                                              "%Y:%m:%d %H:%M:%S" )
        else:
            exif_json = ""
            datetime_norm = ""
    else:
        exif_json = ""
        datetime_norm = ""

    # add thumb ref
    thumb_ref = os.path.join('thumbs', image_file)

    # insert in db
    db_insert_image( ref,
                     thumb_ref,
                     datetime_norm,
                     exif_json,
                     gallery_id )

    # create thumbnail if not exists
    # (existence is checked in function --> maybe better check here ?)
    make_thumb_samename(image_file_abspath, thumbs_abspath)

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

def repl_image(img_block):
    '''replace markdown image syntax by html,
using image.html template

- including exif information
- adapting source path (add /media prefix)
'''
    #alt = match_obj.group(1)
    #src = match_obj.group(2)
    alt = img_block[0]
    src = img_block[1]

    # add /media prefix
    if os.path.dirname(src) == '':
        src = os.path.join('/media', src)

    # get exif
    if os.path.splitext(src)[1] in current_app.config['JPEG_EXTS']:
        # make abs path
        img_path_abs = os.path.join( current_app.config['RUN_ABSPATH'],
                                     src.lstrip('/') )
        exif_inst = ExifNice(img_path_abs)
        # --> set defaults, really
        if exif_inst.has_exif:
            img_exif = exif_inst.exif_nice
        else:
            img_exif = None
    else:
        img_exif = None

    repl_html = render_template( 'image.html',
                                 image = { 'alt': alt,
                                           'src': src,
                                           'exif': img_exif })

    return repl_html

IMG_SUBST = 'IMG_23a12f67f614b5518c7f1c2465bf95e3'

def preprocess_md(text_md):
    '''pre-processing markdown text using own functions/filter

this is needed to include exif image information

replacing image tags (markdown) by a placeholder

doing it this way may seem quite bad at a first glance,
and it may actually be...

e.g. image syntax at the beginning of the line
inside fenced code blocks will be replaced:

~~~
![This is caption.](image.jpg)
~~~

however, considering the other solutions I honestly
believe this to be the best for now

alternatives:
- pandoc filters --> terribly overcomplicating things
- using misaka for markdown processing --> the example
    from it's own docs, doesn't work...
- using markdown module and evtl. write an extension <-- probably a good idea...
'''
    # regular expr. to match markdown images
    # (at the beginning of line)
    # two groups
    # what's this "|" for the argument... WTF ?!
    re_md_img = re.compile(r'^!\[(.+?)\]\((.+?)\)', re.MULTILINE|re.DOTALL)

    # get markdown image tags
    # a list of tuples: (alt, src)
    img_blocks = re_md_img.findall(text_md)

    # substitute by placeholders
    text_md_subst = re_md_img.sub(IMG_SUBST, text_md)

    return text_md_subst, img_blocks

def process_input(title, date_str, time_str, text_md):
    '''page edit input processing and prepare for database
(new, replacement for process_edit above)'''

    # make ref (from title)
    ref = url_encode_str(title)

    # process date and time
    date_normed = date_norm2(date_str, "%Y-%m-%d")
    if not date_normed:
        date_normed = "NOT_SET"
        flash("Warning: bad date format..., setting to 'NOT_SET'.")
    time_normed = time_norm(time_str, "%H:%M")
    if not time_normed:
        time_normed = "NOT_SET"
        flash("Warning: bad time format..., setting to 'NOT_SET'.")

    # pre-process markdown
    # substitute text and get image blocks
    text_md_subst, img_blocks = preprocess_md(text_md)

    # process markdown
    body_html_subst = pandoc_pipe( text_md_subst,
                                   [ '--to=html5' ] )

    # back-substitute here
    for img_block in img_blocks:
        # process
        img_block_html = repl_image(img_block)
        # back-subsitute
        body_html_subst = body_html_subst.replace( '<p>' + IMG_SUBST + '</p>',
                                                   img_block_html, 1 )

    # create exif json
    #img_exifs_json = create_exifs_json(meta['files'])

    return ref, date_normed, time_normed, body_html_subst, None
