'''interface helper functions (not returning a view)'''
import os
import json
import re
from flask import current_app, flash, render_template
from rubric_dyn.common import pandoc_pipe, date_norm2, time_norm, \
    url_encode_str, make_thumb_samename
from rubric_dyn.ExifNice import ExifNice

# --> for debug only !!
import sys

def get_images_from_md(md_text):
    '''get a list of images and their thumbnails from markdown text'''
    text_md_subst, img_blocks = preprocess_md(md_text)

    #media_abspath = os.path.join(current_app.config['RUN_ABSPATH'], 'media')
    thumbs_abspath = os.path.join( current_app.config['RUN_ABSPATH'],
                                   'media/thumbs' )

    images = []
    for img_block in img_blocks:
        image_src = img_block[1]
        image_thumb = os.path.join('/media/thumbs', os.path.basename(image_src))

        # handle "external" images
        if image_src.startswith('http://'):
            image_thumb = image_src
            image_src = 'External URL: ' + image_src

        image = { 'src': image_src,
                  'thumb': image_thumb }

        images.append(image)

        # generate thumbnail
        image_abspath = os.path.join( current_app.config['RUN_ABSPATH'],
                                      os.path.relpath(image_src, '/') )
        # (debug output)
        #sys.stderr.write('\nRUN_ABSPATH:'+str(current_app.config['RUN_ABSPATH']))
        #sys.stderr.write('\nIMG SRC:'+image_src)
        make_thumb_samename(image_abspath, thumbs_abspath)

    return images

def get_images(subpath):
    '''get image list from subpath (inside /media/)'''
    # absolute paths
    media_abspath = os.path.join(current_app.config['RUN_ABSPATH'], 'media')
    images_path = os.path.join(media_abspath, subpath)

    if not os.path.isdir(images_path):
        flash("Warning: Invalid image-path given...")
        return []

    files = os.listdir(images_path)
    # filter images
    image_files = []
    for file in files:
        file_ext = os.path.splitext(file)[1]
        if file_ext in current_app.config['IMG_EXTS']:
            image_files.append(file)

    image_files.sort()

    return image_files

def gen_image_md(subpath, images):
    '''generate markdown from a list of image filenames'''
    md_text = ""
    for image in images:
        image_subpath = os.path.join('/media/', subpath, image)
        img_md = "![]({})\n\n".format(image_subpath)
        md_text += img_md
    return md_text

# --> deprecated ?
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
        # --> set defaults in ExifNice !!
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
    # (existence is checked in function --> maybe better check here ? ==> No, WTF?)
    make_thumb_samename(image_file_abspath, thumbs_abspath)

def repl_image(img_block):
    '''replace markdown image syntax by html,
using image.html template

- including exif information
- adapting source path (add /media prefix)
'''
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
    #re_md_img = re.compile(r'^!\[([^\]]+)\]\(([^)]+)\)', re.MULTILINE|re.DOTALL)
    # ==> fix empty alt text !!
    re_md_img = re.compile(r'^!\[(.*?)\]\((.*?)\)', re.MULTILINE|re.DOTALL)

    # get markdown image tags
    # a list of tuples: (alt, src)
    img_blocks = re_md_img.findall(text_md)

    # (debug output)
    #sys.stderr.write(str(img_blocks))

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
                                   [ '--to=html5', '--smart' ] )
#                                   [ '--to=html5',
#                                     '--toc',
#                                     '--template=/home/cem/Scripts/rubric-dyn/rubric_dyn/templates/pandoc/pandoc-base.html' ] )

    # back-substitute here
    for img_block in img_blocks:
        # process
        img_block_html = repl_image(img_block)
        # back-subsitute
        body_html_subst = body_html_subst.replace( '<p>' + IMG_SUBST + '</p>',
                                                   img_block_html, 1 )

    return ref, date_normed, time_normed, body_html_subst, None
