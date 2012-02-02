# -*- coding: utf-8 -*-

import os
import sys

from flask import Flask
from flask.ext.celery import Celery


app = Flask(__name__)

app.config['BROKER_URL'] = os.environ.get('BROKER_URL', 'redis://localhost:6379/0')
celery = Celery(app)


@celery.task(name='yoshi.test_egg')
def test():
    import time
    time.sleep(10)
    print 'hi!'


@app.route('/')
def hello():
    test.delay()
    return 'hello world!'


if __name__ == '__main__':
    app.run()
