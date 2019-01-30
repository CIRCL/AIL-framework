#!/bin/bash

usage() { echo "Usage: sudo $0 [-f <config_absolute_path>] [-p <port_start>] [-n <number_of_splash_servers>]" 1>&2;
          echo "          -f: absolute path to splash docker proxy-profiles directory (used for proxy configuration)";
          echo "          -p: number of the first splash server port number. This number is incremented for the others splash server";
          echo "          -n: number of splash servers to start";
          echo "";
          echo "          -options:";
          echo "          -u: max unbound in-memory cache (Mb, Restart Splash when full, default=3000 Mb)";
          echo "";
          echo "example:";
          echo "sudo ./launch_splash_crawler.sh -f /home/my_user/AIL-framework/configs/docker/splash_onion/etc/splash/proxy-profiles/ -p 8050 -n 3";
          exit 1;
        }

while getopts ":p:f:n:u:" o; do
    case "${o}" in
        p)
            p=${OPTARG}
            ;;
        f)
            f=${OPTARG}
            ;;
        n)
            n=${OPTARG}
            ;;
        u)
            u=${OPTARG}
            ;;
        *)
            usage
            ;;
    esac
done
shift $((OPTIND-1))

if [ -z "${u}" ]; then
    u=3000;
fi

if [ -z "${p}" ] || [ -z "${f}" ] || [ -z "${n}" ]; then
    usage;
fi

RED="\\033[1;31m"
DEFAULT="\\033[0;39m"
GREEN="\\033[1;32m"
WHITE="\\033[0;02m"

if [ ! -d "${f}" ]; then
    printf "$RED\n Error -f, proxy-profiles directory: $WHITE${f}$RED not found\n$DEFAULT Please check if you enter the correct path\n"
    exit 1
fi

if [ ! -f "${f}default.ini" ]; then
    printf "$RED\n Error -f, proxy configuration file:$WHITE default.ini$RED not found\n$DEFAULT Please check if you enter the correct path\n"
    exit 1
fi

screen -dmS "Docker_Splash"
sleep 0.1

for ((i=0;i<=$((${n} - 1));i++)); do
    port_number=$((${p} + $i))
    screen -S "Docker_Splash" -X screen -t "docker_splash:$port_number" bash -c 'sudo docker run -d -p '$port_number':8050 --restart=always --cpus=1 --memory=4.5G -v '$f':/etc/splash/proxy-profiles/ --net="bridge" scrapinghub/splash --maxrss '$u'; read x'
    sleep 0.1
    printf "$GREEN    Splash server launched on port $port_number$DEFAULT\n"
done
