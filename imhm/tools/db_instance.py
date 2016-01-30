# -*- coding:utf-8 -*-
__author__ = 'ery'

import sys
import MySQLdb
import mysql.connector

from sqlalchemy import create_engine, event, select
from sqlalchemy.pool import QueuePool
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.exc import DisconnectionError, DBAPIError
from sqlalchemy.ext.declarative import declarative_base

from imhm.tools import Singleton
# from imhm.tools import GS
from imhm.config import mysqldb_connect_strings, mysql_connector_connect_strings, \
    sqlalchemy_engine_settings, sqlalchemy_sessionmaker_settings, sqlalchemy_queuepool_settings


class DbInstance(object):
    __metaclass__ = Singleton

    def __init__(self):
        # print("create")
        self._mode = "production" # GS.getd("OPERATION_MODE", "development")
        if not ((self._mode == "development") or (self._mode == "production")):
            raise ValueError("Invalid value on OPERATION_MODE : %s" % (self._mode, ))
        self._connector = "MySQLdb" # GS.getd("SQLALCHEMY_CONNECTOR", "MySQLdb")
        if not ((self._connector == "MySQLdb") or (self._connector == "mysql.connector")):
            raise ValueError("Invalid value on SQLALCHEMY_CONNECTOR : %s" % (self._connector, ))

        self._pool = None
        self._engine = None

        self._gevent_already_patched = False

    def _getconn(self):
        if self._connector == "MySQLdb":
            return MySQLdb.connect(**(mysqldb_connect_strings["Common"]))
        elif self._connector == "mysql.connector":
            return mysql.connector.connect(**(mysql_connector_connect_strings["Common"]))
        else:
            raise ValueError("Invalid value on SQLALCHEMY_CONNECTOR : %s" % (self._connector, ))

    def _create_engine(self):
        self.get_pool()
        return create_engine("mysql://", pool=self._pool, \
                            **(sqlalchemy_engine_settings[self._mode]))

    def get_engine(self):
        # print("get engine")
        if not self._engine:
            self._engine = self._create_engine()
        return self._engine

    def get_pool(self):
        # print("get pool")
        if not self._pool:
            self._pool = QueuePool(self._getconn, **(sqlalchemy_queuepool_settings[self._mode]))
        # gevent patch
        # https://github.com/kljensen/async-flask-sqlalchemy-example/blob/master/server.py
        if (not self._gevent_already_patched) and sys.modules.keys().count("gevent") > 0:
            # print("gevent patch")
            self._pool._use_threadlocal = True
            self._gevent_already_patched = True
        return self._pool

    def get_session(self):
        # print("get session")
        return scoped_session(session_factory=sessionmaker(bind=self.get_engine(), \
                                                           **(sqlalchemy_sessionmaker_settings["Common"])))
DB = DbInstance()

Base = declarative_base()
Base.query = DB.get_session().query_property()


@event.listens_for(DB.get_engine(), "engine_connect")
def event_engine_check_connection(connection, branch):
    if branch:
        return
    try:
        connection.scalar(select([1]))
    except DBAPIError, e:
        if e.connection_invalidated:
            connection.scalar(select([1]))
        else:
            raise


@event.listens_for(DB.get_pool(), "checkout")
def event_pool_checkout(dbapi_con, connection_record, connection_proxy):
    try:
        # print("event_pool_checkout #1")
        dbapi_con.ping()
        # print("event_pool_checkout #2")
    except Exception, e:
        # print("event_pool_checkout #3")
        raise DisconnectionError()


# http://docs.sqlalchemy.org/en/latest/core/events.html
# if not GS.is_production():
@event.listens_for(DB.get_pool(), "checkin")
def event_pool_checkin(dbapi_con, connection_record):
    print("HOOK : event_pool_checkin")


@event.listens_for(DB.get_pool(), "connect")
def event_pool_connect(dbapi_con, connection_record):
    print("HOOK : event_pool_connect")


@event.listens_for(DB.get_pool(), "first_connect")
def event_pool_first_connect(dbapi_con, connection_record):
    print("HOOK : event_pool_first_connect")


@event.listens_for(DB.get_pool(), "invalidate")
def event_pool_invalidate(dbapi_con, connection_record, connection_proxy):
    print("HOOK : event_pool_invalidate")


@event.listens_for(DB.get_pool(), "reset")
def event_pool_reset(dbapi_con, connection_record):
    print("HOOK : event_pool_reset")


@event.listens_for(DB.get_pool(), "soft_invalidate")
def event_pool_soft_invalidate(dbapi_con, connection_record, connection_proxy):
    print("HOOK : event_pool_soft_invalidate")


