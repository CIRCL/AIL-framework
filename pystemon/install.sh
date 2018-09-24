git clone https://github.com/cvandeplas/pystemon.git /opt/pystemon

apt-get install -y python-pip python-requests python-yaml python-redis

pip install beautifulsoup4

BASEDIR=$(dirname "$0")
cp $BASEDIR/config.cfg /opt/AIL/bin/packages/
cp $BASEDIR/pystemon.yaml /opt/pystemon/
