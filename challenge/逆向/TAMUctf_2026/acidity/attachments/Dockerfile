# FROM debian:trixie-20260112-slim AS build

# ARG name

# RUN apt-get update -y; apt-get install build-essential -y
# ADD src/game.cpp /tmp/game.cpp
# ADD src/obfuscate.h /tmp/obfuscate.h
# ADD Makefile /tmp/Makefile
# RUN cd /tmp/; make all

FROM debian:trixie-20260112-slim

ARG name
ARG port

RUN apt-get update -y; apt-get install socat -y
COPY build/acidity /pwn/game
RUN chmod +x /pwn/game
COPY flag.txt /pwn/flag.txt
WORKDIR /pwn

EXPOSE $port

RUN echo "exec socat -s TCP-LISTEN:$port,reuseaddr,fork EXEC:'timeout -k 1 60 /pwn/game,stderr'" > /pwn/docker_entrypoint.sh

ENTRYPOINT ["sh", "/pwn/docker_entrypoint.sh"]