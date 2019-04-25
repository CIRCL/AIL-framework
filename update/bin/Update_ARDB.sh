#!/bin/bash

echo "Killing all screens ..."
bash -c "bash ../../bin/LAUNCH.sh -k"
echo ""
echo "Updating ARDB ..."
pushd ../../
rm -r ardb
pushd ardb/
git clone https://github.com/yinqiwen/ardb.git
git checkout 0.10 || exit 1
make || exit 1
popd
popd
echo "ARDB Updated"
echo ""

exit 0
