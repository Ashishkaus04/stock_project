#!/usr/bin/env bash
cd src
gunicorn --worker-class gevent --workers 4 --bind 0.0.0.0:$PORT app.wsgi:application 