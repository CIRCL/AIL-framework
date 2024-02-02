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

## Using Images to run AIL
If you want to use images to install AIL, you can download them from the ail-project [image website](https://images.ail-project.org/)

After downloading the images, you can import them into LXD using the following command:
```bash
lxc image import <path_to_image> --alias <image_alias>
```
Now you can use the image to create a container:
```bash 
lxc launch <image_alias> <container_name>
```

To log into the container you need to know the automatically generated password. You can get it with the following command:
```bash
lxc exec <container_name> --  bash -c "grep '^password=' /home/ail/ail-framework/DEFAULT_PASSWORD | cut -d'=' -f2"
```

If you also want to use Lacus, you can do the same with the Lacus image. After that, you can configure AIL to use Lacus as a crawler. For further information, please refer to the [HOWTO.md](https://github.com/ail-project/ail-framework/blob/master/HOWTO.md).

## Building the images locally
If you want to build the images locally, you can use the `build.sh` script:
```bash
bash build.sh [OPTIONS]
```
| Flag                            | Default Value | Description                                                                       |
| ------------------------------- | ------------- | --------------------------------------------------------------------------------- |
| `--ail`                         | `false`       | Activates the creation of the AIL container.                                      |
| `--lacus`                       | `false`       | Activates the creation of the Lacus container.                                    |
| `--ail-name <container_name>`   | `AIL`         | Specifies the name of the AIL container. The default is a generic name "AIL".     |
| `--lacus-name <container_name>` | `Lacus`       | Specifies the name of the Lacus container. The default is a generic name "Lacus". |
| `-o`, `--outputdir <directory>` | `<none>`      | Sets the output directory for the LXD image files.                                |
| `-s`, `--sign`                  | `false`       | Enables the signing of the generated LXD image files.                             |
