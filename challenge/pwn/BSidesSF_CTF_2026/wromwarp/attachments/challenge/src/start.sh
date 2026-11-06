#!/bin/bash

cd /home/ctf/

socat "TCP-LISTEN:6502,reuseaddr,fork" "EXEC:'./wromwarp_tty.sh',pty,stderr,setsid,sigint,sane"
