python3 models.py
gunicorn --bind 0.0.0.0:8000 --workers=9 wsgi:app
