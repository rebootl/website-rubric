#!/usr/bin/python

from flask_frozen import Freezer
import subprocess

from rubric_dyn import app
import config

#freezer = Freezer(app)

#app.config['FREEZER_IGNORE_ENDPOINTS'] = ['endpoint1', 'endpoint2']
app.config['FREEZER_IGNORE_ENDPOINTS'] = [ 'interface.edit',
                                           'interface.overview',
                                           'interface.login',
                                           'interface.new',
                                           'interface.pub',
                                           'interface.unpub',
                                           'interface.download_text',
                                           'interface.recreate_exifs' ]

# This is a copy of Freezer.no_argument_rules() modified to ignore certain paths
def no_argument_rules_urls_with_ignore():
    """URL generator for URL rules that take no arguments."""
    ignored = app.config.get('FREEZER_IGNORE_ENDPOINTS', [])
    for rule in app.url_map.iter_rules():
        if rule.endpoint not in ignored and not rule.arguments \
         and 'GET' in rule.methods:
            yield rule.endpoint, {}

freezer = Freezer(app=app, with_no_argument_rules=False)
freezer.register_generator(no_argument_rules_urls_with_ignore)

def copy_folder(in_dir, dest_dir):
    cp_command = ['cp', '-ur', in_dir, dest_dir]
    exitcode = subprocess.call(cp_command)

if __name__ == '__main__':
    freezer.freeze()
    copy_folder(config.MEDIA_DIR, 'rubric_dyn/build/')

#    freezer.run(debug=True)
