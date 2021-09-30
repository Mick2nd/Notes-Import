#!/bin/sh
folder=$(pwd)
echo "Installing Environment for Notes Import in $folder"
pipenv install
cmds1="cd $folder/NotesImport"
cmds2="python ./gui.py"
cmds="${cmds1};${cmds2}"
echo $cmds
pipenv shell $cmds
