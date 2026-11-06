FROM debian:bookworm

RUN apt-get update -y && \
    apt-get install -y socat libncurses6 locales

RUN sed -i 's/^# *en_US.UTF-8 UTF-8/en_US.UTF-8 UTF-8/' /etc/locale.gen && locale-gen
ENV LANG=en_US.UTF-8
ENV LC_ALL=en_US.UTF-8

# The current user
RUN useradd -r ctf -u 1000

# This is where everything lives
ENV APP_HOME=/home/ctf

# The binary name
ENV BIN_NAME=wromwarp

# Set up the directory
RUN mkdir $APP_HOME
RUN chown ctf:ctf $APP_HOME
WORKDIR $APP_HOME

# Copy up the binary
COPY src/$BIN_NAME $APP_HOME/$BIN_NAME
RUN chown root:root $APP_HOME/$BIN_NAME
RUN chmod 0755 $APP_HOME/$BIN_NAME

# Copy up the games
COPY src/roms/ $APP_HOME/roms/
RUN rm $APP_HOME/roms/printflag.les
RUN chown root:root $APP_HOME/roms
RUN chown root:root $APP_HOME/roms/*
RUN chmod 0555 $APP_HOME/roms
RUN chmod 0444 $APP_HOME/roms/*

# Copy up the WRAM
COPY src/WRAM.bin $APP_HOME/WRAM.bin
RUN chown root:root $APP_HOME/WRAM.bin
RUN chmod 0444 $APP_HOME/WRAM.bin

# Copy up the logo
COPY src/les_logo.txt $APP_HOME/les_logo.txt
RUN chown root:root $APP_HOME/les_logo.txt
RUN chmod 0444 $APP_HOME/les_logo.txt

# Copy up the wrappers
COPY src/start.sh $APP_HOME/start.sh
COPY src/wromwarp_tty.sh $APP_HOME/wromwarp_tty.sh
RUN chown root:root $APP_HOME/*.sh
RUN chmod 0755 $APP_HOME/*.sh


# Switch to our user
USER 1000

EXPOSE 6502

# Start server
ENTRYPOINT ["/home/ctf/start.sh"]

# You can build and start a testing copy of this container with something like:
# docker buildx build . --progress=plain -t test && docker run --rm -it -p 6502:6502 test

# Once built and started, you can connect to the service to test with something like:
# socat STDIO,raw,echo=0,escape=0x03 TCP:localhost:6502
