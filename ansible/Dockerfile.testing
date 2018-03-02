FROM ubuntu:latest

# Install Ansible
RUN apt-get -y update && \
	apt-get -y install \
		software-properties-common && \
	apt-add-repository ppa:ansible/ansible && \
	apt-get update && \
	apt-get -y install ansible

# Add the playbook
ADD . /tmp/AIL-framework-ansible

# Run the AIL role on localhost
RUN ansible-playbook /tmp/AIL-framework-ansible/deployLocal.yml -c local
