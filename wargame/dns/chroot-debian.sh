#!/bin/sh

CHROOT=/chroot/bind

mkdir $CHROOT
mkdir -p $CHROOT/etc/bind/master $CHROOT/etc/bind/slave $CHROOT/etc/bind/dnssec-keys
chmod 770 $CHROOT/etc/bind/master $CHROOT/etc/bind/slave
chmod g+s $CHROOT/etc/bind/master $CHROOT/etc/bind/slave
chown bind:bind $CHROOT/etc/bind/master $CHROOT/etc/bind/slave
chown root:bind $CHROOT/etc/bind/dnssec-keys
cp -a /etc/bind/* $CHROOT/etc/bind
rm /etc/bind/*
rmdir /etc/bind
ln -s $CHROOT/etc/bind/ /etc/bind
mkdir -p $CHROOT/dev
rm -f $CHROOT/dev/null $CHROOT/dev/random
mknod $CHROOT/dev/null c 1 3
mknod $CHROOT/dev/random c 1 8
chmod 666 $CHROOT/dev/null
chmod 666 $CHROOT/dev/random
mkdir -p $CHROOT/var/cache $CHROOT/var/log $CHROOT/var/run $CHROOT/var/log/named $CHROOT/var/run/named $CHROOT/var/cache/named
chmod 770 $CHROOT/var/log/named
chmod 775 $CHROOT/var/run/named $CHROOT/var/cache/named
chown root:bind $CHROOT/var/log/named $CHROOT/var/run/named $CHROOT/var/cache/named
