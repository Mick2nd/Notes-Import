'''
Created on 22.09.2021

@author: juergen@habelt-jena.de
'''


class StdoutRedirector(object):
    '''
    Redirects console output to a given Editor widget
    Usage: 
    Activate:     sys.stdout = StdoutRedirector(widget)
    De-Activate:  sys.stdout = sys.__stdout__
    '''


    def __init__(self, text_edit):
        '''
        Constructor
        '''
        self.text_edit = text_edit
        

    def write(self, text):
        '''
        Mimics output to console replacement in form of a TextEdit widget
        '''
        self.text_edit.append(f'<span style="color:{self._get_color(text)};">{text[ : -1]}</span>')        
       
       
    def _get_color(self, text):
        '''
        Returns a color belonging to the type of message in text
        ''' 
        if text.startswith('WARNING'):
            return '#f5bf42'
        if text.startswith('ERROR'):
            return '#ff0000'
        
        return '#000000'