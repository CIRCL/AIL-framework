FROM ubuntu:14.04

RUN mkdir /opt/AIL && apt-get update -y \
	&& apt-get install git python-dev build-essential \
	libffi-dev libssl-dev libfuzzy-dev wget -y
ADD . /opt/AIL
WORKDIR /opt/AIL
RUN ./installing_deps.sh && cd var/www/ && ./update_thirdparty.sh
CMD bash docker_start.sh
