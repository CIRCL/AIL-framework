:warning:
Not maintained at the moment.
If you are interested to get this running, please:

Fork -> Branch -> PR

In case of questions please Join our [GITTER](https://gitter.im/SteveClement/AIL-framework) chat.

# AIL-framework-ansible
This Ansible role can be used to deploy the AIL-Framework on a host.

## Usage
- Create a folder called `inventories`
- In this folder, create an inventory called `develop` with the following content:

```
[ail]
<Your server IP(s) separated by newlines>

[ail:vars]
ansible_ssh_private_key_file=<Path to your private SSH key for the server(s)>

```
- Grab the latest `bin/packages/config.cfg.sample` file from the AIL repository and modify it to so it fits your needs. Then, place it in `roles/ail-host/files/config.cfg`.
- Make sure the SSH service is reachable and that python is installed on the remote host(s) for Ansible to work
- Run `deploy.sh`

## Starting/Stopping AIL

All AIL components are available as systemd services.

Use `systemctl {start, stop} ail-redis ail-leveldb ail-logging ail-queues ail-scripts ail-flask` to start/stop specific services.

To start the AIL components manually, the remote scripts in `/opt/AIL-scripts` can also be used. They will be present after using the AIL role.

## Remote user
By default, this Ansible project requires remote root access. However, if you want to use the `become` directive of Ansible,
you can edit the required files as follows:

- In `deploy.sh` add `--ask-become-pass`
- In `deploy.yml` add:

```
become: yes
become_user: root
```

- In `group_vars/ail.yml` change the `remote_user` to the user that will escalate privileges on the remote host(s) using `sudo`.

## Updating thirdparty libraries
To deploy AIL, the thirdparty files in the folder `var/www/static` are shipped along with this project to
minimize the risk of unavailable or unexpected files. If you need to update all these
dependencies, you can use the script `update_thirdparty.sh` which is being shipped along with AIL.

# Testing

It's possible to test the AIL role locally in a docker environment which is also provided in this repository. Please note that as of this version, this tests the playbook until the systemd services are being activated. To also test the deployment of the systemd services you might use an ubuntu image with systemd support (systemd has to have PID 1).

To test this Ansible playbook, execute these commands:

- Start the testing process: `sudo docker build --rm -f Dockerfile.testing -t ail-testing .`
