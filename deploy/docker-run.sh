#!/usr/bin/env bash

set -u   # crash on missing env variables
set -e   # stop on any error
set -x

echo Collecting static files
python manage.py collectstatic --no-input

# run uwsgi
exec uwsgi --ini main/uwsgi.ini
