'''regular website pages'''
import os
import sqlite3
import json

from flask import Blueprint, render_template, g, request, session, redirect, \
    url_for, abort, flash, current_app

from rubric_dyn.common import gen_hrefs, get_feat
from rubric_dyn.db_read import get_entry_by_ref, get_entrylist, \
    get_entrylist_limit, get_changelog_limit, get_changelog, \
    get_entry_by_date_ref
from rubric_dyn.helper_pages import create_page_nav, gen_changelog

pages = Blueprint('pages', __name__)

# --> not needed atm., move to config anyway...
PAGE_NAV_DEFAULT = { 'prev_href': None,
                     'next_href': None,
                     'index': "/" }

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

### routes

### individually adapted pages

@pages.route('/')
def home():
    '''the home page'''

    #feat_id = get_feat()
    n = 5

    g.db.row_factory = sqlite3.Row
    cur = g.db.execute('''SELECT id, ref, type, title,
                           date_norm, time_norm, body_html, tags
                          FROM entries
                          WHERE type = 'blog'
                           AND pub = 1
                          ORDER BY date_norm DESC, time_norm DESC
                          LIMIT ?''', (n,))
    pages_rows = cur.fetchall()
    if pages_rows == None:
        abort(404)

    # --> move into the timeline entries...????
    hrefs = gen_hrefs(pages_rows)

    date_sets = gen_timeline_date_sets(pages_rows)

    return render_template( 'home.html',
                            title = 'Home',
                            date_sets = date_sets,
                            hrefs = hrefs )

# --> not used atm...
#
@pages.route('/timeline/')
def timeline():
    '''generate timeline'''
    # (number of entries to show)
    n = 30

    g.db.row_factory = sqlite3.Row
    cur = g.db.execute('''SELECT id, ref, type, title,
                           date_norm, time_norm, body_html, tags
                          FROM entries
                          WHERE type = 'note'
                           AND pub = 1
                          ORDER BY date_norm DESC, time_norm DESC
                          LIMIT ?''', (n,))
    pages_rows = cur.fetchall()

    hrefs = gen_hrefs(pages_rows)

    date_sets = gen_timeline_date_sets(pages_rows)

    return render_template( 'timeline.html',
                            title = 'Timeline',
                            date_sets = date_sets,
                            hrefs = hrefs )

# --> why is this separate actually ?
# ==> cause of page history integrated...
@pages.route('/special/about/')
def about():
    '''about page'''
    row = get_entry_by_ref('about', 'special')

    # page history
    history_rows = get_entrylist_limit( 'history',
                                        current_app.config['NUM_HISTORY_ON_HOME'] )

    return render_template( 'about.html',
                            title = row['title'],
                            page = row,
                            history = history_rows,
                            page_nav = None )

### lists / overviews

@pages.route('/blog/')
def blog():
    '''list of blog entries'''
    g.db.row_factory = sqlite3.Row
    cur = g.db.execute( '''SELECT ref, title, date_norm, tags
                           FROM entries
                           WHERE type = 'blog'
                           AND pub = 1
                           ORDER BY date_norm DESC, time_norm DESC''' )
    blog_rows = cur.fetchall()

    return render_template( 'blog.html',
                            title = 'Blog',
                            blogentries = blog_rows )

@pages.route('/notes/')
def notes():
    '''list of notes'''
    g.db.row_factory = sqlite3.Row
    cur = g.db.execute( '''SELECT ref, title, date_norm
                           FROM entries
                           WHERE type = 'note'
                           AND pub = 1
                           ORDER BY date_norm DESC, time_norm DESC''' )
    notes_rows = cur.fetchall()

    return render_template( 'notes.html',
                            title = 'Notes',
                            notes = notes_rows )

@pages.route('/history/')
def history():
    '''show all history entries'''
    # get entries
    rows = get_entrylist('history')

    return render_template( 'history.html',
                            title = 'Page history',
                            history = rows )

# --> merge w/ timeline...
@pages.route('/changelog/')
def changelog():
    '''show all changelog entries'''
    # get entries
    change_rows = get_changelog()

    # get list ordered by dates
    date_sets = gen_changelog(change_rows)

    return render_template( 'changelog.html',
                            title = 'Latest/Changelog',
                            date_sets = date_sets )

# --> don't use this atm...
@pages.route('/categorized/')
def categorized():
    '''create a categorized overview'''

    g.db.row_factory = sqlite3.Row
    cur = g.db.execute( '''SELECT id, title, tags
                           FROM categories
                           ORDER BY title ASC''' )
    topics_rows = cur.fetchall()

    # select all pages (entries)
    cur = g.db.execute( '''SELECT id, ref, title, type, date_norm, tags
                           FROM entries
                           WHERE pub = 1
                           AND type IS NOT 'history'
                           ORDER BY date_norm DESC, time_norm DESC''' )
    pages_rows = cur.fetchall()

    # generate hrefs
    hrefs = gen_hrefs(pages_rows)

    # auto-magically categorize pages by tags
    topics = []
    unsorted = []
    for topic in topics_rows:
        topic_item = { 'id': topic['id'],
                       'title': topic['title'],
                       'tags': topic['tags'],   
                       'pages': [] }
        for page in pages_rows:
            #pass
            # comprehension
            if len(set(map(str.strip, topic['tags'].split(','))).intersection(map(str.strip, page['tags'].split(',')))) > 0:
                # match found
                topic_item['pages'].append(page)
        topics.append(topic_item)

    # find unsorted
    all_tags = []
    for topic in topics_rows:
        all_tags.extend(list(map(str.strip, topic['tags'].split(','))))

    unsorted = []
    for page in pages_rows:
        if len(set(map(str.strip, page['tags'].split(','))).intersection(all_tags)) == 0:
            unsorted.append(page)

    topics.append( { 'id': None,
                     'title': "Unsorted",
                     'tags': [],
                     'pages': unsorted } )

    return render_template( 'topics.html',
                            title = "Categorized",
                            topics = topics,
                            hrefs = hrefs )

### individual pages

@pages.route('/special/<ref>/')
def special(ref):
    '''special pages'''

    row = get_entry_by_ref(ref, 'special')

    return render_template( 'post.html',
                            title = row['title'],
                            page = row,
                            page_nav = None )

@pages.route('/<prefix>/<date>/<ref>/')
def entry(prefix, date, ref):
    '''single entry'''

    row = get_entry_by_date_ref(date, ref)

    # get previous/next navigation
    page_nav = create_page_nav( row['id'],
                                row['type'] )

    return render_template( 'post.html',
                            title = row['title'],
                            page = row,
                            page_nav = page_nav )
