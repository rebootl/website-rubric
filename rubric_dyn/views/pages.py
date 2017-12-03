'''regular website pages'''
import os
import sqlite3
import json

from flask import Blueprint, render_template, g, request, session, redirect, \
    url_for, abort, flash, current_app

from rubric_dyn.common import gen_hrefs, get_feat
from rubric_dyn.db_read import get_entry_by_ref, get_entrylist, \
    get_entrylist_limit, get_changelog_limit, get_changelog, \
    get_entry_by_date_ref, get_cat_by_ref, get_entries_by_cat, \
    get_entries_for_home, get_cat_items
from rubric_dyn.helper_pages import create_page_nav, gen_changelog

pages = Blueprint('pages', __name__)


### helper

def gen_timeline_date_sets(pages_rows):
    '''generate timeline entries'''
    # create list (--> use list sqlite.Row instead ???)
    pages = []
    for page_row in pages_rows:
        page = dict(page_row)

        # limit page length
        #  more than three paragraphs
        if page['body_html'].count('</p>') > 3:
            body_html_cut = "</p>".join(page['body_html'].split("</p>", 3)[:3])
            page['body_html'] = body_html_cut
            page['cut'] = True
        # --> more than one image
        #elif ...

        pages.append(page)

    date_sets = []
    last_date = ""
    for page in pages_rows:
        curr_date = page['date_norm']
        if curr_date != last_date:
            date_set = { 'date': curr_date,
                         'pages': [] }
            date_sets.append(date_set)
            last_date = curr_date

    # add the changes to the sets
    for date_set in date_sets:
        for page in pages:
            if page['date_norm'] == date_set['date']:
                date_set['pages'].append(page)

    return date_sets

### functions returning a view
# ...

def render_catmenu(*args, **kwargs):
    '''render wrapper incl. the menu'''
    cat_menuitems = get_cat_items()

    return render_template(*args, **kwargs, cat_menuitems = cat_menuitems)

def render_timeline(title, pages_rows):
    '''render a timeline view'''

    hrefs = gen_hrefs(pages_rows)
    date_sets = gen_timeline_date_sets(pages_rows)

    return render_catmenu( 'timeline.html',
                            title = title,
                            date_sets = date_sets,
                            hrefs = hrefs )

### routes

### lists / overviews

@pages.route('/')
def home():
    '''the home page'''

    # (use feat. entry here instead if wanted)
    n = 5
    pages_rows = get_entries_for_home(n)

    return render_timeline('Home', pages_rows)

@pages.route('/<cat_ref>/')
def cat_view(cat_ref):
    '''show entries from category as timeline w/ preview'''

    cat_row = get_cat_by_ref(cat_ref)

    # --> get n entries from cat.
    n = 5
    pages_rows = get_entries_by_cat(cat_row['id'], n)

    return render_timeline(cat_row['title'], pages_rows)

@pages.route('/<cat_ref>/list/')
def cat_list(cat_ref):
    return "FOOO"

# --> not used atm...
# --> maybe reuse later, but using above func.s
#@pages.route('/timeline/')
#def timeline():
#    '''show all entries as timeline w/ preview'''
#
#    # (number of entries to show)
#    n = 30
#
#    g.db.row_factory = sqlite3.Row
#    cur = g.db.execute('''SELECT id, ref, type, title,
#                           date_norm, time_norm, body_html, tags
#                          FROM entries
#                          WHERE type = 'note'
#                           AND pub = 1
#                          ORDER BY date_norm DESC, time_norm DESC
#                          LIMIT ?''', (n,))
#    pages_rows = cur.fetchall()
#
#    hrefs = gen_hrefs(pages_rows)
#
#    date_sets = gen_timeline_date_sets(pages_rows)
#
#    return render_template( 'timeline.html',
#                            title = 'Timeline',
#                            date_sets = date_sets,
#                            hrefs = hrefs )

# --> reimplement using above functions / template etc.
#@pages.route('/history/')
#def history():
#    '''show all history entries'''
#    # get entries
#    rows = get_entrylist('history')
#
#    return render_template( 'history.html',
#                            title = 'Page history',
#                            history = rows )

### individual pages

@pages.route('/special/<ref>/')
def special(ref):
    '''special pages'''

    row = get_entry_by_ref(ref, 'special')

    return render_template( 'post.html',
                            title = row['title'],
                            page = row,
                            page_nav = None )

@pages.route('/<cat_ref>/<date>/<ref>/')
def entry(cat_ref, date, ref):
    '''single entry'''

    row = get_entry_by_date_ref(date, ref)

    # get previous/next navigation
    page_nav = create_page_nav( row['id'],
                                row['type'] )

    return render_template( 'post.html',
                            title = row['title'],
                            page = row,
                            page_nav = page_nav )
