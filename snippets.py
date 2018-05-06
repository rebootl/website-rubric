#!/usr/bin/python (only for syntax highlight)
#
# examples from tutorial

# config
# overwrite config from environment example
app.config.from_envvar('FLASKR_SETTINGS', silent=True)

# blueprint
#
simple_page = Blueprint('simple_page', __name__,
                        template_folder='templates')

@simple_page.route('/', defaults={'page': 'index'})
@simple_page.route('/<page>')
def show(page):
    try:
        return render_template('pages/%s.html' % page)
    except TemplateNotFound:
        abort(404)


# restrict all views example
# --> login needs to be adapted for this so that login is possible
@interface.before_request
def restrict_access():
    if not session.get('logged_in'):
        abort(401)


# general backend stuff
#
@app.route('/add', methods=['POST'])
def add_entry():
    if not session.get('logged_in'):
        abort(401)
    g.db.execute('insert into entries (title, text) values (?, ?)',
                 [request.form['title'], request.form['text']])
    g.db.commit()
    flash('New entry was successfully posted')
    return redirect(url_for('show_entries'))

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    flash('You were logged out')
    return redirect(url_for('show_entries')
