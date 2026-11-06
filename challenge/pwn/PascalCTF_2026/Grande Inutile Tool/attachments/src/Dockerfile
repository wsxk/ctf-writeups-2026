FROM ubuntu:24.04

ARG FLAG
ARG ADMIN_PASSWORD

RUN apt-get update && apt-get install -y \
    openssh-server \
    sudo \
    libcap2-bin \
    && rm -rf /var/lib/apt/lists/* \
    && mkdir /var/run/sshd

COPY mygit /usr/bin/mygit
RUN chown root:root /usr/bin/mygit && chmod 4755 /usr/bin/mygit

RUN echo "${FLAG}" > /flag \
    && chmod 400 /flag

RUN useradd -m -s /bin/bash admin \
    && echo "admin:${ADMIN_PASSWORD}" | chpasswd \
    && echo "admin ALL=(root) NOPASSWD: /usr/sbin/useradd, /usr/sbin/chpasswd" >> /etc/sudoers

RUN sed -i 's/#PermitRootLogin prohibit-password/PermitRootLogin no/' /etc/ssh/sshd_config \
    && sed -i 's/#PasswordAuthentication yes/PasswordAuthentication yes/' /etc/ssh/sshd_config

RUN chmod 700 /tmp \
    && chown root:root /tmp \
    && rm -rf /var/tmp \
    && mkdir /var/tmp \
    && chmod 700 /var/tmp \
    && chown root:root /var/tmp

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 22

CMD ["/entrypoint.sh"]