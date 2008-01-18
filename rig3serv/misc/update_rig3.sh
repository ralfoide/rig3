#!/bin/bash

cd my_site

mkdir -p rig3serv-temp-update
cd rig3serv-temp-update

if svn update --non-interactive && python src/test_rig3.py ; then
	cd ..
	echo
	echo "*** Updating"
	echo
	rsync -avP --delete-before rig3serv-temp-update/ rig3serv-trunk
	echo
	echo "*** Generating"
	echo
else
	cd ..
	echo
	echo "*** Update and Test failed"
	echo
fi
python ./rig3serv-trunk/src/rig3.py -c my_site.rc $@
echo Done

