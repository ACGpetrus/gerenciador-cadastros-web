#!/usr/bin/env bash
# exit on error
set -o errexit

pip install -r requirements.txt

python -m flask shell <<EOF
from app import db
with app.app_context():
    db.create_all()
EOF