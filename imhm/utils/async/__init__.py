# -*- coding:utf-8 -*-
__author__ = 'ery'

from datetime import datetime, timedelta
from celery import Celery
from celery.schedules import crontab
from flask import current_app

from imhm.tools import GS
from imhm.config import celery_configs

capp = Celery(current_app, include=["functions"])
if GS.is_production():
    capp.config_from_object(celery_configs["production"])
else:
    capp.config_from_object(celery_configs["development"])