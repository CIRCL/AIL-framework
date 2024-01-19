#!/bin/bash

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

setVars() {
    DEPEDENCIES=("lxc" "jq")
    PATH_TO_BUILD="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

    PROJECT_NAME=$(generateName "AIL")
    STORAGE_POOL_NAME=$(generateName "AIL")
    NETWORK_NAME=$(generateName "AIL")
    NETWORK_NAME=${NETWORK_NAME:0:14}

    UBUNTU="ubuntu:22.04"

    AIL_CONTAINER=$(generateName "AIL")
    LACUS_CONTAINER=$(generateName "LACUS")
    LACUS_SERVICE_FILE="$PATH_TO_BUILD/conf/lacus.service"
}

setDefaults(){
    default_ail=false
    default_ail_image="AIL"
    default_lacus=false
    default_lacus_image="Lacus"
    default_outputdir=""
    default_sign=false
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

cleanupProject(){
    local project="$1"

    info "Starting cleanup ..."
    echo "Deleting container in project"
    for container in $(lxc query "/1.0/containers?recursion=1&project=${project}" | jq .[].name -r); do
        lxc delete --project "${project}" -f "${container}"
    done

    echo "Deleting images in project"
    for image in $(lxc query "/1.0/images?recursion=1&project=${project}" | jq .[].fingerprint -r); do
        lxc image delete --project "${project}" "${image}"
    done

    echo "Deleting project"
    lxc project delete "${project}"
}

cleanup(){
    cleanupProject "$PROJECT_NAME"
    lxc storage delete "$STORAGE_POOL_NAME"
    lxc network delete "$NETWORK_NAME"
}

createAILContainer(){
    lxc launch $UBUNTU "$AIL_CONTAINER" -p default --storage "$STORAGE_POOL_NAME" --network "$NETWORK_NAME"
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
    lxc launch $UBUNTU "$LACUS_CONTAINER" -p default --storage "$STORAGE_POOL_NAME" --network "$NETWORK_NAME"
    waitForContainer "$LACUS_CONTAINER"
    lxc exec "$LACUS_CONTAINER" -- sed -i "/#\$nrconf{restart} = 'i';/s/.*/\$nrconf{restart} = 'a';/" /etc/needrestart/needrestart.conf
    lxc exec "$LACUS_CONTAINER" -- apt update
    lxc exec "$LACUS_CONTAINER" -- apt upgrade -y
    lxc exec "$LACUS_CONTAINER" -- apt install pipx -y
    lxc exec "$LACUS_CONTAINER" -- pipx install poetry 
    lxc exec "$LACUS_CONTAINER" -- pipx ensurepath
    lxc exec "$LACUS_CONTAINER" -- apt install build-essential tcl -y
    lxc exec "$LACUS_CONTAINER" -- git clone https://github.com/redis/redis.git
    lxc exec "$LACUS_CONTAINER" --cwd=/root/redis -- git checkout 7.2
    lxc exec "$LACUS_CONTAINER" --cwd=/root/redis -- make
    lxc exec "$LACUS_CONTAINER" --cwd=/root/redis -- make test
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
    lxc file push "$LACUS_SERVICE_FILE" "$LACUS_CONTAINER"/etc/systemd/system/lacus.service
    lxc exec "$LACUS_CONTAINER" -- systemctl daemon-reload
    lxc exec "$LACUS_CONTAINER" -- systemctl enable lacus.service
    lxc exec "$LACUS_CONTAINER" -- systemctl start lacus.service
}

createLXDImage() {
    local container="$1"
    local image_name="$2"
    local path_to_repo="$3"
    local user="$4"

    local commit_id
    local version
    commit_id=$(getCommitID "$container" "$path_to_repo")
    version=$(getVersion "$container" "$path_to_repo" "$user")

    lxc stop "$container"
    lxc publish "$container" --alias "$image_name"
    lxc image export "$image_name" "$OUTPUTDIR"
    local file_name
    file_name="${image_name}_${version}_${commit_id}.tar.gz"
    pushd "$OUTPUTDIR" && mv -i "$(ls -t | head -n1)" "$file_name" 
    popd || { error "Failed to rename image file"; exit 1; }
    sleep 2
    if $SIGN; then
        sign "$file_name"
    fi
}

getCommitID() {
    local container="$1"
    local path_to_repo="$2"
    local current_branch
    current_branch=$(lxc exec "$container" -- cat "$path_to_repo"/.git/HEAD | awk '{print $2}')
    local commit_id
    commit_id=$(lxc exec "$container" -- cat "$path_to_repo"/.git/"$current_branch")
    echo "$commit_id"
}

getVersion() {
    local container="$1"
    local path_to_repo="$2"
    local user="$3"
    local version
    version=$(lxc exec "$container" --cwd="$path_to_repo" -- sudo -u "$user" bash -c "git tag | sort -V | tail -n 1")
    echo "$version"
}

sign() {
    if ! command -v gpg &> /dev/null; then
        error "GPG is not installed. Please install it before running this script with signing."
        exit 1
    fi
    local file=$1
    SIGN_CONFIG_FILE="$PATH_TO_BUILD/conf/sign.json"

    if [[ ! -f "$SIGN_CONFIG_FILE" ]]; then
        error "Config file not found: $SIGN_CONFIG_FILE"
        exit 1
    fi

    GPG_KEY_ID=$(jq -r '.EMAIL' "$SIGN_CONFIG_FILE")
    GPG_KEY_PASSPHRASE=$(jq -r '.PASSPHRASE' "$SIGN_CONFIG_FILE")

    # Check if the GPG key is available
    if ! gpg --list-keys | grep -q "$GPG_KEY_ID"; then
        warn "GPG key not found: $GPG_KEY_ID. Create new key."
        # Setup GPG key
        KEY_NAME=$(jq -r '.NAME' "$SIGN_CONFIG_FILE")
        KEY_EMAIL=$(jq -r '.EMAIL' "$SIGN_CONFIG_FILE")
        KEY_COMMENT=$(jq -r '.COMMENT' "$SIGN_CONFIG_FILE")
        KEY_EXPIRE=$(jq -r '.EXPIRE_DATE' "$SIGN_CONFIG_FILE")
        KEY_PASSPHRASE=$(jq -r '.PASSPHRASE' "$SIGN_CONFIG_FILE")
        BATCH_FILE=$(mktemp -d)/batch

        cat > "$BATCH_FILE" <<EOF
%echo Generating a basic OpenPGP key
Key-Type: default
Subkey-Type: default
Name-Real: ${KEY_NAME}
Name-Comment: ${KEY_COMMENT}
Name-Email: ${KEY_EMAIL}
Expire-Date: ${KEY_EXPIRE}
Passphrase: ${KEY_PASSPHRASE}
%commit
%echo done
EOF

        gpg --batch --generate-key "$BATCH_FILE" || { log "Failed to generate GPG key"; exit 1; }
        rm -r "$BATCH_FILE" || { log "Failed to remove batch file"; exit 1; }
    fi

    SIGN_DIR="${OUTPUTDIR}/${file/.tar.gz/}"
    mkdir -p "$SIGN_DIR"

    # Move the file to the new directory
    mv "${OUTPUTDIR}/${file}" "$SIGN_DIR"

    # Change to the directory
    pushd "$SIGN_DIR" || exit

    # Signing the file
    info "Signing file: $file in directory: $SIGN_DIR with key: $GPG_KEY_ID"
    gpg --default-key "$GPG_KEY_ID" --pinentry-mode loopback --passphrase "$GPG_KEY_PASSPHRASE" --detach-sign "${file}"

    # Check if the signing was successful
    if [ $? -eq 0 ]; then
        info "Successfully signed: $file"
    else
        error "Failed to sign: $file"
        exit 1
    fi
    popd || exit
}

checkSoftwareDependencies(){

    for dep in "$@"; do
        if ! command -v "$dep" &> /dev/null; then
            echo -e "${RED}Error: $dep is not installed.${NC}"
            exit 1
        fi
    done
}

usage() {
    echo "Usage: $0 [OPTIONS]"
}

# ------------------ MAIN ------------------
checkSoftwareDependencies "${DEPEDENCIES[@]}"
setVars
setDefaults

VALID_ARGS=$(getopt -o ho:s --long help,outputdir:,sign,ail,lacus,ail-name:,lacus-name:  -- "$@")
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
        --ail)
            ail=true
            shift 
            ;;
        --lacus)
            lacus=true
            shift 
            ;;
        --ail-name)
            ail_image=$2
            shift 2
            ;;
        --lacus-name)
            lacus_image=$2
            shift 2
            ;;
        -o | --outputdir)
            outputdir=$2
            shift 2
            ;;
        -s | --sign)
            sign=true
            shift 
            ;;
        *)  
            break 
            ;;
    esac
