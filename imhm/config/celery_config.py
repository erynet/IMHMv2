# -*- coding:utf-8 -*-
__author__ = 'ery'

from datetime import timedelta


class CeleryConfigCommon(object):
    # BROKER_URL = "redis://localhost:6379/1"
    # CELERY_RESULT_BACKEND = "redis://localhost:6379/1"
    # BROKER_URL = "redis+socket:///tnp/redis.sock?virtual_host=1"
    # CELERY_RESULT_BACKEND = "redis+socket:///tnp/redis.sock?virtual_host=1"
    BROKER_URL = "amqp://guest:guest@localhost:5672/"
    # CELERY_RESULT_BACKEND = "redis://localhost:6379/1"
    CELERY_ENABLE_UTC = False
    CELERY_ACCEPT_CONTENT = ["pickle", "json", "msgpack", "yaml"]
    # CELERY_REDIS_MAX_CONNECTIONS = 32
    CELERY_RESULT_BACKEND = 'amqp'
    CELERY_TASK_RESULT_EXPIRES = 18000


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
