# -*- coding:utf-8 -*-
__author__ = 'ery'

import datetime
try:
    import ujson as json
except ImportError:
    import json
from flask import current_app, request
# from imhm.tools import GS


def pre_request_logging():
    s = ""
    if request.data.__len__() > 0:
        try:
            d = json.loads(unicode(request.data, "utf8"))
            # d = json.loads(request.data)
            s = json.dumps(d, indent=4, sort_keys=True)
        except Exception, e:
            print str(e)

    current_app.logger.debug("\n".join([
        datetime.datetime.today().ctime() + " " + request.remote_addr,
        request.method + " " + request.url,
        s,
        ", ".join([": ".join(x) for x in request.headers])])
    )


def after_request_logging(response):
    if response:
        try:
            d = json.loads(unicode(response.get_data(), "utf8"))
            # d = json.loads(response.get_data())
            current_app.logger.debug(
                json.dumps(d, indent=4, sort_keys=True))
        except Exception, e:
            print str(e)

    return response
