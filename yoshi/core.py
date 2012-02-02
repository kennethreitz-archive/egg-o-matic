# -*- coding: utf-8 -*-

import os
import sys


import heroku
from flask import Flask
from flask.ext.celery import Celery
from raven.contrib.flask import Sentry

app = Flask(__name__)

redis_url = os.environ.get('REDISTOGO_URL', 'redis://localhost:6379/0')

app.config['BROKER_URL'] = redis_url
app.config['CELERY_ENABLE_UTC'] = True

celery = Celery(app)
sentry = Sentry(app)

heroku = heroku.from_key(os.environ.get('HEROKU_APIKEY'))


@celery.task(name='yoshi.test_egg')
def test():
    print heroku.apps


@app.route('/')
def hello():
    test.delay()
    return 'hello world!'


if __name__ == '__main__':
    app.run()
