FROM debian:bookworm

RUN apt-get update -y && \
    apt-get install -y socat

# The current user
RUN useradd -r ctf -u 1000

# This is where everything lives
ENV APP_HOME=/home/ctf

# The binary name
ENV BIN_NAME=nameme

# Set up the directory
RUN mkdir $APP_HOME
RUN chown ctf:ctf $APP_HOME
WORKDIR $APP_HOME

# Copy up the binary
COPY src/$BIN_NAME $APP_HOME/$BIN_NAME
RUN chown root:root $APP_HOME/$BIN_NAME
RUN chmod 0755 $APP_HOME/$BIN_NAME

# Copy up the flag
COPY flag.txt $APP_HOME/flag.txt
RUN chown root:root $APP_HOME/flag.txt
RUN chmod 0444 $APP_HOME/flag.txt

# Copy up the hostlist
COPY host.list $APP_HOME/host.list
RUN chown root:root $APP_HOME/host.list
RUN chmod 0444 $APP_HOME/host.list

# Switch to our user
USER 1000

EXPOSE 4444

# Start server
ENTRYPOINT ["socat", "UDP-LISTEN:53535,reuseaddr,fork", "EXEC:'/home/ctf/nameme'"]

# You can build and start a testing copy of this container with something like:
# docker buildx build . --progress=plain -t test && docker run --rm -it -p 4444:4444 test

# Once built and started, you can connect to the service to test with something like:
# ncat localhost 4444
