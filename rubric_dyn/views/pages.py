'''regular website pages'''
import os
import sqlite3
import json

from flask import Blueprint, render_template, g, request, session, redirect, \
    url_for, abort, flash, current_app

from rubric_dyn.common import pandoc_pipe
from rubric_dyn.db_read import get_entry_by_date_ref_path, get_entry_by_ref
from rubric_dyn.helper_pages import create_page_nav, extract_tags, \
    create_page_nav_image, create_page_nav_gallery

from rubric_dyn.helper_interface import process_input

pages = Blueprint('pages', __name__)

PAGE_NAV_DEFAULT = { 'prev_href': None,
                     'next_href': None,
                     'index': "/" }

### functions returning a view

def show_post(page, page_nav=PAGE_NAV_DEFAULT):
    '''show post
currently used for entry types:
- article
- special
- note
'''
    # title and img_exifs_json are separate because they are used
    # in parent template
    # --> is this really necessary ??
    # ==> for title it may make sense, so it can be set separately
    #     - page.title  used on the page
    #     - title       used as "browser title"
    #     (could be used e.g. by interface/edit
    # (==> img_exifs_json is not used anymore)
    return render_template( 'post.html',
                            title = page['title'],
                            page = page,
                            page_nav = page_nav )

# --> should go into helper_pages
def show_post_by_type_ref(type, ref):
    '''helper to show an entry by type and ref,
page_nav is shown but empty

currently used for types:
- special
- note
'''
    row = get_entry_by_ref(ref, type)

    return show_post(row)

### routes

@pages.route('/')
def home():
    '''the home page'''

    # articles

    # get a list of articles
    g.db.row_factory = sqlite3.Row
    cur = g.db.execute( '''SELECT id, ref, title, date_norm, meta_json, tags
                           FROM entries
                           WHERE type = 'article'
                           AND pub = 1
                           ORDER BY date_norm DESC, time_norm DESC''' )
    articles_rows = cur.fetchall()

    # create article preview
    cur = g.db.execute( '''SELECT body_md
                           FROM entries
                           WHERE id = ?''', (articles_rows[0]['id'],))
    # --> disable sqlite3 row ???
    latest_body_md = cur.fetchone()[0]

    latest_body_md_prev = "\n".join(latest_body_md.split("\n")[:5])

    #body_html = pandoc_pipe( body_md_prev,
    #                         [ '--to=html5' ] )
    prev_ref, \
    prev_date_normed, \
    prev_time_normed, \
    prev_body_html_subst, \
    prev_img_exifs = process_input("", '2000-01-01', '12:00', latest_body_md_prev)

    # notes

    g.db.row_factory = sqlite3.Row
    cur = g.db.execute( '''SELECT ref, title, date_norm, meta_json
                           FROM entries
                           WHERE type = 'note'
                           AND pub = 1
                           ORDER BY datetime_norm DESC''' )
    notes_rows = cur.fetchall()

    # image galleries

    cur = g.db.execute( '''SELECT id, ref, title, date_norm, tags
                           FROM galleries
                           ORDER BY date_norm DESC''' )
    galleries_rows = cur.fetchall()

    galleries = []
    for gallery_row in galleries_rows:
        gallery = { 'ref': gallery_row['ref'],
                    'title': gallery_row['title'],
                    'date_norm': gallery_row['date_norm'],
                    'tags': gallery_row['tags'] }

        cur = g.db.execute( '''SELECT thumb_ref FROM images
                               WHERE gallery_id = ?
                               LIMIT 5''', (gallery_row['id'],) )
        thumbs_rows = cur.fetchall()
        gallery['thumbs'] = thumbs_rows

        galleries.append(gallery)

    return render_template( 'home.html',
                            title = None,
                            articles = articles_rows,
                            article_prev = prev_body_html_subst,
                            notes = notes_rows,
                            galleries = galleries )

@pages.route('/articles/<path:article_path>/')
def article(article_path):
    '''single article'''

    row = get_entry_by_date_ref_path(article_path, 'article')

    # get previous/next navigation
    #page_nav = create_page_nav( row['type'],
    #                            row['datetime_norm'] )
    page_nav = create_page_nav( row['id'],
                                row['type'] )

    return show_post(row, page_nav)

@pages.route('/special/<ref>/')
def special(ref):
    '''special page'''

    return show_post_by_type_ref('special', ref)

@pages.route('/notes/<ref>/')
def show_note(ref):
    '''note page'''

    return show_post_by_type_ref('note', ref)

@pages.route('/galleries/<ref>/')
def gallery(ref):
    '''image gallery page'''

    # load from db
    g.db.row_factory = sqlite3.Row
    cur = g.db.execute('''SELECT id, ref, title, desc, date_norm,
                           tags
                          FROM galleries
                          WHERE ref = ?''', (ref,))
    gallery_row = cur.fetchone()
    # catch not found
    if gallery_row == None:
        abort(404)

    # load thumbnails
    cur = g.db.execute( '''SELECT ref, thumb_ref FROM images
                           WHERE gallery_id = ?
                           ORDER BY datetime_norm ASC''',
                           (gallery_row['id'],) )
    images_rows = cur.fetchall()

    page_nav = create_page_nav_gallery(gallery_row['id'])

    return render_template( 'gallery.html',
                            gallery = gallery_row,
                            images = images_rows,
                            page_nav = page_nav )

@pages.route('/galleries/<path:image_path>/')
def imagepage(image_path):
    '''single image page'''
    gallery_ref, image_ref = os.path.split(image_path)

    image_ref = os.path.join('galleries', image_path)

    # get image data
    g.db.row_factory = sqlite3.Row
    cur = g.db.execute('''SELECT id, ref, caption, datetime_norm,
                           exif_json, gallery_id
                          FROM images
                          WHERE ref = ?''', (image_ref,))
    row = cur.fetchone()
    # catch not found
    if row == None:
        abort(404)

    # prepare data
    try:
        exif = json.loads(row['exif_json'])
    except json.decoder.JSONDecodeError:
        exif = None

    src = os.path.join('/media', image_ref)

    page_nav = create_page_nav_image( row['id'],
                                      row['gallery_id'],
                                      gallery_ref )

    return render_template( 'imagepage.html',
                            image = { 'alt': row['caption'],
                                      'src': src,
                                      'exif': exif },
                            imagepage = True,
                            page_nav = page_nav )
