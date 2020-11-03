#!/bin/bash

# A quick and dirty bash script to start the development server and all of its
# required services

check_prerequisites () {
	if ! type python3 > /dev/null; then
		echo 'python3 command not found. Install python 3 before continuing.'
		return 1
	elif ! type redis-server > /dev/null; then
		echo 'redis-server command not found. Install redis before continuing.'
		return 1
	elif [[ ! -d ./env/ ]]; then
		echo 'Create a virtual environment in the env folder and install requirements before continuing.'
		return 1
	elif [[ ! -d ./redis/ ]]; then
		mkdir redis
	elif [[ ! -f ./redis/redis.conf ]]; then
		echo 'Create a redis.conf file in the redis folder before continuing.'
		return 1
	fi
	return 0
}

check_prerequisites || exit 1

# Activate virtual environment
source env/bin/activate

# Start redis and workers in the background
cd redis
redis-server redis.conf &
cd ..
python3 bagitobjecttransfer/manage.py rqworker --no-color default &

# Start server
python3 bagitobjecttransfer/manage.py runserver
