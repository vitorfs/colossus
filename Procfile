web: gunicorn colossus.wsgi --log-file -
worker: celery worker --app=colossus --loglevel=INFO
beat: celery beat --app=colossus --loglevel=INFO
