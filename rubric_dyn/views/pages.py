'''regular website pages'''
import os
import sqlite3
import json
from flask import Blueprint, render_template, g, request, session, redirect, \
    url_for, abort, flash, current_app

from rubric_dyn.common import pandoc_pipe
from rubric_dyn.db_read import get_entry_by_date_ref_path, get_entry_by_ref
from rubric_dyn.helper_pages import create_page_nav, extract_tags

pages = Blueprint('pages', __name__)

### functions returning a view

def show_post(row, page_nav):
    '''show post
currently used for entry types:
- article
- special
- note
'''
    # --> make this one function with belows ?

    # set tags
    # --> could be changed to set _all_ meta information instead
    #entry = { 'db': row }
    #entry['tags'] = extract_tags(row['meta_json'])

    # title and img_exifs_json are separate because they are used
    # in parent template
    # --> is this really necessary ??
    return render_template( 'post.html',
                            title = row['title'],
                            page = row,
                            page_nav = page_nav,
                            img_exifs_json = row['exifs_json'] )

# --> simplify ??
def show_post_by_type_ref(type, ref):
    '''helper to show an entry by type, ref
currently used for types:
- special
- note
'''
    row = get_entry_by_ref(ref, type)

    page_nav = { 'prev_href': None,
                 'next_href': None }

    return show_post(row, page_nav)

### routes

@pages.route('/')
def home():
    '''the home page'''

    # articles
    # get a list of articles
    g.db.row_factory = sqlite3.Row
    cur = g.db.execute( '''SELECT id, ref, title, date_norm, meta_json
                           FROM entries
                           WHERE type = 'article'
                           AND pub = 1
                           ORDER BY datetime_norm DESC''' )
    rows = cur.fetchall()

    # --> streamline shit
    # prepare data for template (tags)
    #
    # [ { 'row': row,
    #     'tags': TAGS }
    #   { 'row: row,
    #     'tags': TAGS } }
    articles = []
    for row in rows:
        d = { 'db': row }
        d['tags'] = extract_tags(row['meta_json'])
        articles.append(d)

    # create article preview
    cur = g.db.execute( '''SELECT body_md
                           FROM entries
                           WHERE id = ?''', (rows[0]['id'],))
    # --> disable sqlite3 row ???
    body_md = cur.fetchone()[0]

    body_md_prev = "\n".join(body_md.split("\n")[:5])

    body_html = pandoc_pipe( body_md_prev,
                             [ '--to=html5',
                               '--filter=rubric_dyn/filter_img_path.py' ] )

    # notes
    g.db.row_factory = sqlite3.Row
    cur = g.db.execute( '''SELECT ref, title, date_norm, meta_json
                           FROM entries
                           WHERE type = 'note'
                           AND pub = 1
                           ORDER BY datetime_norm DESC''' )
    rows = cur.fetchall()

    notes = []
    for row in rows:
        d = { 'db': row }
        notes.append(d)

    return render_template( 'home.html',
                            title = None,
                            articles = articles,
                            article_prev = body_html,
                            notes = notes )

@pages.route('/articles/<path:article_path>/')
def article(article_path):
    '''single article'''

    row = get_entry_by_date_ref_path(article_path, 'article')

    # get previous/next navigation
    page_nav = create_page_nav(row['type'], row['datetime_norm'])

#    # foto exif information
#    if row['exifs_json'] == "":
#        img_exifs_json = False
#
# --> jinja evaluates "" as not defined, as far as I can see...

    return show_post(row, page_nav)

@pages.route('/special/<ref>/')
def special(ref):
    '''special page'''

    return show_post_by_type_ref('special', ref)

@pages.route('/notes/<ref>/')
def show_note(ref):
    '''note page'''

    return show_post_by_type_ref('note', ref)
