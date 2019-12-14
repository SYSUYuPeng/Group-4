python3 models.py
gunicorn --bind 0.0.0.0:20080 --workers=9 wsgi:app
