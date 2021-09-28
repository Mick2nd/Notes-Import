#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, print_function, unicode_literals

'''
Created on 02.07.2018

@author: Jürgen Habelt
'''

from os.path import join
import logging.config
import json, re


class LoggingInstance(object):
    '''
    Supports logging, maintains all logger instances
    '''
    
    @classmethod
    def type(cls, obj):
        '''
        Returns the somehow modified class name of an object
        @param obj: the logging object instance
        @return: the class name to be used as logger name
        '''
        tp = str(type(obj))
        dottedName = re.match(r".*?'(.*?)'>", tp).group(1) 
        return dottedName.split('.')[-1]


    def __init__(self, project_path = '.'):
        '''
        Constructor
        '''
        if 'loggers' in self.__dict__:
            return
        
        self.loggers = {}
        json_location = join(project_path, 'ConfigFiles', 'Logging.json')
        
        with open(json_location, 'r') as f:
            dic = json.load(f)
            logging.config.dictConfig(dic)


    def getLogger(self, name = 'raw'):
        '''
        Instantiates a logger with given name and additional console handler
        @param name: Can be name (string) or object
        '''
        if len(self.loggers) == 0:                                                  # at the begin of each session do a roll-over
            logger = logging.getLogger('raw')
            for handler in logger.handlers:
                if isinstance(handler, logging.handlers.TimedRotatingFileHandler):
                    pass
                    #handler.doRollover()
        
        if not isinstance(name, str):
            name = LoggingInstance.type(name)
        
        if name not in self.loggers:
            logger = logging.getLogger(name)
            self.loggers[name] = logger
        
        return self.loggers[name]

    
    def shutdown(self):
        '''
        Shutdown the logging system
        '''
        logging.shutdown()
        
