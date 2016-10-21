'''
globalRedirect.py

Copyright 2006 Andres Riancho

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

import core.controllers.outputManager as om

# options
from core.data.options.option import option
from core.data.options.optionList import optionList

import core.data.kb.knowledgeBase as kb
import core.data.kb.vuln as vuln
import core.data.constants.severity as severity

import core.data.parsers.dpCache as dpCache
from core.data.fuzzer.fuzzer import createMutants
from core.controllers.w3afException import w3afException
from core.controllers.basePlugin.baseAuditPlugin import baseAuditPlugin

import re


class globalRedirect(baseAuditPlugin):
    '''
    Find scripts that redirect the browser to any site.
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''

    def __init__(self):
        baseAuditPlugin.__init__(self)
        
        # Internal variables
        self._test_site = 'http://www.w3af.org/'
        self._script_re = re.compile('< *?script.*?>(.*?)< *?/ *?script *?>', 
                                     re.IGNORECASE | re.DOTALL )
        self._meta_url_re = re.compile('.*?;URL=(.*)', re.IGNORECASE | re.DOTALL)

    def audit(self, freq ):
        '''
        Tests an URL for global redirect vulnerabilities.
        
        @param freq: A fuzzableRequest
        '''
        om.out.debug( 'globalRedirect plugin is testing: ' + freq.getURL() )
        
        mutants = createMutants( freq , [self._test_site, ] )
            
        for mutant in mutants:
            if self._has_no_bug(mutant):
                args = (mutant,)
                kwds = {'callback': self._analyze_result,
                        'follow_redir': False }
                self._run_async(meth=self._uri_opener.send_mutant, args=args,
                                                                    kwds=kwds)
        self._join()

    def _analyze_result( self, mutant, response ):
        '''
        Analyze results of the _send_mutant method.
        '''
        if self._find_redirect( response ):
            v = vuln.vuln( mutant )
            v.setPluginName(self.getName())
            v.setId( response.id )
            v.setName( 'Insecure redirection' )
            v.setSeverity(severity.MEDIUM)
            v.setDesc( 'Global redirect was found at: ' + mutant.foundAt() )
            kb.kb.append( self, 'globalRedirect', v )
    
    def end(self):
        '''
        This method is called when the plugin wont be used anymore.
        '''
        self._join()
        self.printUniq( kb.kb.getData( 'globalRedirect', 'globalRedirect' ), 'VAR' )
        
    def _find_redirect( self, response ):
        '''
        This method checks if the browser was redirected ( using a 302 code ) 
        or is being told to be redirected by javascript or <meta http-equiv="refresh"
        '''
        #
        #    Test for 302 header redirects
        #
        lheaders = response.getLowerCaseHeaders()
        for header_name in ('location', 'uri'):
            if header_name in lheaders and \
               lheaders[header_name].startswith( self._test_site ):
                # The script sent a 302, and w3af followed the redirection
                # so the URL is now the test site
                return True

        #
        # Test for meta redirects
        #
        try:
            dp = dpCache.dpc.getDocumentParserFor( response )
        except w3afException:
            # Failed to find a suitable parser for the document
            return False
        else:
            for redir in dp.getMetaRedir():
                match_url = self._meta_url_re.match(redir)
                if match_url:
                    url = match_url.group(1)
                    if url.startswith( self._test_site ):
                        return True

        #
        # Test for JavaScript redirects, these are some common redirects:
        #     location.href = '../htmljavascript.htm';
        #     window.location = "http://www.w3af.com/"
        #     window.location.href="http://www.w3af.com/";
        #     location.replace('http://www.w3af.com/');
        res = self._script_re.search( response.getBody() )
        if res:
            for script_code in res.groups():
                script_code = script_code.split('\n')
                code = []
                for i in script_code:
                    code.extend( i.split(';') )
                    
                for line in code:
                    if re.search( '(window\.location|location\.).*' + self._test_site, line ):
                        return True
        
        return False
        
    def getOptions( self ):
        '''
        @return: A list of option objects for this plugin.
        '''    
        ol = optionList()
        return ol

    def setOptions( self, OptionList ):
        '''
        This method sets all the options that are configured using the user interface 
        generated by the framework using the result of getOptions().
        
        @parameter OptionList: A dictionary with the options for the plugin.
        @return: No value is returned.
        ''' 
        pass
        
    def getPluginDeps( self ):
        '''
        @return: A list with the names of the plugins that should be run before the
        current one.
        '''
        return []
    
    def getLongDesc( self ):
        '''
        @return: A DETAILED description of the plugin functions and features.
        '''
        return '''
        This plugin finds global redirection vulnerabilities. This kind of bugs are used for
        phishing and other identity theft attacks. A common example of a global redirection
        would be a script that takes a "url" parameter and when requesting this page, a HTTP
        302 message with the location header to the value of the url parameter is sent in the
        response.
        
        Global redirection vulnerabilities can be found in javascript, META tags and 302 / 301 
        HTTP return codes.
        '''
