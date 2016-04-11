import os
import sqlite3
import json
from flask import Blueprint, render_template, g, request, session, redirect, \
    url_for, abort, flash, current_app
from rubric_dyn.common import pandoc_pipe

pages = Blueprint('pages', __name__)


#def get_entry_by_id(id):
#    '''return entry data from database'''
#    g.db.row_factory = sqlite3.Row
#    cur = g.db.execute( '''SELECT type, ref, title, date_norm,
#                            datetime_norm, body_html, data1, exifs_json,
#                            meta_json
#                           FROM entries
#                           WHERE id = ?''', (id,))
#    return cur.fetchone()

def get_entry_by_date_ref_path(date_ref_path, type, published=True):
    '''return entry data from db, by <date>/<ref> path'''

    date, ref = os.path.split(date_ref_path)

    if published == True:
        pub = 1
    else:
        pub = 0

    g.db.row_factory = sqlite3.Row
    cur = g.db.execute( '''SELECT type, ref, title, date_norm,
                            datetime_norm, body_html, data1, exifs_json,
                            meta_json
                           FROM entries
                           WHERE date_norm = ?
                           AND ref = ?
                           AND type = ?
                           AND pub = ?''', (date, ref, type, pub))
    row = cur.fetchone()
    # (catch not found !!!)
    if row is None:
        abort(404)

    return row

def get_entry_by_ref(ref, type, published=True):
    '''return entry data from db, by ref'''

    if published == True:
        pub = 1
    else:
        pub = 0

    g.db.row_factory = sqlite3.Row
    cur = g.db.execute( '''SELECT type, ref, title, date_norm,
                            datetime_norm, body_html, data1, exifs_json,
                            meta_json
                           FROM entries
                           WHERE ref = ?
                           AND type = ?
                           AND pub = ?''', (ref, type, pub))
    row = cur.fetchone()
    # (catch not found !!!)
    if row is None:
        abort(404)

    return row

def get_page_nav(curr_type, curr_datetime_norm):
    '''create previous/next navigation for posts (using same type)'''

    q_begin = '''SELECT date_norm, ref
                 FROM entries
                 WHERE date_norm IS NOT 'ERRONEOUS_DATE'
                 AND ( type = ? )
                 AND pub = 1
                 '''

    # get previous page
    # and create new page_nav list
    cur = g.db.execute( q_begin + \
                        '''AND datetime_norm < ?
                           ORDER BY datetime_norm DESC LIMIT 1''',
                           (curr_type, curr_datetime_norm) )
    prev_result = cur.fetchone()

    if curr_type == 'article':
        type_subpath = "/articles"

    if prev_result is not None:
        prev_date = prev_result[0]
        prev_ref = prev_result[1]
        page_nav = { 'prev_href': os.path.join(type_subpath, prev_date, prev_ref) }
    else:
        page_nav = { 'prev_href': None }

    # get next page
    # and fill in page_nav list
    cur = g.db.execute( q_begin + \
                        '''AND datetime_norm > ?
                           ORDER BY datetime_norm ASC LIMIT 1''',
                           (curr_type, curr_datetime_norm) )
    next_result = cur.fetchone()

    if next_result is not None:
        next_date = next_result[0]
        next_ref = next_result[1]
        page_nav['next_href'] = os.path.join(type_subpath, next_date, next_ref)
    else:
        page_nav['next_href'] = None

    return page_nav

def extract_tags(meta_json):
    '''extract tags from json'''
    meta = json.loads(meta_json)
    if 'tags' in meta.keys():
        return meta['tags']
    else:
        return None

def show_page_by_type_ref(type, ref):
    '''show an entry by type, ref
currently used for types: special and note'''
    row = get_entry_by_ref(ref, type)

    # set tags
    entry = { 'db': row }
    entry['tags'] = extract_tags(row['meta_json'])

    page_nav = { 'prev_href': None,
                 'next_href': None }

    return render_template( 'article.html',
                            title = entry['db']['title'],
                            entry = entry,
                            page_nav = page_nav,
                            img_exifs_json = entry['db']['exifs_json'] )

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

    # imagepages

