#!/bin/bash

gunicorn --bind 127.0.0.1:5000 app:app &

APP_PID=$!

sleep 5

curl http://127.0.0.1:5000/

APP_CODE=$?

sleep 5

kill -TERM $APP_PID

exit $APP_CODE