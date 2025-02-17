#!/bin/bash

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

setVars() {
    STORAGE_POOL_NAME=$(generateName "AIL")
    NETWORK_NAME=$(generateName "AIL")
    NETWORK_NAME=${NETWORK_NAME:0:14}
    PROFILE=$(generateName "AIL")

    UBUNTU="ubuntu:24.04"
}

setDefaults(){
    default_ail_project=$(generateName "AIL")
    default_ail_name=$(generateName "AIL")
    default_lacus="Yes"
    default_lacus_name=$(generateName "LACUS")
    default_partition=""
}

error() {
    echo -e "${RED}ERROR: $1${NC}"
}

warn() {
    echo -e "${YELLOW}WARNING: $1${NC}"
}

info() {
    echo -e "${BLUE}INFO: $1${NC}"
}

success() {
    echo -e "${GREEN}SUCCESS: $1${NC}"
}

err() {
    local parent_lineno="$1"
    local message="$2"
    local code="${3:-1}"

    if [[ -n "$message" ]] ; then
        error "Line ${parent_lineno}: ${message}: exiting with status ${code}"
    else
        error "Line ${parent_lineno}: exiting with status ${code}"
    fi

    deleteLXDProject "$PROJECT_NAME"
    lxc storage delete "$APP_STORAGE"
    lxc storage delete "$DB_STORAGE"
    lxc network delete "$NETWORK_NAME"
    exit "${code}"
}

generateName(){
    local name="$1"
    echo "${name}-$(date +%Y%m%d%H%M%S)"
}

setupLXD(){
    lxc project create "$PROJECT_NAME"
    lxc project switch "$PROJECT_NAME"

    if checkRessourceExist "storage" "$STORAGE_POOL_NAME"; then
        error "Storage '$STORAGE_POOL_NAME' already exists."
        exit 1
    fi
    lxc storage create "$STORAGE_POOL_NAME" zfs source="$PARTITION"

    if checkRessourceExist "network" "$NETWORK_NAME"; then
        error "Network '$NETWORK_NAME' already exists."
    fi
    lxc network create "$NETWORK_NAME" --type=bridge

    if checkRessourceExist "profile" "$PROFILE"; then
        error "Profile '$PROFILE' already exists."
    fi
    lxc profile create "$PROFILE"
    lxc profile device add "$PROFILE" root disk path="/" pool="$STORAGE_POOL_NAME"
    lxc profile device add "$PROFILE" eth0 nic name=eth0 network="$NETWORK_NAME"
}

waitForContainer() {
    local container_name="$1"

    sleep 3
    while true; do
        status=$(lxc list --format=json | jq -e --arg name "$container_name"  '.[] | select(.name == $name) | .status')
        if [ "$status" = "\"Running\"" ]; then
            echo -e "${BLUE}$container_name ${GREEN}is running.${NC}"
            break
        fi
        echo "Waiting for $container_name container to start."
        sleep 5
    done
}

interrupt() {
    warn "Script interrupted by user. Delete project and exit ..."
    deleteLXDProject "$PROJECT_NAME"
    lxc network delete "$NETWORK_NAME"
    exit 130
}

deleteLXDProject(){
    local project="$1"

    echo "Starting cleanup ..."
    echo "Deleting container in project"
    for container in $(lxc query "/1.0/containers?recursion=1&project=${project}" | jq .[].name -r); do
        lxc delete --project "${project}" -f "${container}"
    done

    echo "Deleting images in project"
    for image in $(lxc query "/1.0/images?recursion=1&project=${project}" | jq .[].fingerprint -r); do
        lxc image delete --project "${project}" "${image}"
    done

    echo "Deleting profiles in project"
    for profile in $(lxc query "/1.0/profiles?recursion=1&project=${project}" | jq .[].name -r); do
    if [ "${profile}" = "default" ]; then
        printf 'config: {}\ndevices: {}' | lxc profile edit --project "${project}" default
        continue
    fi
    lxc profile delete --project "${project}" "${profile}"
    done

    echo "Deleting project"
    lxc project delete "${project}"
}

