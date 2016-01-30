# -*- coding:utf-8 -*-
__author__ = 'ery'

from datetime import timedelta


class CeleryConfigCommon(object):
    BROKER_URL = "redis://192.168.137.120:63709/5"
    CELERY_RESULT_BACKEND = "redis://192.168.137.120:63709/6"
    CELERY_ENABLE_UTC = False
    CELERY_ACCEPT_CONTENT = ["pickle", "json", "msgpack", "yaml"]
    CELERY_REDIS_MAX_CONNECTIONS = 32

    CELERYBEAT_SCHEDULE = {
        "patrol": {
            "task": "coock.utils.async.functions.patrol",
            "schedule": timedelta(seconds=15)
        },
    }


class CeleryConfigDevelopment(CeleryConfigCommon):
    CELERY_REDIRECT_STDOUTS = True
    CELERY_REDIRECT_STDOUTS_LEVEL = "DEBUG"


class CeleryConfigProduction(CeleryConfigCommon):
    CELERY_REDIRECT_STDOUTS = False
    CELERY_REDIRECT_STDOUTS_LEVEL = "ERROR"


celery_configs = \
    {
        "development": CeleryConfigDevelopment,
        "production": CeleryConfigProduction,
    }
