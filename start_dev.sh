#!/bin/bash
#useradd -M celery
export LC_ALL=C.UTF-8
export LANG=C.UTF-8
python manage.py migrate --settings=apis.settings.dev
mkdir /tmp/celery
supervisord -c celery_config/celery_dev.conf
supervisorctl -c celery_config/celery_dev.conf start all
python manage.py runserver ${1}