createAILContainer(){
    lxc launch $UBUNTU "$AIL_CONTAINER" --profile "$PROFILE"
    waitForContainer "$AIL_CONTAINER"
    lxc exec "$AIL_CONTAINER" -- sed -i "/#\$nrconf{restart} = 'i';/s/.*/\$nrconf{restart} = 'a';/" /etc/needrestart/needrestart.conf
    lxc exec "$AIL_CONTAINER" -- apt update
    lxc exec "$AIL_CONTAINER" -- apt upgrade -y
    lxc exec "$AIL_CONTAINER" -- useradd -m -s /bin/bash ail
    if lxc exec "$AIL_CONTAINER" -- id ail; then
        lxc exec "$AIL_CONTAINER" -- usermod -aG sudo ail
        success "User ail created."
    else
        error "User ail not created."
        exit 1
    fi
    lxc exec "$AIL_CONTAINER" -- bash -c "echo 'ail ALL=(ALL) NOPASSWD: ALL' | sudo tee /etc/sudoers.d/ail"
    lxc exec "$AIL_CONTAINER" --cwd=/home/ail -- sudo -u ail bash -c "git clone https://github.com/ail-project/ail-framework.git"
    lxc exec "$AIL_CONTAINER" --cwd=/home/ail/ail-framework -- sudo -u ail bash -c "./installing_deps.sh"
    lxc exec "$AIL_CONTAINER" -- sed -i '/^\[Flask\]/,/^\[/ s/host = 127\.0\.0\.1/host = 0.0.0.0/' /home/ail/ail-framework/configs/core.cfg
    lxc exec "$AIL_CONTAINER" --cwd=/home/ail/ail-framework/bin -- sudo -u ail bash -c "./LAUNCH.sh -l"
    lxc exec "$AIL_CONTAINER" -- sed -i "/^\$nrconf{restart} = 'a';/s/.*/#\$nrconf{restart} = 'i';/" /etc/needrestart/needrestart.conf
}

createLacusContainer(){
    lxc launch $UBUNTU "$LACUS_CONTAINER" --profile "$PROFILE"
    waitForContainer "$LACUS_CONTAINER"
    lxc exec "$LACUS_CONTAINER" -- sed -i "/#\$nrconf{restart} = 'i';/s/.*/\$nrconf{restart} = 'a';/" /etc/needrestart/needrestart.conf
    lxc exec "$LACUS_CONTAINER" -- apt update
    lxc exec "$LACUS_CONTAINER" -- apt upgrade -y
    lxc exec "$LACUS_CONTAINER" -- apt install pipx -y
    lxc exec "$LACUS_CONTAINER" -- pipx install poetry 
    lxc exec "$LACUS_CONTAINER" -- pipx ensurepath
    lxc exec "$LACUS_CONTAINER" -- apt install build-essential tcl ffmpeg libavcodec-extra -y
    lxc exec "$LACUS_CONTAINER" -- git clone https://github.com/valkey-io/valkey.git
    lxc exec "$LACUS_CONTAINER" --cwd=/root/valkey -- git checkout 8.0
    lxc exec "$LACUS_CONTAINER" --cwd=/root/valkey -- make
    lxc exec "$LACUS_CONTAINER" -- git clone https://github.com/ail-project/lacus.git
    lxc exec "$LACUS_CONTAINER" --cwd=/root/lacus -- /root/.local/bin/poetry install
    AIL_VENV_PATH=$(lxc exec "$LACUS_CONTAINER" --cwd=/root/lacus -- bash -c "/root/.local/bin/poetry env info -p")
    lxc exec "$LACUS_CONTAINER" --cwd=/root/lacus -- bash -c "source ${AIL_VENV_PATH}/bin/activate && playwright install-deps"
    lxc exec "$LACUS_CONTAINER" --cwd=/root/lacus -- bash -c "echo LACUS_HOME=/root/lacus >> .env"
    lxc exec "$LACUS_CONTAINER" --cwd=/root/lacus -- bash -c "export PATH='/root/.local/bin:$PATH' && echo 'no' | /root/.local/bin/poetry run update --init"
    # Install Tor
    lxc exec "$LACUS_CONTAINER" -- apt install apt-transport-https -y
    lxc exec "$LACUS_CONTAINER" -- bash -c "echo 'deb [signed-by=/usr/share/keyrings/tor-archive-keyring.gpg] https://deb.torproject.org/torproject.org $(lsb_release -cs) main' >> /etc/apt/sources.list.d/tor.list"
    lxc exec "$LACUS_CONTAINER" -- bash -c "echo 'deb-src [signed-by=/usr/share/keyrings/tor-archive-keyring.gpg] https://deb.torproject.org/torproject.org $(lsb_release -cs) main' >> /etc/apt/sources.list.d/tor.list"
    lxc exec "$LACUS_CONTAINER" -- bash -c "wget -qO- https://deb.torproject.org/torproject.org/A3C4F0F979CAA22CDBA8F512EE8CBC9E886DDD89.asc | gpg --dearmor | tee /usr/share/keyrings/tor-archive-keyring.gpg > /dev/null"
    lxc exec "$LACUS_CONTAINER" -- apt update
    lxc exec "$LACUS_CONTAINER" -- apt install tor deb.torproject.org-keyring -y
    lxc exec "$LACUS_CONTAINER" -- sed -i "/^\$nrconf{restart} = 'a';/s/.*/#\$nrconf{restart} = 'i';/" /etc/needrestart/needrestart.conf
    # Start Lacus
    lxc exec "$LACUS_CONTAINER" --cwd=/root/lacus -- cp ./config/logging.json.sample ./config/logging.json
    lxc file push ./systemd/lacus.service "$LACUS_CONTAINER"/etc/systemd/system/lacus.service
    lxc exec "$LACUS_CONTAINER" -- systemctl daemon-reload
    lxc exec "$LACUS_CONTAINER" -- systemctl enable lacus.service
    lxc exec "$LACUS_CONTAINER" -- systemctl start lacus.service
}

