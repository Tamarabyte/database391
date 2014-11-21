#!/bin/bash

"""
Host the app on gunicorn. A python WSGI HTTP Server.
"""


gunicorn app:app --bind 127.0.0.1:8002
