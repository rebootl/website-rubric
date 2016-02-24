import os
import sqlite3
import json
from flask import Blueprint, render_template, g, request, session, redirect, \
    url_for, abort, flash, current_app

pages = Blueprint('pages', __name__)

QUERY_POST_SELECT_FROM = '''SELECT type, ref, title, date_norm,
                             datetime_norm, body_html, data1, exifs_json,
                             meta_json
                            FROM entries
                            '''
QUERY_POST_WHERE = '''WHERE ( type = 'article' OR type = 'imagepage' )
                      '''
QUERY_POST_AND_PUB = '''AND pub = 1
                        '''

QUERY_POST = QUERY_POST_SELECT_FROM + \
             QUERY_POST_WHERE + \
             QUERY_POST_AND_PUB

@pages.route('/')
def home():

    if current_app.config['HOME_SHOWS'] == 'latest':
        # show the latest post by date
        g.db.row_factory = sqlite3.Row
        cur = g.db.execute( QUERY_POST +
                            '''ORDER BY datetime_norm DESC LIMIT 1''')
        row = cur.fetchone()

    elif current_app.config['HOME_SHOWS'] == 'latest_id':
        # show the latest post by id
        g.db.row_factory = sqlite3.Row
        cur = g.db.execute( QUERY_POST +
                            '''ORDER BY id DESC LIMIT 1''')
        row = cur.fetchone()

    else:
        # show post id set in config
        id = current_app.config['HOME_SHOWS']
        g.db.row_factory = sqlite3.Row
        cur = g.db.execute( QUERY_POST +
                            '''AND id = ?''', (id,))
        row = cur.fetchone()

    return render_post(row['ref'], row)

#@pages.route('/test')
#def test():
#    g.db.row_factory = sqlite3.Row
#    cur = g.db.execute("select * from entries limit 1")
#    row = cur.fetchone()
#
#    return row['body_html']

@pages.route('/index/')
def index():
    # shows a list of posts (articles and imagepages),
    # grouped by date
    cur = g.db.execute('''SELECT type, ref, title, date_norm, data1 
                          FROM entries
                          WHERE ( type = 'article' OR type = 'imagepage' )
                          AND pub = 1
                          ORDER BY datetime_norm DESC, title ASC''')

    entries = [ dict( type = row[0],
                      ref = row[1],
                      title = row[2],
                      date = row[3],
                      data = row[4] ) for row in cur.fetchall() ]

    # generate items
    date_items = []

    last_date = ""
    for entry in entries:
        # set imagepage thumbs
        if entry['type'] == "imagepage":
            thumb_filename = os.path.splitext(entry['data'])[0] + '_thumb.png'
            entry['thumb_src'] = os.path.join('/media', thumb_filename)

        # set link href
        entry['href'] = os.path.join(entry['date'], entry['ref'])

        # construct list
        date = entry['date']
        if date != last_date:
            date_item = { 'date': date, 'entries': [ entry ] }
            date_items.append(date_item)
        else:
            date_items[-1]['entries'].append(entry)
        last_date = date

    title = "Index"
    return render_template( 'entries_index.html',
                            title=title,
                            date_items=date_items )

@pages.route('/about/')
def about():
    # --> make function for special pages ?
    g.db.row_factory = sqlite3.Row
    cur = g.db.execute( QUERY_POST_SELECT_FROM + \
                        '''WHERE ref = ?''', ('about',))
    row = cur.fetchone()

    page_nav = { 'prev_href': url_for('pages.about'),
                 'prev_inactive_class': "inactive",
                 'next_href': url_for('pages.about'),
                 'next_inactive_class': "inactive" }

    return render_template( 'post.html',
                            type = row['type'],
                            title = row['title'],
                            body_html = row['body_html'],
                            page_nav = page_nav )

@pages.route('/post/<path:post_ref>/')
def show_post(post_ref):

    post_date, post_ref = os.path.split(post_ref)

    g.db.row_factory = sqlite3.Row
    cur = g.db.execute( QUERY_POST_SELECT_FROM + \
                        '''WHERE date_norm = ?
                           AND ref = ?
                           AND pub = 1''', (post_date, post_ref))
    row = cur.fetchone()

    # (catch not found !!!)
    if row is not None:
        return render_post(post_ref, row)
    else:
        abort(404)

def render_post(ref, row):
    # row: type, title, date_norm, datetime_norm, body_html, data1

    # set imagepage specifics
    if row['type'] == "imagepage":
        img_src = os.path.join("/media", row['data1'])
        article_class = "imagepage"
    else:
        img_src = ""
        article_class = ""

    if row['exifs_json'] == "":
        img_exifs_json = False

    # get previous and next pages for navigation
    page_nav = get_page_nav(row['datetime_norm'], row['date_norm'], ref)

    # get tags
    meta = json.loads(row['meta_json'])
    if 'tags' in meta.keys():
        tags = meta['tags']
    else:
        tags = None

    return render_template( 'post.html',
                            type = row['type'],
                            title = row['title'],
                            date = row['date_norm'],
                            body_html = row['body_html'],
                            article_class = article_class,
                            img_src = img_src,
                            page_nav = page_nav,
                            img_exifs_json = row['exifs_json'],
                            tags = tags )

QUERY_PAGE_NAV = '''SELECT date_norm, ref
                    FROM entries
                    WHERE date_norm IS NOT 'ERRONEOUS_DATE'
                    AND ( type = 'article' OR type = 'imagepage' )
                    AND pub = 1
                    '''

def get_page_nav(datetime_norm, post_date, post_ref):
    # get previous page
    # and create new page_nav list
    cur = g.db.execute( QUERY_PAGE_NAV + \
                        '''AND datetime_norm < ?
                           ORDER BY datetime_norm DESC LIMIT 1''', (datetime_norm,))
    prev_result = cur.fetchone()
    if prev_result is not None:
        prev_date = prev_result[0]
        prev_ref = prev_result[1]
        page_nav = { 'prev_href': os.path.join('/post', prev_date, prev_ref) }
    else:
        page_nav = { 'prev_href': os.path.join('/post', post_date, post_ref),
                     'prev_inactive_class': "inactive" }

    # get next page
    # and fill in page_nav list
    cur = g.db.execute( QUERY_PAGE_NAV + \
                        '''AND datetime_norm > ?
                           ORDER BY datetime_norm ASC LIMIT 1''', (datetime_norm,))
    next_result = cur.fetchone()
    if next_result is not None:
        next_date = next_result[0]
        next_ref = next_result[1]
        page_nav['next_href'] = os.path.join('/post', next_date, next_ref)
    else:
        page_nav['next_href'] = os.path.join('/post', post_date, post_ref)
        page_nav['next_inactive_class'] = "inactive"

    return page_nav
