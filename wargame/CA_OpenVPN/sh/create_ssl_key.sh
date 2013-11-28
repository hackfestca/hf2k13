#!/bin/bash
#Script to generate server and client key for Hackfest team
#With some help from http://www.macfreek.nl/memory/Create_a_OpenVPN_Certificate_Authority

##################
# function build_server_key()
#
# Build server key (SSL) to use with openvpn
# In : Nothing
# Return : Nothing (files)
####################
build_server_key()
{	
 for (( c=1; c<=8; c++ ))
 do
	echo $TEXT_COLOR"Create Server Certificate - Team $c"$DEFAULT_COLOR
	#Write server.cnf for the current team
	cat > files/server.team$c.cnf <<EOF
		# Hackfest 2013 War Game
		# Server Key - OpenVPN Track             
		# Team: $c
# TLS server certificate request

# This file is used by the openssl req command. The subjectAltName cannot be
# prompted for and must be specified in the SAN environment variable.

        [ req ]
        default_bits            = 2048                  # RSA key size
        encrypt_key             = no                    # Protect private key
        default_md              = sha1                # MD to use
        utf8                    = yes                   # Input is UTF-8
        string_mask             = utf8only              # Emit UTF-8 strings
        prompt                  = no                    # Prompt for DN
        distinguished_name      = server_dn             # DN template
        req_extensions          = server_reqext         # Desired extensions

        [ server_dn ]
        countryName             = "CA"
        stateOrProvinceName     = "QC"
        localityName            = "Quebec"
        organizationName        = "War Game"
        commonName              = "Team$c_srvclt"
        #commonName_max          = 64

        [ server_reqext ]
        keyUsage                = critical,digitalSignature,keyEncipherment
        #extendedKeyUsage        = serverAuth,clientAuth
        extendedKeyUsage        = serverAuth
        subjectKeyIdentifier    = hash
EOF

	#Build server certificate
	openssl req -new -config files/server.team$c.cnf -keyout CA/Team$c/server.key -out CA/Team$c/server.req
	openssl ca -batch -config files/ca-sign.cnf -extensions X509_server -in CA/Team$c/server.req -out CA/Team$c/server.crt
	
  #Set security on key
  chmod 400 CA/Team$c/server.key
 done 
}

##############################
#                            #
#      Main Function         #
#                            #
##############################

#Clean everything and create new folders (roughly clean-all from easy-rsa)
#Create folder : CA, CA/TeamX (X = 1..8)
#Create empty file for further use by OpenSSL : index.txt, serial
cd $SCRIPT_DIR
/bin/rm -r CA >> /dev/null
mkdir CA
for (( c=1; c<=8; c++ ))
do
	mkdir CA/Team$c
done 
touch CA/index.txt
echo 01\n > CA/serial

#Build RootCA certificate (roughly build-ca from easy-rsa)
echo $TEXT_COLOR"Create CA key"$DEFAULT_COLOR
openssl req -new -config files/ca.cnf -keyout CA/ca.key -out CA/ca.req

echo $TEXT_COLOR"Create CA-sign request"$DEFAULT_COLOR
openssl ca -batch -config files/ca-sign.cnf -extensions X509_ca -days 3650 -create_serial -selfsign \
    -keyfile CA/ca.key -in CA/ca.req -out CA/ca.crt

#Set security on key
chmod 400 CA/ca.key
chmod 444 CA/ca.crt

#Build Prime Numbers (Roughly equivalent to build-dh
openssl dhparam -out CA/dh1024.pem 1024

#Create teams server key
echo $SUCCESS_COLOR''\n\n\nCreation of server keys for the teams''$DEFAULT_COLOR
build_server_key

#Clean up the crap
/bin/rm -f CA/0*.pem
/bin/rm -f CA/1*.pem
/bin/rm -f CA/*.req

echo $SUCCESS_COLOR''Creation of OpenSSL certificates succesful''$DEFAULT_COLOR
