#!/usr/bin/env bash
cd src

echo "DATABASE_URL: $DATABASE_URL"

gunicorn --worker-class gevent --workers 4 --bind 0.0.0.0:$PORT app.wsgi:application 