done

AIL=${ail:-$default_ail}
LACUS=${lacus:-$default_lacus}
AIL_IMAGE=${ail_image:-$default_ail_image}
LACUS_IMAGE=${lacus_image:-$default_lacus_image}
OUTPUTDIR=${outputdir:-$default_outputdir}
SIGN=${sign:-$default_sign}

if [ ! -e "$OUTPUTDIR" ]; then
    error "The specified directory does not exist."
    exit 1
fi

if ! $AIL && ! $LACUS; then
    error "No image specified!"
    exit 1
fi

echo "----------------------------------------"
echo "Startting creating LXD images ..."
echo "----------------------------------------"

trap cleanup EXIT

lxc project create "$PROJECT_NAME"
lxc project switch "$PROJECT_NAME"
lxc storage create "$STORAGE_POOL_NAME" "dir" 
lxc network create "$NETWORK_NAME"

if $AIL; then
    createAILContainer
    createLXDImage "$AIL_CONTAINER" "$AIL_IMAGE" "/home/ail/ail-framework" "ail"
fi

if $LACUS; then
    createLacusContainer
    createLXDImage "$LACUS_CONTAINER" "$LACUS_IMAGE" "/root/lacus" "root"
fi

echo "----------------------------------------"
echo "Build script finished."
echo "----------------------------------------"