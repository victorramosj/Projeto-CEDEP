release: python cedepe/manage.py migrate && python cedepe/manage.py collectstatic --noinput
web: gunicorn cedepe.cedepe.wsgi:application --chdir cedepe --bind 0.0.0.0:$PORT --workers 2 --log-level debug
