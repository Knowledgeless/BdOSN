#!/usr/bin/env bash
set -euo pipefail

python manage.py collectstatic --noinput --ignore='css/all.min.css'
