FROM ubuntu:22.04 as build

RUN apt-get update -y; apt-get install build-essential zlib1g-dev python3 -y
ADD war-hymn.c /tmp/war-hymn.c
ADD decrypt.c /tmp/decrypt.c
ADD shared.c /tmp/shared.c
ADD perform_zlib_compression.py /tmp/perform_zlib_compression.py
ADD make_encrypted_zlib.py /tmp/make_encrypted_zlib.py
ADD Makefile /tmp/Makefile
RUN cd /tmp/; make compile