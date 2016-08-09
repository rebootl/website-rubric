'''regular website pages'''
import os
import sqlite3
import json

from flask import Blueprint, render_template, g, request, session, redirect, \
    url_for, abort, flash, current_app

from rubric_dyn.common import pandoc_pipe
from rubric_dyn.db_read import get_entry_by_date_ref_path, get_entry_by_ref, \
    get_entrylist, get_entrylist_limit
from rubric_dyn.helper_pages import create_page_nav

from rubric_dyn.helper_interface import process_input

pages = Blueprint('pages', __name__)

PAGE_NAV_DEFAULT = { 'prev_href': None,
                     'next_href': None,
                     'index': "/" }

### functions returning a view

# --> deprecated
#def show_post(page, page_nav=PAGE_NAV_DEFAULT):
#    '''show post
#currently used for entry types:
#- article
#- special
#- note
#'''
    # title and img_exifs_json are separate because they are used
    # in parent template
    # --> is this really necessary ??
    # ==> for title it may make sense, so it can be set separately
    #     - page.title  used on the page
    #     - title       used as "browser title"
    #     (could be used e.g. by interface/edit
    # (==> img_exifs_json is not used anymore)
#    return render_template( 'post.html',
#                            title = page['title'],
#                            page = page,
#                            page_nav = page_nav )

### routes

### individually adapted pages

@pages.route('/')
def home():
    '''the home page'''

    # latest
    latest_rows = get_entrylist_limit( 'latest',
                                       current_app.config['NUM_LATEST_ON_HOME'] )

    # page history
    history_rows = get_entrylist_limit( 'history',
                                        current_app.config['NUM_HISTORY_ON_HOME'] )

    return render_template( 'home.html',
                            title = 'Home',
                            latest = latest_rows,
                            history = history_rows )

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

@pages.route('/articles/')
def articles():
    '''articles list/overview'''

    # get a list of articles
    g.db.row_factory = sqlite3.Row
    cur = g.db.execute( '''SELECT id, ref, title, date_norm, tags
                           FROM entries
                           WHERE type = 'article'
                           AND pub = 1
                           ORDER BY date_norm DESC, time_norm DESC''' )
    articles_rows = cur.fetchall()

    # create article preview
    # --> currently not used
    if articles_rows != []:
        cur = g.db.execute( '''SELECT body_md
                               FROM entries
                               WHERE id = ?''', (articles_rows[0]['id'],))
        # --> disable sqlite3 row ???
        latest_body_md = cur.fetchone()[0]

        latest_body_md_prev = "\n".join(latest_body_md.split("\n")[:5])

        #body_html = pandoc_pipe( body_md_prev,
        #                         [ '--to=html5' ] )
        prev_ref, \
        prev_body_html_subst = process_input("", latest_body_md_prev)
    else:
        prev_body_html_subst = None

#    return str(articles_rows)
    return render_template( 'articles.html',
                            title = 'Articles',
                            articles = articles_rows,
                            article_prev = prev_body_html_subst )

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

@pages.route('/latest/')
def latest():
    '''show all latest entries'''
    # get entries
    rows = get_entrylist('latest')

    return render_template( 'latest.html',
                            title = 'Latest',
                            latest = rows )

@pages.route('/history/')
def history():
    '''show all history entries'''
    # get entries
    rows = get_entrylist('history')

    return render_template( 'history.html',
                            title = 'Page history',
                            history = rows )

### individual pages

@pages.route('/articles/<path:article_path>/')
def article(article_path):
    '''single article'''

    row = get_entry_by_date_ref_path(article_path, 'article')

    # get previous/next navigation
    page_nav = create_page_nav( row['id'],
                                row['type'] )

    #return show_post(row, page_nav)
    return render_template( 'post.html',
                            title = row['title'],
                            page = row,
                            page_nav = page_nav )

@pages.route('/notes/<ref>/')
def show_note(ref):
    '''note pages'''

    row = get_entry_by_ref(ref, 'note')

    page_nav = { 'prev_href': None,
                 'next_href': None,
                 'index': "/notes/" }

    return render_template( 'post.html',
                            title = row['title'],
                            page = row,
                            page_nav = page_nav )

@pages.route('/special/<ref>/')
def special(ref):
    '''special pages'''

    row = get_entry_by_ref(ref, 'special')

    return render_template( 'post.html',
                            title = row['title'],
                            page = row,
                            page_nav = None )
