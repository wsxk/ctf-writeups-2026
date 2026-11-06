#!/bin/bash

objcopy --add-section bmb.c=bmb.c \
        --set-section-flags bmb.c=noload,readonly \
        bmb bmb.src

mv bmb.src bmb
