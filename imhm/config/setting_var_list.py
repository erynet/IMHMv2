# -*- coding:utf-8 -*-

vars = \
    {
        "VAR_NAME_EXAMPLE1": \
            {
                "type": object,
                "default": [1,2,3,4,5]
            },
        "VAR_NAME_EXAMPLE2": \
            {
                "type": str,
                "default": "string value"
            },
        "VAR_NAME_EXAMPLE3": \
            {
                "type": int,
                "default": 2**16
            },
        "VAR_NAME_EXAMPLE4": \
            {
                "type": float,
                "default": 0.001
            },
        "VAR_NAME_CUSTOM1": \
            {
                "type": object,
                "default": {}
            },
        "VAR_CELERY_PUSH_CHUNK_SIZE": \
            {
                "type": int,
                "default": 20
            },
        "OPERATION_MODE": \
            {
                "type": str,
                "default": "development"
            },
        "SQLALCHEMY_CONNECTOR": \
            {
                "type": str,
                "default": "MySQLdb" # or mysql.connector
            },
        "POLICY_INITIAL_POINT_FOR_NEW_USER": \
            {
                "type": int,
                "default": 5000
            },
        "POLICY_INTRODUCE_POINT_FOR_NEW_USER": \
            {
                "type": int,
                "default": 5000
            },
        "POLICY_BASE_COST_OF_30_DAYS": \
            {
                "type": int,
                "default": 30000
            },
        "POLICY_DISCOUNT_RATE_OF_A_YEAR": \
            {
                "type": float,
                "default": 25.
            },
        "POLICY_USER_WITHDRAW_POSTPONE_HOURS": \
            {
                "type": int,
                "default": 720
            },
        "POLICY_WARNING_DEFAULT_ACTIVE_HOURS": \
            {
                "type": int,
                "default": 720
            },
        "POLICY_ACTIVE_WARNING_COUNT_TO_DISABLE": \
            {
                "type": int,
                "default": 3
            },

    }
