#!/bin/bash

#usage() { echo "Usage: sudo $0 [-f <config absolute_path>] [-p <port_start>] [-n <number_of_splash>]" 1>&2; exit 1; }

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
    #usage
    echo "usage"
fi

first_port=$p
echo "usage0"
screen -dmS "Docker_Splash"
echo "usage1"
sleep 0.1

for ((i=0;i<=$((${n} - 1));i++)); do
    port_number=$((${p} + $i))
    screen -S "Docker_Splash" -X screen -t "docker_splash:$i" bash -c 'sudo docker run -p '$port_number':8050 --cpus=1 -v '$f':/etc/splash/proxy-profiles/ --net="bridge" scrapinghub/splash; read x'
    sleep 0.1
done
