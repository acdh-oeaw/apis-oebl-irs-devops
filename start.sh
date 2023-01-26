#!/bin/bash
#useradd -M celery
export LC_ALL=C.UTF-8
export LANG=C.UTF-8
python manage.py makemigrations --settings=apis.settings.dev
python manage.py migrate --settings=apis.settings.dev
mkdir /tmp/celery
supervisord -c celery_config/celery.conf
supervisorctl -c celery_config/celery.conf start all
gunicorn apis.wsgi -b 0.0.0.0:5000 --timeout 120 --workers=3 --threads=3 --worker-connections=1000