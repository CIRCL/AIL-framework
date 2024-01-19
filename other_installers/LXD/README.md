# AIL-framework-LXD
This installer is based on the [LXD](https://canonical.com/lxd) container manager and can be used to install AIL on Linux. It also supports the installation of [Lacus](https://github.com/ail-project/lacus) a crawler for the AIL framework.

## Requirements
- [LXD](https://canonical.com/lxd) 5.19
- jq 1.6

## Usage
Make sure you have all the requirements installed on your system. 

### Interactive mode
Run the INSTALL.sh script with the --interactive flag to enter the interactive mode, which guides you through the configuration process:
```bash
bash INSTALL.sh --interactive
```

### Non-interactive mode
If you want to install AIL without the interactive mode, you can use the following command:
```bash
bash INSTALL.sh [OPTIONS]
```

The following options are available:
| Flag                            | Default Value           | Description                                                              |
| ------------------------------- | ----------------------- | ------------------------------------------------------------------------ |
| `-i`, `--interactive`           | N/A                     | Activates an interactive installation process.                           |
| `--project <project_name>`      | `AIL-<creation_time>`   | Name of the LXD project for organizing and running the containers.       |
| `--ail-name <container_name>`   | `AIL-<creation_time>`   | The name of the container responsible for running the AIL application.   |
| `--no-lacus`                    | `false`                 | Determines whether to install the Lacus container.                       |
| `--lacus-name <container_name>` | `LACUS-<creation_time>` | The name of the container responsible for running the Lacus application. |
| `--partition <partition>`       | `<none>`                | Dedicated partition for LXD-project storage.                             |


## Configuration
If you installed Lacus, you can configure AIL to use it as a crawler. For further information, please refer to the [HOWTO.md](https://github.com/ail-project/ail-framework/blob/master/HOWTO.md)
