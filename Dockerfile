FROM ubuntu:16.04

RUN mkdir /opt/AIL && apt-get update -y \
	&& apt-get install git python-dev build-essential \
	libffi-dev libssl-dev libfuzzy-dev wget sudo -y

# Adding sudo command
RUN useradd -m docker && echo "docker:docker" | chpasswd && adduser docker sudo
RUN echo "root ALL=(ALL) NOPASSWD: ALL" >> /etc/sudoers

# Installing AIL dependencies
ADD . /opt/AIL
WORKDIR /opt/AIL
RUN ./installing_deps.sh 
WORKDIR /opt/AIL

# Installing Web dependencies,
# remove all the parts below if you dont need the Web UI
WORKDIR /opt/AIL/var/www
RUN ./update_thirdparty.sh
WORKDIR /opt/AIL

# Default to UTF-8 file.encoding
ENV LANG C.UTF-8

RUN ./pystemon/install.sh

COPY docker.sh /docker.sh
ENTRYPOINT ["/bin/bash", "docker.sh"]
