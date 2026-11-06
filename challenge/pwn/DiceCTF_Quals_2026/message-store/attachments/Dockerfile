FROM ubuntu:24.04 AS app

FROM pwn.red/jail
COPY --from=app / /srv
RUN mkdir /srv/app
COPY challenge /srv/app/run
COPY flag.txt /srv/app
RUN chmod 755 /srv/app/run

ENV JAIL_POW=30000
