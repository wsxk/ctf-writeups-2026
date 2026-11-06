#!/bin/bash

cd /home/ctf/

socat "TCP-LISTEN:1184,reuseaddr,fork" "EXEC:'./bmb_tty.sh',pty,stderr,setsid,sigint,sane"
