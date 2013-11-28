#!/bin/bash

aptitude update;
aptitude install -y openssl
if [ $? -eq 0 ]; then
	echo "****Installation successfull****"
	exit 0
else
	echo "****Installation ended with error $?****"
	exit $?
fi
