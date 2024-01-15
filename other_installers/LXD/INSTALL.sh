#!/bin/bash

setVars() {
    GREEN='\033[0;32m'
    YELLOW='\033[1;33m'
    BLUE='\033[0;34m'
    RED='\033[0;31m'
    NC='\033[0m' # No Color

    PROJECT_NAME=$(generateName "AIL")
    STORAGE_POOL_NAME=$(generateName "AIL")
    NETWORK_NAME=$(generateName "AIL")
    NETWORK_NAME=${NETWORK_NAME:0:14}

    UBUNTU="ubuntu:22.04"

    AIL_CONTAINER=$(generateName "AIL")
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
    lxc storage create "$STORAGE_POOL_NAME" "dir" 
    lxc network create "$NETWORK_NAME"
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
    lxc storage delete "$APP_STORAGE"
    lxc storage delete "$DB_STORAGE"
    lxc network delete "$NETWORK_NAME"
    exit 130
}

