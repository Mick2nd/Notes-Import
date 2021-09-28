#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, print_function, unicode_literals


__license__   = 'GPL v3'
__copyright__ = u'2019, Jürgen Habelt <juergen@habelt-jena.de>'
__docformat__ = 'restructuredtext en'


from logging_instance_json import LoggingInstance


class LoggingFactory(object):
    '''
    Supports logging, maintains all logger instances
    '''

    _singleton = None

    def __new__(cls, *args, **kwargs):
        '''
        Overrides the __new__ method. Every constructor call returns then the
        same instance.
        TODO: thello_worldif this works, when we derive different subclasses from it
        '''
        if not LoggingFactory._singleton:
            LoggingFactory._singleton = object.__new__(LoggingInstance)
            LoggingFactory._singleton.__init__(*args, **kwargs)
        
        return LoggingFactory._singleton
