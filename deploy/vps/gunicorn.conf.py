"""Gunicorn configuration for VPS production."""

import multiprocessing
import os

bind = f"unix:{os.environ.get('GUNICORN_SOCKET', '/home/estronix/ecommerce/estronix.sock')}"
workers = int(os.environ.get("WEB_CONCURRENCY", max(2, multiprocessing.cpu_count())))
threads = int(os.environ.get("GUNICORN_THREADS", 2))
timeout = int(os.environ.get("GUNICORN_TIMEOUT", 120))
umask = 0o007
wsgi_app = "wsgi:app"
accesslog = "-"
errorlog = "-"
capture_output = True
preload_app = True
