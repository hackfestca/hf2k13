#!/bin/bash
# Bash script to setup basic configs of HF 2013 VMs

if [[ $(/usr/bin/id -u) -ne 0 ]]; then
    echo "Not running as root."
    exit
fi

#Set SCRIPT_DIR to contain current folder where the script is runned
export SCRIPT_DIR=`pwd`

###########################Color Formating##############################
export TEXT_COLOR="[38;05;105m"
export DEFAULT_COLOR="[38;05;015m"
export SUCCESS_COLOR="[32;01m"
export RED_COLOR="[31;01m"
########################################################################


###########################Main script##############################
## Install required packages
echo $TEXT_COLOR"Installing some packages  - OpenSSL and family"$DEFAULT_COLOR
bash sh/installOpenSSL.sh

if [ $? -ne 0 ]; then
	echo $RED_COLOR''Error when installing OpenSSL packages''$DEFAULT_COLOR
	exit 1
fi

echo $SUCCESS_COLOR''Installation of OpenVPN packages succesfull''$DEFAULT_COLOR

echo $RED_COLOR"Warning! You gonna have to enter a password for the CA. Remember it or you're gonna hate yourself and hate life all together as you can't sign your certificate without it!!"$DEFAULT_COLOR

bash $SCRIPT_DIR/sh/create_ssl_key.sh

exit 0
