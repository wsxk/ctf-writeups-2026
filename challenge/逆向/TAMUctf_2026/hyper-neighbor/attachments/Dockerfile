FROM alpine AS chal

RUN apk add alpine-sdk util-linux-misc

FROM pwn.red/jail

COPY --from=chal / /srv
COPY init.sh /srv/app/run

ENV JAIL_TIME=300
ENV JAIL_MEM=32M
ENV JAIL_CPU=0
ENV JAIL_PIDS=16
ENV JAIL_POW=6000
ENV JAIL_TMP_SIZE=128M

ARG shell_port
ENV JAIL_PORT=${shell_port}
