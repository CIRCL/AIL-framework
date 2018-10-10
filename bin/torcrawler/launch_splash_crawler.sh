#!/bin/bash

usage() { echo "Usage: sudo $0 [-f <config_absolute_path>] [-p <port_start>] [-n <number_of_splash_servers>]" 1>&2;
          echo "          -f: absolute path to splash docker proxy-profiles directory (used for proxy configuration)";
          echo "          -p: number of the first splash server port number. This number is incremented for the others splash server";
          echo "          -n: number of splash servers to start";
          echo "";
          echo "example:";
          echo "sudo ./launch_splash_crawler.sh -f /home/my_user/AIL-framework/configs/docker/splash_onion/etc/splash/proxy-profiles/ -p 8050 -n 3";
          exit 1;
        }

while getopts ":p:f:n:" o; do
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
        *)
            usage
            ;;
    esac
done
shift $((OPTIND-1))

if [ -z "${p}" ] || [ -z "${f}" ] || [ -z "${n}" ]; then
    usage;
fi

screen -dmS "Docker_Splash"
sleep 0.1

for ((i=0;i<=$((${n} - 1));i++)); do
    port_number=$((${p} + $i))
    screen -S "Docker_Splash" -X screen -t "docker_splash:$port_number" bash -c 'sudo docker run -p '$port_number':8050 --cpus=1 --memory=4.5G -v '$f':/etc/splash/proxy-profiles/ --net="bridge" scrapinghub/splash; read x'
    sleep 0.1
    echo "    Splash server launched on port $port_number"
done
