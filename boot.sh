#!/bin/bash
source venv/bin/activate
while true; do
    flask db upgrade
    if [[ "$?" == "0" ]]; then
        break
    fi
    echo Upgrade command failed, retrying in 5 secs...
    sleep 5
done
exec gunicorn -b :5003 --workers=2 --threads=4 --worker-class=gthread --worker-tmp-dir /dev/shm --access-logfile - --error-logfile - main:app
