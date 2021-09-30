# Notes Import for QNAP Notes Station Notes into Joplin
## This Python app provides the following:
 1. A GUI to configure the import process
 1. Configure the path of the Joplin app
 1. Configure the Joplin token for data api access
 1. Configure the insertion point in Joplin where to import the QNAP contents
 1. Configure the path of the exported QNAP notes database
 1. A class with basically an *import_it* method which does the real work
 1. With the press of a button one initiates the import action
 
 To invoke the GUI, invoke the *gui.py* module to launch the dialog.
## Features of QNAP Notes Station which will be transformed
 1. Headings
 1. Paragraphs
 1. Tables
 1. Code sections
 1. Citations
 1. Attachments
 1. Images
 1. Ordered lists
 1. Bullet lists
 1. Task lists
 1. Nested lists
 1. (External) Links
 1. Horizontal rulers
 1. Subscripts
 1. Superscripts
 1. Tags assigned to notes
  
## How to install and invoke the GUI
This will install the distribution in a virtual environment and invoke the GUI
 1. Copy the whole content of the project folder into a chosen local folder
 1. Open a terminal window inside the local folder
 1. `>`pipenv install
 1. `>`pipenv shell
 1. `>`cd NotesImport
 1. `>`python
 1. `>>>`from gui import Gui
 1. `>>>`Gui.main()

### Simplified Method
Simply invoke the startup script (Linux or Windows Powershell) from inside the installation folder.

The GUI is more or less self-explanatory and shows tool tips on the controls.
 
There is ongoing work to simplify the usage of the code.
 