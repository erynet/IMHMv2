# -*- coding:utf-8 -*-

import sys
reload(sys)
sys.setdefaultencoding("utf-8")
import os
basedir = os.path.abspath(os.path.dirname(__file__))
sys.path.append(os.path.join(basedir, "../"))

import redis
import cPickle
import MySQLdb
from contextlib import closing
from datetime import datetime, timedelta
from imhm.tools import Singleton
from imhm.tools import LocalCacheManager
from imhm.config import vars, redis_server_settings, mysqldb_connect_strings


class PickledRedis(redis.Redis):
    def get(self, name):
        _pickled = super(PickledRedis, self).get(name)
        if _pickled is None:
            return None
        return cPickle.loads(_pickled)

    def set(self, name, value, ex=None, px=None, nx=False, xx=False):
        return super(PickledRedis, self).set(name, cPickle.dumps(value, cPickle.HIGHEST_PROTOCOL), ex, px, nx, xx)

    def setex(self, name, value, time):
        return super(PickledRedis, self).setex(name, cPickle.dumps(value, cPickle.HIGHEST_PROTOCOL), time)


class GlobalSettings(object):
    __metaclass__ = Singleton

    def __init__(self, prefix=None):
        if not prefix:
            self.prefix = "SetTtiNg"
        else:
            assert isinstance(prefix, str)
            self.prefix = prefix
        # cache level L1
        self.local = LocalCacheManager(default_expire_mean=30)
        # self.local.clear()
        # cache level L2
        self.redis_connection_pool = \
            redis.ConnectionPool(max_connections=128, **redis_server_settings["RemoteSetting"])
        self.redis = redis.Redis(connection_pool=self.redis_connection_pool)
        # cache level L3
        self.my_conn = MySQLdb.connect(**(mysqldb_connect_strings["Setting"]))
        self.my_conn.autocommit(False)
        self.my_cur = None

        self._is_production = None

    def clear_cache(self, l1=True, l2=False):
        if l1:
            self.local.clear()
        if l2:
            self.redis.flushdb()

    def reset_to_default(self):
        # clear L1, L2 Caches
        self.clear_cache(l1=True, l2=True)
        # reset L3
        try:
            self.my_conn.ping(True)
            with closing(self.my_conn.cursor()) as self.my_cur:
                self.my_cur.execute("""DELETE FROM `Coock`.`settings` WHERE 1""")
                for key in vars:
                    self.my_cur.execute("""INSERT INTO `Coock`.`settings`(rkey, value) VALUES(%s, %s)""", \
                        (self._convert_to_real_key(key), self._encode_value(key, vars[key]["default"])))
                self.my_conn.commit()
        except MySQLdb.Error, e:
            self.my_conn.rollback()
            print(e.message, str(e.args))
            return False
        # reset L2
        try:
            p = self.redis.pipeline(transaction=True)
            for key in vars:
                p.setex(self._convert_to_real_key(key), self._encode_value(key, vars[key]["default"]), \
                        86400 * 365 * 10)
            p.execute()
        except redis.RedisError, e:
            print(e.message, str(e.args))
            return False
        # reset L1
        for key in vars:
            self.local.set(self._convert_to_real_key(key), self._encode_value(key, vars[key]["default"]))

        return True

    def reload_all_from_db(self):
        # clear L1, L2 Caches
        self.clear_cache(l1=True, l2=True)
        # load all real_key, value in L3(db)
        try:
            self.my_conn.ping(True)
            with closing(self.my_conn.cursor()) as self.my_cur:
                self.my_cur.execute("""SELECT rkey, value FROM `Coock`.`settings` WHERE 1""")
                _fetched = self.my_cur.fetchall()
        except MySQLdb.Error, e:
            print(e.message, str(e.args))
            return False
        # fetch all rows
        d = {}
        for row in _fetched:
            d[row[0]] = row[1]
        # cross check vice versa
        # for key in d.keys():
        #     if key not in vars:
        #         return False
        # for key in vars:
        #     if key not in d.keys():
        #         return False
        # set to L2
        try:
            p = self.redis.pipeline(transaction=True)
            for key in d.keys():
                p.setex(key, d[key], 86400 * 365 * 10)
            p.execute()
        except redis.RedisError, e:
            print(e.message, str(e.args))
            return False
        # set to L1
        for key in d.keys():
            self.local.set(key, d[key])
        return True

    def _convert_to_real_key(self, key):
        if key not in vars:
            return None
        if vars[key]["type"] == str:
            return self.prefix + "__" + key + "__S"
        elif vars[key]["type"] == int:
            return self.prefix + "__" + key + "__I"
        elif vars[key]["type"] == float:
            return self.prefix + "__" + key + "__F"
        elif vars[key]["type"] == object:
            return self.prefix + "__" + key + "__O"
        else:
            assert "This Can't be"

    def _encode_value(self, key, value=None):
        if key not in vars:
            return None
        if not value:
            value = vars[key]["default"]

        if vars[key]["type"] == str:
            return value
        elif vars[key]["type"] == int:
            return str(value)
        elif vars[key]["type"] == float:
            return str(value)
        elif vars[key]["type"] == object:
            return cPickle.dumps(value, cPickle.HIGHEST_PROTOCOL)
        else:
            assert "This Can't be"

    def _decode_value(self, key, serialized_value):
        if key not in vars:
            return None
        if vars[key]["type"] == str:
            return serialized_value
        elif vars[key]["type"] == int:
            return int(serialized_value)
        elif vars[key]["type"] == float:
            return float(serialized_value)
        elif vars[key]["type"] == object:
            return cPickle.loads(serialized_value)
        else:
            assert "This Can't be"

    def set(self, key, value):
        real_key = self._convert_to_real_key(key)
        if not real_key:
            return False
        serialized_value = self._encode_value(key, value)
        # L3
        try:
            self.my_conn.ping(True)
            with closing(self.my_conn.cursor()) as self.my_cur:
                self.my_cur.execute("""SELECT COUNT(*) FROM `Coock`.`settings` WHERE rKey = %s""", (real_key,))
                _count = self.my_cur.fetchone()
                if _count[0] > 0:
                    self.my_cur.execute("""UPDATE `Coock`.`settings` SET value = %s WHERE rkey = %s""", \
                                        (serialized_value, real_key))
                else:
                    self.my_cur.execute("""INSERT INTO `Coock`.`settings`(rkey, value) VALUES(%s, %s)""", \
                                    (real_key, serialized_value,))
                self.my_conn.commit()
        except MySQLdb.Error, e:
            self.my_conn.rollback()
            print(e.message, str(e.args))
            return False
        # L2
        try:
            self.redis.setex(real_key, serialized_value, 86400 * 365 * 10)
        except redis.RedisError, e:
            print(e.message, str(e.args))
            return False
        # L1
        if not self.local.set(real_key, serialized_value):
            return False
        return True

    def get(self, key, level=None):
        if key not in vars:
            return None
        real_key = self._convert_to_real_key(key)

        if not level:
            # approach to l1
            _l1_value = self.local.get(real_key)
            if not _l1_value:
                # approach to l2
                _l2_value = self.redis.get(real_key)
                if not _l2_value:
                    # worst case, using L1, L2, L3
                    # approach to L3
                    try:
                        self.my_conn.ping(True)
                        with closing(self.my_conn.cursor()) as self.my_cur:
                            self.my_cur.execute("""SELECT COUNT(*) FROM `Coock`.`settings` WHERE rKey = %s""", (real_key,))
                            _count = self.my_cur.fetchone()
                            if _count[0] > 0:
                                self.my_cur.execute("""SELECT value FROM `Coock`.`settings` WHERE rKey = %s""", (real_key,))
                                _value = self.my_cur.fetchone()
                                _l3_value = _value[0]
                            else:
                                # maybe have problem
                                return None
                    except MySQLdb.Error, e:
                        # print(e.message, str(e.args))
                        return None
                    # approach to L2
                    try:
                        self.redis.setex(real_key, _l3_value, 86400 * 365 * 10)
                    except redis.RedisError, e:
                        # print(e.message, str(e.args))
                        return None
                    # approach to L1
                    self.local.set(real_key, _l3_value)
                    # print("L3 : %s" % key)
                    return self._decode_value(key, _l3_value)

                else:
                    # good case, used L1, L2
                    # print("L2 : %s" % key)
                    self.local.set(real_key, _l2_value)
                    return self._decode_value(key, _l2_value)
            else:
                # best case, only used l1
                # print("L1 : %s" % key)
                return self._decode_value(key, _l1_value)
        elif level == 1:
            # load from L1, if key not exist in L1 returns None
            _l1_value = self.local.get(real_key)
            if _l1_value:
                return self._decode_value(key, _l1_value)
            else:
                return None
        elif level == 2:
            # load from L2, if key not exist in L2 returns None
            _l2_value = self.redis.get(real_key)
            if _l2_value:
                return self._decode_value(key, _l2_value)
            else:
                return None
        elif level == 3:
            # load from L3, if key not exist in L3 returns None
            try:
                self.my_conn.ping(True)
                with closing(self.my_conn.cursor()) as self.my_cur:
                    self.my_cur.execute("""SELECT COUNT(*) FROM `Coock`.`settings` WHERE rKey = %s""", (real_key,))
                    _count = self.my_cur.fetchone()
                    if _count[0] > 0:
                        self.my_cur.execute("""SELECT value FROM `Coock`.`settings` WHERE rKey = %s""", (real_key,))
                        _value = self.my_cur.fetchone()
                        _l3_value = _value[0]
                    else:
                        # maybe have problem
                        return None
            except MySQLdb.Error, e:
                # print(e.message, str(e.args))
                return None
            if _l3_value:
                return self._decode_value(key, _l3_value)
            else:
                return None
        else:
            raise "Unknown cache level : %s" % (str(level), ), ValueError

    def getd(self, key, default=None, level=None):
        _rt = self.get(key, level)
        if not _rt:
            # print("Using default, %s : %s" % (key, default,))
            if not default:
                return vars[key]["default"]
            return default
        else:
            return _rt

    def get_many(self, keys):
        real_keys_dict = {}
        for candidate in keys:
            if candidate not in vars:
                raise "Unknown setting variable name '%s'" % (candidate, ), AttributeError
            real_keys_dict[self._convert_to_real_key(candidate)] = candidate
        real_keys = real_keys_dict.keys()

        d = {}

        # approach to L1
        _l1_found_dict, _l1_not_found_list = self.local.get_many(real_keys)
        if _l1_not_found_list.__len__() == 0:
            # best case, only used L1
            for _real_key in _l1_found_dict.keys():
                key = real_keys_dict[_real_key]
                d[key] = self._decode_value(key, _l1_found_dict[_real_key])
            return d
        # approach to L2
        _l2_found_dict = {}
        _l2_not_found_list = []
        try:
            p = self.redis.pipeline()
            for idx in range(_l1_not_found_list.__len__()):
                p.get(_l1_not_found_list[idx])
            _values = p.execute()
        except redis.RedisError, e:
            print(e.message, str(e.args))
            return None
        for idx in range(_l1_not_found_list.__len__()):
            if not _values[idx]:
                _l2_not_found_list.append(_l1_not_found_list[idx])
            else:
                _l2_found_dict[_l1_not_found_list[idx]] = _values[idx]
        if _l2_found_dict.__len__() > 0:
            # set to L1 for future
            for _real_key in _l2_found_dict:
                self.local.set(_real_key, _l2_found_dict[_real_key])

        if _l2_not_found_list.__len__() == 0:
            # good case, used L1, L2
            _d = _l1_found_dict.copy()
            _d.update(_l2_found_dict)
            for _real_key in _d.keys():
                key = real_keys_dict[_real_key]
                d[key] = self._decode_value(key, _d[_real_key])
            return d
        # approach to L3
        _l3_found_dict = {}
        try:
            self.my_conn.ping(True)
            with closing(self.my_conn.cursor()) as self.my_cur:
                for _real_key in _l2_not_found_list:
                    self.my_cur.execute("""SELECT COUNT(*) FROM `Coock`.`settings` WHERE rKey = %s""", (_real_key,))
                    _count = self.my_cur.fetchone()
                    if _count[0] > 0:
                        self.my_cur.execute("""SELECT value FROM `Coock`.`settings` WHERE rkey = %s""", (_real_key,))
                        _value = self.my_cur.fetchone()
                        _l3_found_dict[_real_key] = _value[0]
                    else:
                        # maybe have problem
                        return None
        except MySQLdb.Error, e:
            print(e.message, str(e.args))
            return None
        if _l3_found_dict.__len__() > 0:
            # set to L1, L2 for future
            try:
                p = self.redis.pipeline(transaction=True)
                for _real_key in _l3_found_dict:
                    p.setex(_real_key, _l3_found_dict[_real_key], 86400 * 365 * 10)
                p.execute()
            except redis.RedisError, e:
                print(e.message, str(e.args))
                return None
            for _real_key in _l3_found_dict:
                self.local.set(_real_key, _l3_found_dict[_real_key])
            # worst case, using L1, L2, L3
            _d = _l1_found_dict.copy()
            _d.update(_l2_found_dict)
            _d.update(_l3_found_dict)
            for _real_key in _d.keys():
                # d[real_keys_dict[_real_key]] = _d[_real_key]
                key = real_keys_dict[_real_key]
                d[key] = self._decode_value(key, _d[_real_key])
            return d
        else:
            # maybe have problem
            return None

    def get_many_from_default(self, keys):
        d = {}
        for key in keys:
            if key not in vars:
                raise "Unknown setting variable name '%s'" % (key, ), AttributeError
            d[key] = vars[key]["default"]
        return d

    def listing_all(self):
        r = []
        for key in vars:
            r.append((key, repr(self.get(key))))
        return r

    def is_production(self):
        if not self._is_production:
            _value = self.get("OPERATION_MODE", level=2)
            if not _value:
                # set to default value as production
                self._is_production = (True, datetime.now() + timedelta(seconds=600))
                return True
            else:
                if _value == "production":
                    self._is_production = (True, datetime.now() + timedelta(seconds=600))
                    return True
                elif _value == "development":
                    self._is_production = (False, datetime.now() + timedelta(seconds=600))
                    return False
                else:
                    raise "Invalid OPERATION_MODE value : '%s'" % (str(_value), ), ValueError
        else:
            if self._is_production[1] >= datetime.now():
                return self._is_production[0]
            else:
                _value = self.get("OPERATION_MODE", level=2)
                if not _value:
                    # set to default value as production
                    self._is_production = (True, datetime.now() + timedelta(seconds=600))
                    return True
                else:
                    if _value == "production":
                        self._is_production = (True, datetime.now() + timedelta(seconds=600))
                        return True
                    elif _value == "development":
                        self._is_production = (False, datetime.now() + timedelta(seconds=600))
                        return False
                    else:
                        raise "Invalid OPERATION_MODE value : '%s'" % (str(_value), ), ValueError

    def switch_operation_mode(self):
        if self.is_production():
            # switch to development
            self.set("OPERATION_MODE", "development")
            self._is_production = (False, datetime.now() + timedelta(seconds=600))
            return "development"
        else:
            # switch to production
            self.set("OPERATION_MODE", "production")
            self._is_production = (True, datetime.now() + timedelta(seconds=600))
            return "production"

GS = GlobalSettings()