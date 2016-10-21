'''
exception_handler.py

Copyright 2012 Andres Riancho

This file is part of w3af, w3af.sourceforge.net .

w3af is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation version 2 of the License.

w3af is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with w3af; if not, write to the Free Software
Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

'''
import md5
import random
import threading
import traceback

import core.data.kb.config as cf
import core.controllers.outputManager as om

from os.path import basename

from core.controllers.exception_handling.cleanup_bug_report import cleanup_bug_report
from core.controllers.w3afException import (w3afMustStopException,
                                            w3afMustStopByUnknownReasonExc)

        
class ExceptionHandler(object):
    '''
    This class handles exceptions generated while running plugins, usually
    the handling is just to store the traceback for later processing.
    
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''
    
    MAX_EXCEPTIONS_PER_PLUGIN = 3
    NO_HANDLING = (MemoryError, w3afMustStopByUnknownReasonExc, w3afMustStopException)
    
    def __init__(self):
        # TODO: Maybe this should be a disk_list just to make sure we don't
        # fill the memory with exceptions?
        self._exception_data = []
        self._lock = threading.RLock()
        
        self._scan_id = None

    def handle( self, current_status, exception, exec_info, enabled_plugins ):
        '''
        This method stores the current status and the exception for later
        processing. If there are already too many stored exceptions for this
        plugin then no action is taken.
        
        @param current_status: Pointer to the coreHelpers.status module
        @param exception: The exception that was raised
        @param exec_info: The exec info as returned by sys module
        @param enabled_plugins: A string as returned by helpers.pprint_plugins.
                                First I thought about getting the enabled_plugins
                                after the scan finished, but that proved to be an
                                incorrect approach since the UI and/or strategy
                                could simply remove that information as soon as the
                                scan finished.
        
        @return: None
        '''
        #
        # There are some exceptions, that because of their nature I don't want
        # to handle. So what I do is to raise them in order for them to get to
        # w3afCore.py , most likely to the except lines around self.strategy.start()
        #
        if isinstance(exception, self.NO_HANDLING):
            raise
            
        stop_on_first_exception = cf.cf.getData( 'stop_on_first_exception' )
        if stop_on_first_exception:
            # TODO: Not sure if this is 100% secure code, but it should work
            # in most cases, and in the worse scenario it is just a developer
            # getting hit ;)
            #
            # The risk is that the exception being raise is NOT the same exception
            # that was caught before calling this handle method. This might happen
            # (not sure actually) in places where lots of exceptions are raised
            # in a threaded environment
            raise
        
        #
        # Now we really handle the exception that was produced by the plugin in
        # the way we want to.
        #
        except_type, except_class, tb = exec_info
        
        with self._lock:
            edata = ExceptionData(current_status, exception, tb, enabled_plugins)
            
            count = 0
            for stored_edata in self._exception_data:
                if edata.plugin == stored_edata.plugin and\
                edata.phase == stored_edata.phase:
                    count += 1
            
            if count < self.MAX_EXCEPTIONS_PER_PLUGIN:
                self._exception_data.append(edata)

                msg = edata.get_summary()
                msg += ' The scan will continue but some vulnerabilities might not'
                msg += ' be identified.'
                om.out.error( msg )

    def clear(self):
        self._exception_data = []
                
    def get_all_exceptions(self):
        return self._exception_data
    
    def generate_summary_str(self):
        '''
        @return: A string with a summary of the exceptions found during the
                 current scan. This is mostly used for printing in the console
                 but can be used anywhere.
        
        @see: generate_summary method for a way of getting a summary in a
              different format.
        '''
        fmt_with_exceptions = 'During the current scan (with id: %s) w3af caught'
        fmt_with_exceptions += ' %s exceptions in it\'s plugins. The scan was able'
        fmt_with_exceptions += ' to continue by ignoring those failures but the'
        fmt_with_exceptions += ' scan result is most likely incomplete.\n\n'
        fmt_with_exceptions += 'These are the phases and plugins that raised'
        fmt_with_exceptions += ' exceptions:\n'
        fmt_with_exceptions += '%s\n'
        fmt_with_exceptions += 'We recommend you report these vulnerabilities'
        fmt_with_exceptions += ' to the developers in order to help increase the'
        fmt_with_exceptions += ' project\'s stability.'
        
        fmt_without_exceptions = 'No exceptions were raised during scan with id: %s.'
        
        summary = self.generate_summary()
        
        if summary['total_exceptions']:
            phase_plugin_str = ''
            for phase in summary['exceptions']:
                for plugin, fr, exception, traceback in summary['exceptions'][phase]:
                    phase_plugin_str += '- %s.%s\n' % (phase, plugin)
            
            with_exceptions = fmt_with_exceptions % ( self.get_scan_id() ,
                                                      summary['total_exceptions'],
                                                      phase_plugin_str)
            return with_exceptions
        else:
            without_exceptions = fmt_without_exceptions % self.get_scan_id()
            return without_exceptions
    
    def generate_summary(self):
        '''
        @return: A dict with information about exceptions.
        '''
        res = {}
        res['total_exceptions'] = len(self._exception_data)
        res['exceptions'] = {}
        exception_dict = res['exceptions']
        
        for exception in self._exception_data:
            phase = exception.phase
            
            data = (exception.plugin,
                    exception.fuzzable_request,
                    exception.exception,
                    exception.traceback)            
            
            if phase not in exception_dict:
                exception_dict[phase] = [ data, ]
            else:
                exception_dict[phase].append( data )
        
        return res
    
    def get_scan_id(self):
        '''
        @return: A scan identifier to bind all bug reports together so that we
                 can understand them much better when looking at the individual
                 Trac bug reports.
                 
                 Note that this will NOT leak any personal information to our
                 systems.
        '''
        if not self._scan_id:
            hash_data = ''
            hash_data += str(random.randint(1,50000000) * random.randint(1,50000000)) 
            
            m = md5.new(hash_data)
            self._scan_id = m.hexdigest()[:10]
        
        return self._scan_id

        
class ExceptionData(object):
    def __init__(self, current_status, e, tb, enabled_plugins):
        self.exception = e
        self.traceback = tb
       
        # Extract the filename and line number where the exception was raised
        filepath = traceback.extract_tb(tb)[-1][0]
        self.filename = basename(filepath)
        self.lineno = tb.tb_lineno
                
        self.traceback_str = ''.join(traceback.format_tb(tb))
        self.traceback_str = cleanup_bug_report(self.traceback_str)
        
        self.plugin = current_status.get_running_plugin()
        self.phase = current_status.get_phase()
        self.enabled_plugins = enabled_plugins
        
        self.fuzzable_request = current_status.get_current_fuzzable_request()
        self.fuzzable_request = cleanup_bug_report( str(self.fuzzable_request) )

    def get_summary(self):
        res = 'An exception was found while running %s.%s on "%s". The exception'
        res += ' was: "%s" at %s:%s.'
        res = res % (self.phase, self.plugin, self.fuzzable_request, self.exception,
                     self.filename, self.lineno)
        return res
        
    def get_details(self):
        res = self.get_summary()
        res += 'The full traceback is:\n%s' % self.traceback_str
        return res
    
    def get_where(self):
        return '%s.%s:%s' % (self.phase, self.plugin, self.lineno)

    def __str__(self):
        return self.get_details()
    
exception_handler = ExceptionHandler()
