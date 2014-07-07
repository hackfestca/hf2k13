#!/bin/bash

/etc/init.d/ntp stop

rootfs=/chroot/ntp
mkdir -p $rootfs/{etc,var/lib/ntp,var/log}

mv /etc/ntp.conf $rootfs/etc
ln -s $rootfs/etc/ntp.conf /etc/ntp.conf

if [ -e /var/lib/ntp/ntp.drift ]; then
	mv /var/lib/ntp/ntp.drift $rootfs/var/lib/ntp
fi

ln -s $rootfs/var/lib/ntp/ntp.drift /var/lib/ntp/ntp.drift
chown -R ntp:ntp $rootfs/var/lib/ntp

mv /var/log/ntpstats $rootfs/var/log
ln -s $rootfs/var/log/ntpstats /var/log/ntpstats
chown -R ntp:ntp $rootfs/var/log/ntpstats

sed -e "s,'-g','-i $rootfs -g'," /etc/default/ntp > /tmp/x
mv /tmp/x /etc/default/ntp

/etc/init.d/ntp start
