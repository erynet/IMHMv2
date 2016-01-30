# -*- coding:utf-8 -*-

# DB 0 : Setting
# DB 1 : RLock
# DB 2 : Session
# DB 3 : Static Caching
# DB 4 : DB Caching
# DB 5 : Celery
# DB 6 : Celery Result

# redis.ConnectionPool(max_connections=128, **redis_server_settings["Setting"])

redis_server_settings = \
    {
        "LocalSetting":
            {
                "db": 0,
                "password": None,
                "path": "/tmp/redis.sock"
            },

        "RemoteSetting":
            {
                "host": "192.168.137.120",
                "port": 63709,
                "db": 0,
                "password": None,
                "socket_timeout": None,
                #"charset": "utf-8",
                #"errors": "strict",
                #"unix_socket_path": None,

            },

        "RLock":{
                "host": "192.168.137.120",
                "port": 63709,
                "db": 1,
                "password": None,
                "socket_timeout": None,
            }
            ,

        "Session":
            {
                "host": "192.168.137.120",
                "port": 63709,
                "db": 2,
                "password": None,
                "socket_timeout": None,
            },

        "StaticCache":
            {
                "host": "192.168.137.120",
                "port": 63709,
                "db": 3,
                "password": None,
                "socket_timeout": None,
            },

        "DBCache":
            {
                "host": "192.168.137.120",
                "port": 63709,
                "db": 4,
                "password": None,
                "socket_timeout": None,
            },

        "Celery":
            {
                "host": "192.168.137.120",
                "port": 63709,
                "db": 5,
                "password": None,
                "socket_timeout": None,
            },
    }

