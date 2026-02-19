#!/usr/bin/env python3
"""
WSGI entry point for Render deployment
Gunicorn uses this to start the Flask application
"""

from web_app import create_app
import os

# Flask app 생성
app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
