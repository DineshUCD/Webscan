'''
failing_spider.py

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
from plugins.discovery.webSpider import webSpider


class failing_spider(webSpider):
    '''
    This is a test plugin that will raise exceptions.
    Only useful for testing, see test_discover_exception_handling.py
    
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''

    def __init__(self):
        webSpider.__init__(self)
        
        self.blacklist = ('2.html',)

    def discover(self, fuzzable_req):
        '''
        Raises an exception if the fuzzable_req ends with something in the blacklist.
        '''
        for ending in self.blacklist:
            if fuzzable_req.getURL().url_string.endswith(ending):
                raise Exception('Test')
        
        return super(failing_spider, self).discover(fuzzable_req)

