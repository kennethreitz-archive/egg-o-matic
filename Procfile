web: gunicorn yoshi:app -b 0.0.0.0:$PORT -w 3 -k gevent -t 3 --name eggomatic
node: python manage.py celeryd
