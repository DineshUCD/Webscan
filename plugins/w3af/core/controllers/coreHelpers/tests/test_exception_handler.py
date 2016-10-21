# -*- coding: UTF-8 -*-
'''
test_exception_handler.py

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

import unittest
import sys

from core.controllers.coreHelpers.exception_handler import exception_handler
from core.controllers.coreHelpers.status import w3af_core_status


class TestExceptionHandler(unittest.TestCase):

    def setUp(self):
        exception_handler.clear()
        
        self.status = fake_status()
        self.status.set_running_plugin( 'plugin' )
        self.status.set_phase( 'phase' )
        self.status.set_current_fuzzable_request( 'http://www.w3af.org/' )        
    
    def test_handle_one(self):
        
        try:
            raise Exception('unittest')
        except Exception, e:
            exec_info = sys.exc_info()
            enabled_plugins = ''
            exception_handler.handle( self.status, e , exec_info, enabled_plugins )
        
        scan_id = exception_handler.get_scan_id()
        self.assertTrue( scan_id )
        
        all_edata = exception_handler.get_all_exceptions()
        
        self.assertEqual(1, len(all_edata))
        
        edata = all_edata[0]
        
        self.assertTrue( edata.get_summary().startswith('An exception was found') )
        self.assertTrue( 'traceback' in edata.get_details() )
        self.assertEquals( edata.plugin, 'plugin' )
        self.assertEquals( edata.phase, 'phase' )
        self.assertEquals( edata.fuzzable_request, 'http://www.w3af.org/' )
        self.assertEquals( edata.filename, 'test_exception_handler.py' )
        self.assertEquals( edata.exception, e )
    
    def test_handle_multiple(self):
        
        for i in xrange(10):
            try:
                raise Exception('unittest')
            except Exception, e:
                exec_info = sys.exc_info()
                enabled_plugins = ''
                exception_handler.handle( self.status, e , exec_info, enabled_plugins )
        
        exception_handler.get_scan_id()
        all_edata = exception_handler.get_all_exceptions()
        
        self.assertEqual(exception_handler.MAX_EXCEPTIONS_PER_PLUGIN, len(all_edata))
        
        edata = all_edata[0]
        
        self.assertTrue( edata.get_summary().startswith('An exception was found') )
        self.assertTrue( 'traceback' in edata.get_details() )
        self.assertEquals( edata.plugin, 'plugin' )
        self.assertEquals( edata.phase, 'phase' )
        self.assertEquals( edata.fuzzable_request, 'http://www.w3af.org/' )
        self.assertEquals( edata.filename, 'test_exception_handler.py' )
    
           
class fake_status(w3af_core_status):
    pass

