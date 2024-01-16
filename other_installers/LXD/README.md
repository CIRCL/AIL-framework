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

## Configuration
If you installed Lacus, you can configure AIL to use it as a crawler. For further information, please refer to the [HOWTO](https://github.com/ail-project/ail-framework/blob/master/HOWTO.md)
