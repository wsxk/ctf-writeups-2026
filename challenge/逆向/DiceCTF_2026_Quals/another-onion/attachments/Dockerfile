FROM fedora:42

RUN dnf -y install \
    binutils \
    ca-certificates \
    clang \
    gdb \
    python3 \
    && dnf clean all

WORKDIR /app
COPY instance_server.py /app/
COPY generate.py /app/
COPY encrypt.py /app/
COPY compile.sh /app/

RUN chmod +x compile.sh

ENV HTTP_PORT=8000
ENV TOKEN_PORT=31337
ENV PACK_NAME=instance
ENV BINARY_ROUTE=/binary
ENV BINARY_FILENAME=another_onion
ENV TOKEN_BYTES=16
ENV NSEGMENTS=256
ENV FLAG=dice{set_me}

EXPOSE 8000 31337

CMD ["python3", "instance_server.py"]
