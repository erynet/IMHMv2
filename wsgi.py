import os
import sys
from gevent.monkey import patch_all
patch_all()

activate_this = '../bin/activate_this.py'
execfile(activate_this, dict(__file__=activate_this))

path = os.path.join(os.path.dirname(__file__), os.pardir)
if path not in sys.path:
    sys.path.append(path)

from manage import app
application = app

if __name__ == "__main__":
    application.run()
