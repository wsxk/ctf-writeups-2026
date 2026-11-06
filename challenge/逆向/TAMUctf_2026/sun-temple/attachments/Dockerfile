# FROM debian@sha256:1d3c811171a08a5adaa4a163fbafd96b61b87aa871bbc7aa15431ac275d3d430 AS build

# ARG name

# RUN apt-get update -y; apt-get install build-essential -y
# ADD src/generated_chamber.h /tmp/generated_chamber.h
# ADD src/sun-temple.c /tmp/sun-temple.c
# ADD Makefile /tmp/Makefile
# RUN cd /tmp/; make all

FROM debian@sha256:1d3c811171a08a5adaa4a163fbafd96b61b87aa871bbc7aa15431ac275d3d430

ARG name
ARG port

RUN apt-get update -y; apt-get install socat -y
COPY target/sun-temple /pwn/sun-temple
RUN chmod +x /pwn/sun-temple
COPY flag.txt /pwn/flag.txt
WORKDIR /pwn

EXPOSE $port

RUN echo "exec socat -s TCP-LISTEN:$port,reuseaddr,fork EXEC:'timeout -k 1 60 /pwn/sun-temple,stderr'" > /pwn/docker_entrypoint.sh

ENTRYPOINT ["sh", "/pwn/docker_entrypoint.sh"]