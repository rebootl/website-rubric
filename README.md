This is basically the underlaying system I use to manage my little personal website.

The website is live at: <http://reboot.li>  

It's basically a self written "micro-cms" based on python-flask (the micro-framework) and I named it __rubric-dyn__.

Please feel free to explore this and use for reference. But please don't use this to simply create a copy of my website.

Note that currently this is not licensed and as such should be considered copyright protected.  
Though I may release it under GPL...

Thanks :)

## Basic Setup

### Prerequisites

- python (v3)
- python-flask
- sqlite3
- pandoc (markdown conversion)
- python-pillow (for image-processing)

### DB

Create new db:

    $ sqlite3 website.db < schema.sql

### Config

Copy `config-example.py` to `config.py` and adapt settings.

### Build-in flask Development Server

run `server.py`

starts server on port 5000

interface login via: http://<host>:5000/interface/



## Production environment setup / Deployment (example)

Below steps were done on Arch Linux.
Apache config. details etc. varies for diff. distributions.

refs:

- http://flask.pocoo.org/docs/0.12/deploying/mod_wsgi/
- https://wiki.archlinux.org/index.php/Apache_HTTP_Server
- https://modwsgi.readthedocs.io/en/develop/user-guides.html

### Apache Setup

uncomment in httpd.conf:

activate SSL:

    LoadModule socache_shmcb_module modules/mod_socache_shmcb.so
    LoadModule ssl_module modules/mod_ssl.so
    Include conf/extra/httpd-ssl.conf

for SSL to work obv. more steps are req.

use vhosts:

    # vhosts
    Include conf/extra/httpd-vhosts.conf

wsgi:

    # wsgi
    LoadModule wsgi_module modules/mod_wsgi.so
    LogLevel info

virtual host config:

~~~
Listen 80xx
<VirtualHost *:80xx>
    ServerAdmin admin@server.org
    ServerName foo.server.org

    WSGIDaemonProcess mywebsite threads=5
    WSGIScriptAlias / /srv/wsgi/website-rubric/website_rubric.wsgi

    <Directory /srv/wsgi/website-rubric>
        WSGIProcessGroup mywebsite
        WSGIApplicationGroup %{GLOBAL}
        WSGIScriptReloading On
        Require all granted
    </Directory>

    ErrorLog "/var/log/httpd/foo.server.org-error_log"
    CustomLog "/var/log/httpd/foo.server.org-access_log" common
</VirtualHost>
~~~

This setup uses a separate wsgi directory outside of the default
apache webroot /srv/www/ for additional security/benefits.

### Application files

Copy/clone files into /srv/wsgi/website-rubric.

Create wsgi entry file, website_rubric.wsgi:

 import sys
 sys.path.insert(0, '/srv/wsgi/website-rubric')

 from website_rubric import app as application

Adapt config.

Create/copy database outside of web directories.

Evtl. copy media files etc.

For image upload through the backend the webserver will need write
permission on images and thumbs under website_rubric/media.

With this setup, everything (media files etc.) is served through the wsgi app.

Alternatively apache could be setup to serve the media files directly. --> ToDo
