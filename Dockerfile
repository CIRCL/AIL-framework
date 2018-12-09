FROM ubuntu:16.04

# Make sure that all updates are in place
RUN apt-get clean && apt-get update -y && apt-get upgrade -y \
        && apt-get dist-upgrade -y && apt-get autoremove -y

# Install needed packages
RUN apt-get install git python-dev build-essential \
       libffi-dev libssl-dev libfuzzy-dev wget sudo -y

# Adding sudo command
RUN useradd -m docker && echo "docker:docker" | chpasswd && adduser docker sudo
RUN echo "root ALL=(ALL) NOPASSWD: ALL" >> /etc/sudoers

# Installing AIL dependencies
RUN mkdir /opt/AIL
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

COPY docker_start.sh /docker_start.sh
ENTRYPOINT ["/bin/bash", "docker_start.sh"]
