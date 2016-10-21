'''
cleanup_bug_report.py

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

import re

import core.data.kb.config as cf


def cleanup_bug_report( input ):
    '''
    @return: A string that contains a "clean" bug report. The function will remove
             all references to the target site, operating system user name, etc.
    
    >>> cleanup_bug_report( 'foo' )
    'foo'
    
    >>> cleanup_bug_report( 'start /home/nsa/w3af/ end' )
    'start /home/user/w3af/ end'
    
    >>> cleanup_bug_report( 'start C:\\Documents and Settings\\CIA\\ end' )
    'start C:/user/ end'

    >>> from core.data.parsers.urlParser import url_object
    >>> target_url = url_object('http://www.target.com/')
    >>> cf.cf.save('targets', [target_url,] )
    >>> cleanup_bug_report( 'start http://www.target.com/ end' )
    'start http://domain/ end'
    
    '''
    user_re = '/home/(.*?)/'
    user_re_win= 'C:\\\\Documents and Settings\\\\(.*?)\\\\'
    
    input = re.sub(user_re, '/home/user/', input)
    input = re.sub(user_re_win, 'C:/user/', input)
    
    targets = cf.cf.getData('targets')
    if targets is not None:
        domains = [url.getDomain() for url in targets]
        paths = [url.getPath() for url in targets if url.getPath() != '/']
    
        for domain in domains:
            input = input.replace(domain, 'domain')
    
        for path in paths:
            input = input.replace(path, '/path/foo/')
        
    return input
    