#!/bin/bash
cd /home/praddy/src/randomize
mkdir temp
export PYTHONPATH=./temp
python setup.py build develop --install-dir ./temp
cp ./temp/Randomize.egg-link /home/praddy/.config/deluge/plugins
rm -fr ./temp
