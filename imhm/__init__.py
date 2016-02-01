# -*- coding:utf-8 -*-
__author__ = 'ery'

try:
    import gevent.monkey
    gevent.monkey.patch_all()
except Exception, e:
    pass

import datetime

from flask import Flask, session, escape, jsonify
from flask.ext.cache import Cache
# from flask.ext.session import Session

from imhm.tools import CustomRedisSession
from imhm.config import flask_config, redis_server_settings, flask_cache_configs

app = Flask(__name__)
flask_session_obj = CustomRedisSession(app, redis_server_settings["Session"])
cache = Cache(app, config=flask_cache_configs["Redis"])


def create_app():
    # OPERATION_MODE = "development"
    OPERATION_MODE = "production"
    app.config.from_object(flask_config[OPERATION_MODE])
    flask_config[OPERATION_MODE].init_app(app)

    app.config["SESSION_TYPE"] = flask_config[OPERATION_MODE].SESSION_TYPE
    app.config["PERMANENT_SESSION_LIFETIME"] = datetime.timedelta(seconds=7200)

    from imhm.controllers import (management_bp, search_bp, music_bp)

    # register blueprints.
    blueprints = [v for k, v in locals().items()
                  if str(k).endswith("_bp")]
    for blueprint in blueprints:
        app.register_blueprint(blueprint)

    return app
