'''
Created on 22.09.2021

@author: juergen@habelt-jena.de

ASSUMPTION about the location of
- configuration files (logging, app configuration)
- logging files

It is relative to current working directory which is src
'''

import sys
from os.path import join
import json
from contextlib import contextmanager
from subprocess import call
from PyQt5.QtWidgets import QDialog, QApplication, QMessageBox, QFileDialog

from gui_ui import Ui_Dialog
from stdout_redirector import StdoutRedirector
from logging_factory import LoggingFactory
from importer import Importer


class Gui(QDialog, Ui_Dialog):
    '''
    A Gui to control import of Qnap Notes Station exports into Joplin
    '''

    def __init__(self, app, argv):
        '''
        Constructor
        '''
        QDialog.__init__(self, parent = None)
        self.setupUi(self)
        sys.stdout = StdoutRedirector(self.textEditOutput)
        
        self.app = app
        self.argv = argv
        
        self.path = '.'                                             # environ['PROJECT_LOC']
        self.logger = LoggingFactory(self.path).getLogger(self)
        self.logger.info('Initializing the dialog')

        self._wire_handlers()
        self._readConfig()


    def _wire_handlers(self):
        '''
        Wire event handlers
        '''
        self.pushButtonExe.clicked.connect(self._select_exe)
        self.pushButtonInvokeExe.clicked.connect(self._invoke_exe)
        self.pushButtonArchive.clicked.connect(self._select_archive)
        self.pushButtonGo.clicked.connect(self._import_archive)
    
    
    def _readConfig(self):
        '''
        Reads a config file in json format
        '''
        path = join(self.path, 'ConfigFiles', 'Config.json')
        with open(path, 'r') as f:
            self.config = json.load(f)
            
        self.config['test'] = 55                                        # test
        self.lineEditExe.setText(self.config.get('joplin', ''))
        self.lineEditToken.setText(self.config.get('token', ''))
        self.lineEditInsertion.setText(self.config.get('insertion-point', ''))
        self.lineEditArchive.setText(self.config.get('archive', ''))
    
    
    def _writeConfig(self):
        '''
        Writes a config file in json format
        '''
        self.config['joplin'] = self.lineEditExe.text()
        self.config['token'] = self.lineEditToken.text()
        self.config['insertion-point'] = self.lineEditInsertion.text()
        self.config['archive'] = self.lineEditArchive.text()
        
        path = join(self.path, 'ConfigFiles', 'Config.json')
        with open(path, 'w') as f:
            json.dump(self.config, f)


    @contextmanager
    def exception_mgr(self):
        '''
        Context manager for exceptions
        '''
        try:
            yield self
            
        except BaseException as _:
            self.logger.exception('Exception during command execution')


    def accept(self, *args, **kwargs):
        '''
        Override used to suppress closing dialog during Save operation
        '''
        return 


    def reject(self, *args, **kwargs):
        '''
        Override used to perform cleanup
        '''
        with self.exception_mgr():
            if QMessageBox.question(self, 'Close', 'Really Close Dialog?') != QMessageBox.Yes:
                return 
    
            self._writeConfig()
            sys.stdout = sys.__stdout__
            print('Exited')
            return super().reject(*args, **kwargs)


    def _select_exe(self):
        '''
        Selects the Joplin exe
        '''
        with self.exception_mgr():
            file_name = QFileDialog.getOpenFileName(
                self, 
                'Joplin Exe', 
                'C:\\Program Files', 
                'Executables (*.exe)')
            if file_name[0]:
                self.lineEditExe.setText(file_name[0])


    def _invoke_exe(self):
        '''
        Invokes the Joplin EXE
        '''
        with self.exception_mgr():
            exe = self.lineEditExe.text()
            if exe:
                call([exe])


    def _select_archive(self):
        '''
        Selects a Qnap Notes Station Archive
        '''
        with self.exception_mgr():
            file_name = QFileDialog.getOpenFileName(
                self, 
                'Qnap Notes Station Archive', 
                'D:\\users\\jsoft\\Downloads', 
                'Archives (*.ns3)')
            if file_name[0]:
                self.lineEditArchive.setText(file_name[0])
                
                
    def _import_archive(self):
        '''
        Imports the selected archive of QNAP notebooks
        '''
        with self.exception_mgr():
            archive = self.lineEditArchive.text()
            token = self.lineEditToken.text()
            insertion = self.lineEditInsertion.text()
            if archive and token:
                importer = Importer(self._refresh_gui, archive, token, insertion)
                importer.import_it()
    
    
    def _refresh_gui(self):
        '''
        Refreshs the Gui
        '''
        self.app.processEvents()

        
if __name__ == '__main__':
    
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    control = Gui(app, sys.argv)
    control.open()
    app.exec_()
