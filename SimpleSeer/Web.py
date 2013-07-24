import os
import sys
import logging
import time

import mongoengine
from flask import Flask
from socketio.server import SocketIOServer

from . import models as M

from . import views
from . import crud
from . import util
from .Session import Session
from path import path

import pkg_resources
    

DEBUG = True

log = logging.getLogger(__name__)

from flask.ext.login import (LoginManager, current_user, login_required,
                            login_user, logout_user, UserMixin, AnonymousUser,
                            confirm_login, fresh_login_required)
class User(UserMixin):
    def __init__(self, name, id, password=None,active=True):
        self.name = name
        self.id = id
        self.password = password
        self.active = active

    def is_active(self):
        return self.active


class Anonymous(AnonymousUser):
    name = u"Anonymous"


appauth = False
session = Session()

timestamp = time.time()
USERS = {1: User(str(timestamp), int(timestamp), str(timestamp), False)}

if session.login:
  USERS = {
      1: User(session.login['username'], 1, session.login['password']),
  }

USER_NAMES = dict((u.name, u) for u in USERS.itervalues())
login_manager = LoginManager()
login_manager.anonymous_user = Anonymous
login_manager.login_view = "login"
login_manager.login_message = u"Please log in to access this page."
login_manager.refresh_view = "reauth"

@login_manager.user_loader
def load_user(id):
    return USERS.get(int(id))

app = Flask(__name__)  
DEBUG = True
app.config.from_object(__name__)

def make_app():
    settings = Session()
    tpath = path("{0}/{1}".format(settings.get_config()['web']['static']['/'], '../templates')).abspath()
    print "Setting template path to {0}".format(tpath)
    template_folder=tpath

    app = Flask(__name__,template_folder=template_folder)


    app.secret_key = 'secretkey'
    login_manager.setup_app(app)
      
    @app.teardown_request
    def teardown_request(exception):
        conn = mongoengine.connection.get_connection()
        conn.end_request()

    views.route.register_routes(app)
    crud.register(app)
    
    for ep in pkg_resources.iter_entry_points('seer.views'):
        mod = __import__(ep.module_name, globals(), locals(), [ep.name])
        getattr(mod, ep.attrs[0]).register_web(app)
    
    return app
        

class WebServer(object):
    """
    This is the abstract web interface to handle event callbacks for Seer
    all it does is basically fire up a webserver to allow you
    to start interacting with Seer via a web interface
    """
    
    web_interface = None
    port = 8000 
    
    def __init__(self, app):
        self.app = app
        session = Session()
        if app.config['DEBUG'] or DEBUG:
            from werkzeug import SharedDataMiddleware
            app.wsgi_app = SharedDataMiddleware(app.wsgi_app, session.web['static'])
        hostport = Session().web["address"].split(":")
        if len(hostport) == 2:
            host, port = hostport
            port = int(port)
        else:
            host, port = hostport, 80
        self.host, self.port = host, port

    def run_gevent_server(self):
        server = SocketIOServer(
            (self.host, self.port),
            self.app, namespace='socket.io',
            policy_server=False)
        log.info('Web server running on %s:%s', self.host, self.port)
        server.serve_forever()
        

