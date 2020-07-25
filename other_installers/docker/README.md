Docker Quick Start (Ubuntu 18.04 LTS)
------------

:warning:
Not maintained at the moment.
If you are interested to get this running, please:

Fork -> Branch -> PR


1. Install Docker
```bash
sudo su
apt-get install -y curl
curl https://get.docker.com | /bin/bash
```

2. Type these commands to build the Docker image:
```bash
git clone https://github.com/CIRCL/AIL-framework.git
cd AIL-framework
cp -r ./other_installers/docker/Dockerfile ./other_installers/docker/docker_start.sh ./other_installers/docker/pystemon ./
docker build -t ail-framework .
```
3. To start AIL on port 7000, type the following command below:
```
docker run -p 7000:7000 ail-framework
```

4. To debug the running container, type the following command and note the container name or identifier:
```bash
docker ps
```

After getting the name or identifier type the following commands:
```bash
docker exec -it CONTAINER_NAME_OR_IDENTIFIER bash
cd /opt/ail
```

Install using Ansible
---------------------

Please check the [Ansible readme](ansible/README.md).

