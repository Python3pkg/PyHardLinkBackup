#!/usr/bin/env bash

ENV_PATH=~/PyHardLinkBackup
CURRENT_DIR=$(pwd)

set -e

ACTIVATE_SCRIPT=${ENV_PATH}/bin/activate
echo "Activate venv with: ${ACTIVATE_SCRIPT}"
source ${ACTIVATE_SCRIPT}

set -x

pip install --upgrade pip
pip install --upgrade PyHardLinkBackup

manage migrate
phlb helper ${ENV_PATH}
