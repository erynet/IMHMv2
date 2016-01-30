#!/imhm/penv/bin/python
# -*- coding:utf-8 -*-
__author__ = 'ery'

from flask_script import Manager, Server, Shell
from flask_migrate import Migrate, MigrateCommand

from werkzeug.contrib.fixers import ProxyFix

from imhm import create_app
from imhm.models import *
from imhm.tools import Base, DB, GS

app = create_app()
app.wsgi_app = ProxyFix(app.wsgi_app)

manager = Manager(app)
migrate = Migrate(app, Base)

server = Server(host="0.0.0.0")


def make_shell_context():
    return dict(app=app, db=DB.get_session(), s=GS,
                PenaltyLog=PenaltyLog
                )


manager.add_command("shell", Shell(make_context=make_shell_context))
manager.add_command("db", MigrateCommand)
manager.add_command("runserver", server)


@manager.command
def initdb():
    Base.metadata.create_all(bind=DB.get_engine())


@manager.command
def reset_variables():
    GS.reset_to_default()

if __name__ == "__main__":
    manager.run()
