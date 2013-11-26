#!/bin/bash
rm /root/stream/feed1.avi
ffserver -f /root/stream/server.conf &
ffmpeg -r 5 -s 320x240 -f video4linux2 -i /dev/video0 http://localhost/feed1.ffm /root/stream/feed1.avi
#ffmpeg -r 5 -s 640x480 -f video4linux2 -i /dev/video0 http://localhost/feed1.ffm feed1.avi
