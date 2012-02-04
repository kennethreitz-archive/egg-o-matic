# -*- coding: utf-8 -*-

import json
import os
import sys
import tempfile

import envoy
import heroku
import requests

from flask import Flask, request, Response
from flask.ext.celery import Celery
from raven.contrib.flask import Sentry

import urllib


app = Flask(__name__)

redis_url = os.environ.get('REDISTOGO_URL', 'redis://localhost:6379/0')

app.config['BROKER_URL'] = redis_url
app.config['CELERY_ENABLE_UTC'] = True
app.config['CELERYD_POOL'] = 'gevent'

celery = Celery(app)
# sentry = Sentry(app)

HEROKU_EMAIL = os.environ.get('HEROKU_EMAIL')
HEROKU_PASS = os.environ.get('HEROKU_PASS')

heroku = heroku.from_pass(HEROKU_EMAIL, HEROKU_PASS)


@celery.task(name='yoshi.install')
def install(package, connect=False):

    # Create temp git directory.
    git_path = os.path.join(tempfile.mkdtemp(), 'repo')

    os.makedirs(git_path)
    os.chdir(git_path)

    # Initialize the repo.
    envoy.run('git init')

    with open('requirements.txt', 'w') as f:
        f.write(package)

    envoy.run('git add requirements.txt')
    envoy.run('git commit -m \'init\'')

    # Create a new app.
    print 'creating'
    h_app = heroku.apps.add(stack='cedar')
    print h_app.__dict__

    print 'pushing'
    cmd = 'git push https://{u}:{p}@code.heroku.com/{app}.git master'.format(
        u=urllib.quote(HEROKU_EMAIL),
        p=urllib.quote(HEROKU_PASS),
        app=h_app.name
    )

    if not connect:
        r = envoy.run(cmd)
        h_app.destroy()
    else:
        r = envoy.connect(cmd)

    return r


@celery.task(name='yoshi.test_install')
def test_install(package, webhook):

    r = install(package)

    success = (r.status_code == 0)

    payload = json.dumps({
        'success': success,
        'package': package
    })

    requests.post(
        url=webhook,
        headers={'Content-Type': 'application/json'},
        data=payload
    )


@app.route('/')
def hello():
    test_install.delay('requests', 'http://www.postbin.org/14y61vg')
    return 'hello world!'


@app.route('/test/install', methods=['POST'])
def test_egg():

    package = request.form['package']
    webhook = request.form['webhook']

    test_install.delay()

    payload = {
        'package': package,
        'queued': True
    }

    return jsonify(payload)


def gen_lines(r):
    yield ''
    while 1:
        line = r._process.stderr.readline()
        if 'code.heroku.com' in line:
            break
        else:
            yield line

@app.route('/test/install/<package>', methods=['GET'])
def test_egg_now(package):
    r = install(package, connect=True)

    return Response(gen_lines(r))



if __name__ == '__main__':
    app.run()
