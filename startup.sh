#!/bin/bash
python -m playwright install chromium
gunicorn --bind=0.0.0.0:$PORT app:app