interactiveConfig(){
    echo
    echo "################################################################################"
    echo -e "# Welcome to the ${BLUE}AIL-framework-LXD${NC} Installer Script                                  #"
    echo "#------------------------------------------------------------------------------#"
    echo -e "# This installer script will guide you through the installation process of     #"
    echo -e "# ${BLUE}AIL${NC} using LXD.                                                              #"
    echo -e "#                                                                              #"
    echo "################################################################################"
    echo
    
    declare -A nameCheckArray

    # Ask for LXD project name
    while true; do 
        read -r -p "Name of the AIL LXD-project (default: $default_ail_project): " ail_project
        PROJECT_NAME=${ail_project:-$default_ail_project}
        if ! checkNamingConvention "$PROJECT_NAME"; then
            continue
        fi
        if checkRessourceExist "project" "$PROJECT_NAME"; then
            error "Project '$PROJECT_NAME' already exists."
            continue
        fi
        break
    done

    # Ask for AIL container name
    while true; do 
        read -r -p "Name of the AIL container (default: $default_ail_name): " ail_name
        AIL_CONTAINER=${ail_name:-$default_ail_name}
        if [[ ${nameCheckArray[$AIL_CONTAINER]+_} ]]; then
            error "Name '$AIL_CONTAINER' has already been used. Please choose a different name."
            continue
        fi
        if ! checkNamingConvention "$AIL_CONTAINER"; then
            continue
        fi
        nameCheckArray[$AIL_CONTAINER]=1
        break
    done

    # Ask for Lacus installation
    read -r -p "Do you want to install Lacus (y/n, default: $default_lacus): " lacus
    lacus=${lacus:-$default_lacus}
    LACUS=$(echo "$lacus" | grep -iE '^y(es)?$' > /dev/null && echo true || echo false)
    if $LACUS; then
        # Ask for LACUS container name
        while true; do
            read -r -p "Name of the Lacus container (default: $default_lacus_name): " lacus_name
            LACUS_CONTAINER=${lacus_name:-$default_lacus_name}
            if [[ ${nameCheckArray[$LACUS_CONTAINER]+_} ]]; then
                error "Name '$LACUS_CONTAINER' has already been used. Please choose a different name."
                continue
            fi
            if ! checkNamingConvention "$LACUS_CONTAINER"; then
                continue
            fi
            nameCheckArray[$LACUS_CONTAINER]=1
            break
        done

    fi

    # Ask for dedicated partitions
    read -r -p "Dedicated partition for AIL LXD-project (leave blank if none): " partition
    PARTITION=${partition:-$default_partition}

    # Output values set by the user
    echo -e "\nValues set:"
    echo "--------------------------------------------------------------------------------------------------------------------"
    echo -e "PROJECT_NAME: ${GREEN}$PROJECT_NAME${NC}"
    echo "--------------------------------------------------------------------------------------------------------------------"
    echo -e "AIL_CONTAINER: ${GREEN}$AIL_CONTAINER${NC}"
    echo "--------------------------------------------------------------------------------------------------------------------"
    echo -e "LACUS: ${GREEN}$LACUS${NC}"
    if $LACUS; then
        echo -e "LACUS_CONTAINER: ${GREEN}$LACUS_CONTAINER${NC}"
        echo "--------------------------------------------------------------------------------------------------------------------"
    fi
    echo -e "PARTITION: ${GREEN}$PARTITION${NC}"
    echo "--------------------------------------------------------------------------------------------------------------------"

    # Ask for confirmation
    read -r -p "Do you want to proceed with the installation? (y/n): " confirm
    confirm=${confirm:-$default_confirm}
    if [[ $confirm != "y" ]]; then
        warn "Installation aborted."
        exit 1
    fi
}

