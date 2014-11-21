#!/usr/bin/env python

"""
Run the app in debug mode. With log printing to command line.
"""

from app import app
app.run(debug=True, port=8002, host='127.0.0.1')
