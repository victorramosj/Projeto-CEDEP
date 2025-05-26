web: gunicorn cedepe.wsgi:application --bind 0.0.0.0:$PORT --workers 2 --log-level debug
release: python manage.py migrate && python manage.py collectstatic --noinput