nonInteractiveConfig(){
    VALID_ARGS=$(getopt -o h --long help,production,project:ail-name:,no-lacus,lacus-name:,partition:  -- "$@")
    if [[ $? -ne 0 ]]; then
        exit 1;
    fi

    eval set -- "$VALID_ARGS"
    while [ $# -gt 0 ]; do
        case "$1" in
            -h | --help)
                usage
                exit 0
                ;;
            --partition)
                partition=$2
                shift 2
                ;;
            --project)
                ail_project=$2
                shift 2
                ;;
            --ail-name)
                ail_name=$2
                shift 2
                ;;
            --no-lacus)
                lacus="N"
                shift
                ;;
            --lacus-name)
                lacus_name=$2
                shift 2
                ;;
            *)  
                break 
                ;;
        esac
    done

    # Set global values
    PROJECT_NAME=${ail_project:-$default_ail_project}
    AIL_CONTAINER=${ail_name:-$default_ail_name}
    lacus=${lacus:-$default_lacus}
    LACUS=$(echo "$lacus" | grep -iE '^y(es)?$' > /dev/null && echo true || echo false)
    LACUS_CONTAINER=${lacus_name:-$default_lacus_name}
    PARTITION=${partition:-$default_partition}
}

validateArgs(){
    # Check Names
    local names=("$PROJECT_NAME" "$AIL_CONTAINER")
    for i in "${names[@]}"; do
        if ! checkNamingConvention "$i"; then
            exit 1
        fi
    done

    if $LACUS && ! checkNamingConvention "$LACUS_CONTAINER"; then
        exit 1
    fi

    # Check for Project
    if checkRessourceExist "project" "$PROJECT_NAME"; then
        error "Project '$PROJECT_NAME' already exists."
        exit 1
    fi

    # Check Container Names
    local containers=("$AIL_CONTAINER")

    declare -A name_counts
    for name in "${containers[@]}"; do
    ((name_counts["$name"]++))
    done

    if $LACUS;then
        ((name_counts["$LACUS_CONTAINER"]++))
    fi

    for name in "${!name_counts[@]}"; do
    if ((name_counts["$name"] >= 2)); then
        error "At least two container have the same name: $name"
        exit 1
    fi
    done
}

