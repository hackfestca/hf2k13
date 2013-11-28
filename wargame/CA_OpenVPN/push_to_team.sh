#!/bin/bash
# This script do magic!! On each server of the 8 teams, it does :
# - Install OpenVPN
# - Create folder structure
# - Create conf file for the OpenVPN server
# - Copy file created (with install_config_OpenVPN.sh script) on the server
# - Start OpenVPN

usage()
{
    echo "Push an openvpn config"
    echo " "
    echo "$0 -i ID"
    echo " "
    echo "options:"
    echo "--help                    show brief help"
    echo "-i, --id=ID               team id (ex: 1..8)"
    echo "--all                     do it for all teams!"
    echo ""
}

push()
{
    echo 'Pushing on team: '$1
    cat > files/openvpn.team$1.conf <<EOF
    # Hackfest 2013 War Game
    # Team: $1

    mode server
    tls-server
    
    ### network options
    port 1194
    proto udp
    dev tun
    
    ### Certificate and key files
    ca /etc/openvpn/keys/ca.crt
    cert /etc/openvpn/keys/server.crt
    key /etc/openvpn/keys/server.key
    dh /etc/openvpn/keys/dh1024.pem
    #tls-auth /etc/openvpn/keys/shared.key
    
    server 10.$1.30.0 255.255.255.0
    push "route 10.$1.25.0 255.255.255.0"
    push "route 192.168.4$1.0 255.255.255.0"
    push "redirect-gateway"
    
    persist-key
    persist-tun
    
    verb 3
    keepalive 10 120
    log-append /var/log/openvpn/openvpn.log
    status /var/log/openvpn/status.log

    client-config-dir /etc/openvpn/client-config-dir
    ccd-exclusive
    
EOF

    # Push the shit!
#    scp /etc/resolv.conf root@10.$1.25.11:/etc/resolv.conf
# ssh root@10.$1.25.11 "aptitude update"
    ssh root@10.$1.25.11 "aptitude install -y openvpn"
    ssh root@10.$1.25.11 "mkdir -p /etc/openvpn/keys"
    ssh root@10.$1.25.11 "chmod -R 700 /etc/openvpn/keys"
    ssh root@10.$1.25.11 "mkdir -p /etc/openvpn/client-config-dir"
    ssh root@10.$1.25.11 "chmod -R 700 /etc/openvpn/client-config-dir"
    ssh root@10.$1.25.11 "mkdir -p /var/log/openvpn"
    ssh root@10.$1.25.11 "chmod o-rwx /etc/openvpn/keys"
    scp CA/ca.crt  root@10.$1.25.11:/etc/openvpn/keys/
    scp CA/Team$1/*  root@10.$1.25.11:/etc/openvpn/keys/
    scp files/openvpn.team$1.conf  root@10.$1.25.11:/etc/openvpn/openvpn.conf
    scp CA/dh1024.pem  root@10.$1.25.11:/etc/openvpn/keys/
    
    ssh root@10.$1.25.11 "/etc/init.d/openvpn restart"
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
                        #if test $# -gt 0; then
                        #        export OUT_FILE=$1
                        #else
                        #        echo "no file specified"
                        #        exit 1
                        #fi
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
    push $ID
else
    for (( i=1; i <= 8; i++ ))
    do
        push $i
    done
fi

exit 0
