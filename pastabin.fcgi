#!/usr/bin/python

from pastabin import app
from flup.server.fcgi import WSGIServer

WSGIServer(app, debug=False).run()