checkRessourceExist() {
    local resource_type="$1"
    local resource_name="$2"

    case "$resource_type" in
        "container")
            lxc info "$resource_name" &>/dev/null
            ;;
        "image")
            lxc image list --format=json | jq -e --arg alias "$resource_name" '.[] | select(.aliases[].name == $alias) | .fingerprint' &>/dev/null
            ;;
        "project")
            lxc project list --format=json | jq -e --arg name "$resource_name" '.[] | select(.name == $name) | .name' &>/dev/null
            ;;
        "storage")
            lxc storage list --format=json | jq -e --arg name "$resource_name" '.[] | select(.name == $name) | .name' &>/dev/null
            ;;
        "network")
            lxc network list --format=json | jq -e --arg name "$resource_name" '.[] | select(.name == $name) | .name' &>/dev/null
            ;;
        "profile")
            lxc profile list --format=json | jq -e --arg name "$resource_name" '.[] | select(.name == $name) | .name' &>/dev/null
            ;;
    esac

    return $?
}

checkNamingConvention(){
    local input="$1"
    local pattern="^[a-zA-Z0-9-]+$"

    if ! [[ "$input" =~ $pattern ]]; then
        error "Invalid Name $input. Please use only alphanumeric characters and hyphens."
        return 1
    fi
    return 0
}

usage() {
    echo "Usage: $0 [OPTIONS]"
    echo
    echo "Options:"
    echo "  -h, --help                  Display this help message and exit."
    echo "  --project <project_name>    Specify the project name."
    echo "  --ail-name <container_name> Specify the AIL container name."
    echo "  --no-lacus                  Do not create Lacus container."
    echo "  --lacus-name <container_name> Specify the Lacus container name."
    echo "  -i, --interactive           Run the script in interactive mode."
    echo
    echo "This script sets up LXD containers for AIL and optionally Lacus."
    echo "It creates a new LXD project, and configures the network and storage."
    echo "Then it launches and configures the specified containers."
    echo
    echo "Examples:"
    echo "  $0 --project myProject --ail-name ailContainer"
    echo "  $0 --interactive"
}

# ------------------ MAIN ------------------

setDefaults

# Check if interactive mode
INTERACTIVE=false
for arg in "$@"; do
    if [[ $arg == "-i" ]] || [[ $arg == "--interactive" ]]; then
        INTERACTIVE=true
        break
    fi
done

if [ "$INTERACTIVE" = true ]; then
    interactiveConfig
else
    nonInteractiveConfig "$@"
fi

validateArgs
setVars

trap 'interrupt' INT
trap 'err ${LINENO}' ERR

info "Setup LXD Project"
setupLXD

info "Create AIL Container"
createAILContainer

if $LACUS; then
    info "Create Lacus Container"
    createLacusContainer
fi

# Print info
ail_ip=$(lxc list "$AIL_CONTAINER" --format=json | jq -r '.[0].state.network.eth0.addresses[] | select(.family=="inet").address')
ail_email=$(lxc exec "$AIL_CONTAINER" -- bash -c "grep '^email=' /home/ail/ail-framework/DEFAULT_PASSWORD | cut -d'=' -f2")
ail_password=$(lxc exec "$AIL_CONTAINER" -- bash -c "grep '^password=' /home/ail/ail-framework/DEFAULT_PASSWORD | cut -d'=' -f2")
ail_API_Key=$(lxc exec "$AIL_CONTAINER" -- bash -c "grep '^API_Key=' /home/ail/ail-framework/DEFAULT_PASSWORD | cut -d'=' -f2")
if $LACUS; then
    lacus_ip=$(lxc list "$LACUS_CONTAINER" --format=json | jq -r '.[0].state.network.eth0.addresses[] | select(.family=="inet").address')
fi
echo "--------------------------------------------------------------------------------------------"
echo -e "${BLUE}AIL ${NC}is up and running on $ail_ip."
echo "You can access the web interface using https://$ail_ip:7000"
echo "--------------------------------------------------------------------------------------------"
echo -e "${BLUE}AIL ${NC}credentials:"
echo -e "Email: ${GREEN}$ail_email${NC}"
echo -e "Password: ${GREEN}$ail_password${NC}"
echo -e "API Key: ${GREEN}$ail_API_Key${NC}"
echo "--------------------------------------------------------------------------------------------"
if $LACUS; then
    echo -e "${BLUE}Lacus ${NC}is up and running on $lacus_ip"
    echo "You can add your Lacus instance to AIL in the settings by editing the Lacus URL:"
    echo "http://$lacus_ip:7100"
fi
echo "--------------------------------------------------------------------------------------------"
