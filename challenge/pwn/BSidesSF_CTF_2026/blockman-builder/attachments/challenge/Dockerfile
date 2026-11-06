FROM debian:bookworm

RUN apt-get update -y && \
    apt-get install -y socat libncursesw6 locales

RUN sed -i 's/^# *en_US.UTF-8 UTF-8/en_US.UTF-8 UTF-8/' /etc/locale.gen && locale-gen
ENV LANG=en_US.UTF-8
ENV LC_ALL=en_US.UTF-8

# The current user
RUN useradd -r ctf -u 1000

# This is where everything lives
ENV APP_HOME=/home/ctf

# The binary name
ENV BIN_NAME=bmb

# Set up the directory
RUN mkdir $APP_HOME
RUN chown ctf:ctf $APP_HOME
WORKDIR $APP_HOME

# Copy up the binary
COPY src/$BIN_NAME $APP_HOME/$BIN_NAME
RUN chown root:root $APP_HOME/$BIN_NAME
RUN chmod 0755 $APP_HOME/$BIN_NAME

# Copy up the level
COPY src/level.txt $APP_HOME/level.txt
RUN chown root:root $APP_HOME/level.txt
RUN chmod 0444 $APP_HOME/level.txt

# Copy up the keys-us
COPY src/keys-us.txt $APP_HOME/keys-us.txt
RUN chown root:root $APP_HOME/keys-us.txt
RUN chmod 0444 $APP_HOME/keys-us.txt

# Copy up the flag
COPY flag.txt $APP_HOME/flag.txt
RUN chown root:root $APP_HOME/flag.txt
RUN chmod 0444 $APP_HOME/flag.txt

# Copy up the wrappers
COPY src/start.sh $APP_HOME/start.sh
COPY src/bmb_tty.sh $APP_HOME/bmb_tty.sh
RUN chown root:root $APP_HOME/*.sh
RUN chmod 0755 $APP_HOME/*.sh


# Switch to our user
USER 1000

EXPOSE 1184

# Start server
ENTRYPOINT ["/home/ctf/start.sh"]

# You can build and start a testing copy of this container with something like:
# docker buildx build . --progress=plain -t test && docker run --rm -it -p 1184:1184 test

# Once built and started, you can connect to the service to test with something like:
# socat STDIO,raw,echo=0,escape=0x03 TCP:localhost:1184
