'''regular website pages'''
import os
import sqlite3
import json
import hashlib

from flask import Blueprint, render_template, g, request, session, redirect, \
    url_for, abort, flash, current_app

from website_rubric.db_read import get_entry_by_ref, get_entry_by_date_ref, \
    get_cat_by_ref, get_entries_by_cat, get_entries_for_home, get_cat_items, \
    get_listentries_by_cat
from website_rubric.helper_pages import gen_timeline_date_sets, create_page_nav

pages = Blueprint('pages', __name__)

### functions returning a view

def render_final(*args, **kwargs):
    '''final render wrapper
- incl. categories for menu'''
    cat_menuitems = get_cat_items()

    return render_template(*args, **kwargs, cat_menuitems = cat_menuitems)

### routes

### lists / overviews

@pages.route('/')
def home():
    '''the home page,
currently this shows n entries of type blog as timeline w/ preview

alternatively something like a featured entry could be used'''
    n = 5
    pages_rows = get_entries_for_home(n)

    return render_final('home.html',
                        title = 'Home',
                        date_sets = gen_timeline_date_sets(pages_rows))

@pages.route('/<cat_ref>/')
def cat_view(cat_ref):
    '''show n entries from given category as timeline w/ preview'''
    cat_row = get_cat_by_ref(cat_ref)

    n = 5
    pages_rows = get_entries_by_cat(cat_row['id'], n)

    page_nav = { 'type': 'prev',
                 'index_ref': cat_row['ref'] }

    return render_final('timeline.html',
                        title = cat_row['title'],
                        date_sets = gen_timeline_date_sets(pages_rows),
                        page_nav = page_nav)

@pages.route('/<cat_ref>/list/')
def cat_list(cat_ref):
    '''show all entries from given category as list
used to show all entries by clicking on list button
below timeline'''
    cat_row = get_cat_by_ref(cat_ref)

    return render_final('list.html',
                        title = cat_row['title'],
                        cat_ref = cat_row['ref'],
                        pages = get_listentries_by_cat(cat_row['id']))

# evtl. (re-)implement
#
#@pages.route('/timeline/')
#def timeline():
#    '''show all entries as timeline w/ preview'''
#    pass
#
#@pages.route('/history/')
#def history():
#    '''show all history entries'''
#    pass

### page views

@pages.route('/special/<ref>/')
def special(ref):
    '''special pages'''

    row = get_entry_by_ref(ref, 'special')

    return render_final( 'post.html',
                         title = row['title'],
                         page = row,
                         page_nav = None )

@pages.route('/<cat_ref>/<date>/<ref>/')
def entry(cat_ref, date, ref):
    '''single entry'''

    row = get_entry_by_date_ref(date, ref)

    # get previous/next navigation
    page_nav = create_page_nav( row['note_cat_id'],
                                row['date_norm'],
                                row['time_norm'] )

    return render_final( 'post.html',
                         title = row['title'],
                         page = row,
                         page_nav = page_nav )

### login / logout

@pages.route('/login-interface', methods=['GET', 'POST'])
def login():
    '''login page'''
    if session.get('logged_in'):
        return redirect(url_for('interface.overview'))
    error = None

    if request.method == 'POST':
        passwd_str = request.form['password']
        passwd_hash = hashlib.sha1(passwd_str.encode()).hexdigest()

        if request.form['username'] != current_app.config['USERNAME'] \
          or passwd_hash != current_app.config['PASSWD_SHA1']:
            error = "Invalid username or password..."
        else:
            session['logged_in'] = True
            flash('Login successful.')
            return redirect(url_for('interface.overview'))

    return render_template('login.html', error=error, title="")

@pages.route('/logout-interface')
def logout():
    '''logout'''
    session.pop('logged_in', None)
    return redirect(url_for('pages.home'))
