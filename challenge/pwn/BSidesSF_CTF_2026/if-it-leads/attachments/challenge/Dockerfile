FROM debian:bookworm

RUN apt-get update
RUN apt-get install -y socat ruby python3 vim nano
RUN apt-get install -y bsdmainutils xxd

# The current user
RUN useradd -r ctf -u 1000

# This is where everything lives
ENV APP_HOME=/home/ctf

# Set up the directory
RUN mkdir $APP_HOME
RUN chown ctf:ctf $APP_HOME
RUN chmod 0777 $APP_HOME
WORKDIR $APP_HOME

# Add a target user
RUN useradd -r target -u 1001

# Copy up the binary, setuid to the target user
COPY src/if-it-leads $APP_HOME/if-it-leads
RUN chown target:target $APP_HOME/if-it-leads
RUN chmod 0555 $APP_HOME/if-it-leads
RUN chmod +s $APP_HOME/if-it-leads

# Copy up the source for reference
COPY src/if-it-leads.c $APP_HOME/if-it-leads.c
RUN chown ctf:ctf $APP_HOME/if-it-leads.c
RUN chmod 0644 $APP_HOME/if-it-leads.c

# Copy the .bash_profile
COPY bash_profile $APP_HOME/.bash_profile
RUN chown ctf:ctf $APP_HOME/.bash_profile
RUN chmod +x $APP_HOME/.bash_profile

# Copy up the flag and password, and make sure only target can read it
COPY flag.txt /home/ctf/flag.txt
RUN chown target:target /home/ctf/flag.txt
RUN chmod 0400 /home/ctf/flag.txt

COPY password.txt /home/ctf/password.txt
RUN chown target:target /home/ctf/password.txt
RUN chmod 0400 /home/ctf/password.txt

# Switch to our user
USER 1000

# Start server
ENTRYPOINT ["socat", "TCP-LISTEN:4445,reuseaddr,fork", "EXEC:'/bin/bash -li',pty,stderr,setsid,sane"]
