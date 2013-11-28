#!/bin/bash

####### Color formating######
NOCOLOR='\033[0m'
GREEN_COLOR='\033[0;32m'
RED_COLOR='\033[0;31m'
PURPLE_COLOR='\033[0;35m'

usage()
{
    echo "Create a new OpenVPN for the team(s)"
    echo " "
    echo "$0 -i ID"
    echo " "
    echo "options:"
    echo "--help                    show brief help"
    echo "-i, --id=ID               team id (ex: 1..8)"
    echo "--all                     do it for all teams!"
    echo ""
}

##################
# function build_client_key()
#
# Build client key (SSL) to use with openvpn
# In : Nothing
# Return : Nothing (files)
####################
build_client_key()
{	
	echo $TEXT_COLOR"Create Client Certificate"$DEFAULT_COLOR
	#Write client.cnf for the current team
	cat > OpenVPN_Client/team$1.$2.client.cnf <<EOF
		# Hackfest 2013 War Game
		# Client Key - OpenVPN Track
		# Team: $1

# TLS client certificate request

# This file is used by the openssl req command. The subjectAltName cannot be
# prompted for and must be specified in the SAN environment variable.

        [ req ]
        default_bits            = 1024                  # RSA key size
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
        commonName              = "Team_$1_cltcert-$2"
        #commonName_max          = 64

        [ server_reqext ]
        keyUsage                = critical,digitalSignature,keyEncipherment
        #extendedKeyUsage        = serverAuth,clientAuth
        extendedKeyUsage        = clientAuth
        subjectKeyIdentifier    = hash

EOF

	#Build client certificate
	openssl req -new -config OpenVPN_Client/team$1.$2.client.cnf -keyout OpenVPN_Client/team$1.$2.client.key -out OpenVPN_Client/team$1.$2.client.req
	openssl ca -batch -config files/ca-sign.cnf -in OpenVPN_Client/team$1.$2.client.req -out OpenVPN_Client/team$1.$2.client.crt
	
	#Delete unecessary file
	/bin/rm -f OpenVPN_Client/team$1.$2.client.req
	/bin/rm -f OpenVPN_Client/team$1.$2.client.cnf
}

create_conf()
{
    mkdir -p OpenVPN_Client >> /dev/null
    echo 'Creating client OpenVPN configuration for team: '$1
    cat > OpenVPN_Client/team$1.$2.client.conf <<EOF
    # Hackfest 2013 War Game
    # Team: $1

    client
    tls-client
    dev tun
    proto udp
    
    remote 10.$1.25.11 1194 # Change to your router's External IP
    resolv-retry infinite
    nobind
    
    persist-tun
    persist-key
    
    ca keys/ca.crt
    cert keys/team$1.$2.client.crt
    key keys/team$1.$2.client.key
    dh keys/dh1024.pem
    
    verb 3
EOF

  build_client_key $1 $2

  echo -e "${GREEN_COLOR}Creation of key and configuration completed!! ${NOCOLOR}"
  
  echo -e "${PURPLE_COLOR}Creating zip package with all requested file ${NOCOLOR}"
  zip -j0 OpenVPN_Client/team$1.$2.client.zip CA/ca.crt CA/dh1024.pem OpenVPN_Client/team$1.$2.* 
  rm -f OpenVPN_Client/team$1.$2.client.crt OpenVPN_Client/team$1.$2.client.key OpenVPN_Client/team$1.$2.client.conf
  echo -e "${GREEN_COLOR}Package created :team$1.$2.client.zip  ${NOCOLOR}"
  
  echo -e "${PURPLE_COLOR}Add Certificate Common Name to Team server${NOCOLOR}"
  ssh root@10.$1.25.11 "touch /etc/openvpn/client-config-dir/Team_$1_cltcert-$2 "
}

# Menu, arguments, help
while test $# -gt 0; do
        case "$1" in
                --help)
			usage
                        exit 0
                        ;;
                --all)
			export ALL=1
                        shift
                        ;;
                -i)
                        shift
                        if test $# -gt 0; then
                                export ID=$1
                        else
                                echo "no id specified"
                                exit 1
                        fi
                        shift
                        ;;
                --id*)
                        export ID=`echo $1 | sed -e 's/^[^=]*=//g'`
                        shift
                        ;;
                *)
                        break
                        ;;
        esac

done

# Some validations

if [ -z $ALL ]
then
    if [ -z $ID ]
    then
        usage
        echo There are missing arguments
        exit 1
    fi
    
    echo -e "${RED_COLOR}Please enter an identification name (your_choice) for the key and configuration file :${NOCOLOR}"
    echo -e "${GREEN_COLOR}Example of name : TeamX.your_choice.client.ovpn ${NOCOLOR}"
    read user_name
    create_conf $ID $user_name


else
    echo -e "${RED_COLOR}Please enter an identification name (your_choice) for the key and configuration file :${NOCOLOR}"
    echo -e "${GREEN_COLOR}Example of name : TeamX.your_choice.client.ovpn ${NOCOLOR}"
    read user_name
    create_conf $ID $user_name
    for (( i=1; i <= 8; i++ ))
    do
        create_conf $i $user_name
    done
fi

exit 0