#    g.db.row_factory = sqlite3.Row
#    cur = g.db.execute( '''SELECT id, ref, title, date_norm, meta_json, data1
#                           FROM entries
#                           WHERE type = 'imagepage'
#                           AND pub = 1
#                           ORDER BY datetime_norm DESC''' )
#    rows = cur.fetchall()
#
#    imagepages = []
#    for row in rows:
#        d = { 'db': row }
#
#        # set imagepage thumbs
#        thumb_filename = os.path.splitext(row['data1'])[0] + '_thumb.png'
#        d['thumb_src'] = os.path.join('/media', thumb_filename)
#
#        # set link href
#        d['href'] = os.path.join(row['date_norm'], row['ref'])
#        imagepages.append(d)

    return render_template( 'home.html',
                            title = None,
                            articles = articles,
                            article_prev = body_html,
                            notes = notes )

@pages.route('/articles/<path:article_path>/')
def article(article_path):
    '''single article'''

    row = get_entry_by_date_ref_path(article_path, 'article')

    # set tags
    entry = { 'db': row }
    entry['tags'] = extract_tags(row['meta_json'])

    # get previous/next navigation
    page_nav = get_page_nav(row['type'], row['datetime_norm'])

#    # foto exif information
#    if row['exifs_json'] == "":
#        img_exifs_json = False
#
# --> jinja evaluates "" as not defined, as far as I can see...

    return render_template( 'article.html',
                            title = entry['db']['title'],
                            entry = entry,
                            page_nav = page_nav,
                            img_exifs_json = entry['db']['exifs_json'] )

#@pages.route('/index/')
#def index():
#    # shows a list of posts (articles and imagepages),
#    # grouped by date
#    cur = g.db.execute('''SELECT type, ref, title, date_norm, data1 
#                          FROM entries
#                          WHERE ( type = 'article' OR type = 'imagepage' )
#                          AND pub = 1
#                          ORDER BY datetime_norm DESC, title ASC''')
#
#    entries = [ dict( type = row[0],
#                      ref = row[1],
#                      title = row[2],
#                      date = row[3],
#                      data = row[4] ) for row in cur.fetchall() ]
#
#    # generate items
#    date_items = []
#
#    last_date = ""
#    for entry in entries:
#        # set imagepage thumbs
#        if entry['type'] == "imagepage":
#            thumb_filename = os.path.splitext(entry['data'])[0] + '_thumb.png'
#            entry['thumb_src'] = os.path.join('/media', thumb_filename)
#
#        # set link href
#        entry['href'] = os.path.join(entry['date'], entry['ref'])
#
#        # construct list
#        date = entry['date']
#        if date != last_date:
#            date_item = { 'date': date, 'entries': [ entry ] }
#            date_items.append(date_item)
#        else:
#            date_items[-1]['entries'].append(entry)
#        last_date = date
#
#    title = "Index"
#    return render_template( 'entries_index.html',
#                            title=title,
#                            date_items=date_items )

@pages.route('/special/<ref>/')
def special(ref):
    '''special page'''

    return show_page_by_type_ref('special', ref)

@pages.route('/notes/<ref>/')
def show_note(ref):
    '''note page'''

    return show_page_by_type_ref('note', ref)

#@pages.route('/post/<path:post_path>/')
#def show_post(post_path):
#
#    post_date, post_ref = os.path.split(post_path)
#
#    g.db.row_factory = sqlite3.Row
#    cur = g.db.execute( QUERY_POST_SELECT_FROM + \
#                        '''WHERE date_norm = ?
#                           AND ref = ?
#                           AND pub = 1''', (post_date, post_ref))
#    row = cur.fetchone()
#
#    # (catch not found !!!)
#    if row is not None:
#        return render_post(post_ref, row)
#    else:
#        abort(404)
