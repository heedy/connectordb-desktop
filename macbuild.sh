#!/bin/sh

# ConnectorDB for Macs must be built on a mac, which is unfortunate. You will need to clone connectordb in parent directory,
# run make, and then return here to run this script.

# Clean working directory
git clean -d -f -x -q

mkdir ./release

VERSION=`../connectordb/bin/connectordb --semver`
NAME=connectordb_desktop_${VERSION}_darwin_amd64

echo -e "... connectordb_desktop_${VERSION}_darwin_amd64"
NEWDIR=./release/${NAME}/
mkdir $NEWDIR

# Copy the laptoplogger python files
cp -a ./src ${NEWDIR}src

# Copy the connectordb binaries
cp -a ../connectordb/bin ${NEWDIR}src/bin

# ...aaand copy the final stuff
cp README.md ${NEWDIR}
cp LICENSE ${NEWDIR}
cp connectordb-desktop ${NEWDIR}

cd release

echo "Running PyInstaller"
pyinstaller --windowed --icon=./src/resources/logo.ico -n "ConnectorDB Desktop" -y src/windowsapp.py
# echo .. ${NAME}.tar.gz
# tar -czf ${NAME}.tar.gz ${NAME}
cd ..
