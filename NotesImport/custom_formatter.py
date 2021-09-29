'''
Created on 28.09.2021

@author: juergen@habelt-jena.de
'''

import logging


class CustomFormatter(logging.Formatter):
    '''
    This Custom Formatter depends on the Logger name:
    The 'raw' Logger logs the message only
    All other Loggers log with the given format
    '''
    def __init__(self, *args, **kwargs):
        '''
        Initialization
        '''
        super(CustomFormatter, self).__init__(*args, **kwargs)
        
        self.raw_formatter = logging.Formatter('%(message)s')
        
    
    def format(self, record):
        '''
        Performs formatting depending on Logger name
        '''
        if record.name == 'raw':
            return self.raw_formatter.format(record)
        
        return super(CustomFormatter, self).format(record)
