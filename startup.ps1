$folder = pwd
pipenv install

$cmds = @"
cd "$folder\NotesImport"
python .\gui.py
"@

$cmds|pipenv shell
