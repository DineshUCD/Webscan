'''
directoryIndexing.py

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

from core.controllers.basePlugin.baseGrepPlugin import baseGrepPlugin

import core.data.kb.knowledgeBase as kb
import core.data.kb.vuln as vuln
import core.data.constants.severity as severity

from core.data.bloomfilter.bloomfilter import scalable_bloomfilter
from core.data.esmre.multi_in import multi_in

import re


class directoryIndexing(baseGrepPlugin):
    '''
    Grep every response for directory indexing problems.
      
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''
    
    DIR_INDEXING = (
        "<title>Index of /", 
        '<a href="?C=N;O=D">Name</a>',
        '<A HREF="?M=A">Last modified</A>', 
        "Last modified</a>",
        "Parent Directory</a>",
        "Directory Listing for",
        "<TITLE>Folder Listing.",
        '<table summary="Directory Listing" ',
        "- Browsing directory ",
        # IIS 6.0 and 7.0
        '">[To Parent Directory]</a><br><br>', 
        # IIS 5.0
        '<A HREF=".*?">.*?</A><br></pre><hr></body></html>'
    )
    _multi_in = multi_in( DIR_INDEXING )    
    
    def __init__(self):
        baseGrepPlugin.__init__(self)
        
        self._already_visited = scalable_bloomfilter()
        
    def grep(self, request, response):
        '''
        Plugin entry point, search for directory indexing.
        @parameter request: The HTTP request object.
        @parameter response: The HTTP response object
        @return: None
        '''
        if response.getURL().getDomainPath() in self._already_visited:
            # Already worked for this URL, no reason to work twice
            return
        
        else:
            # Save it,
            self._already_visited.add( response.getURL().getDomainPath() )
            
            # Work,
            if response.is_text_or_html():
                html_string = response.getBody()
                for dir_indexing_match in self._multi_in.query( html_string ):
                    v = vuln.vuln()
                    v.setPluginName(self.getName())
                    v.setURL( response.getURL() )
                    msg = 'The URL: "' + response.getURL() + '" has a directory '
                    msg += 'indexing vulnerability.'
                    v.setDesc( msg )
                    v.setId( response.id )
                    v.setSeverity(severity.LOW)
                    path = response.getURL().getPath()
                    v.setName( 'Directory indexing - ' + path )
                    kb.kb.append( self , 'directory' , v )
                    break
    
    def setOptions( self, OptionList ):
        pass
    
    def getOptions( self ):
        '''
        @return: A list of option objects for this plugin.
        '''    
        ol = optionList()
        return ol
        
    def end(self):
        '''
        This method is called when the plugin wont be used anymore.
        '''
        self.printUniq( kb.kb.getData( 'directoryIndexing', 'directory' ), 'URL' )
            
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
        This plugin greps every response directory indexing problems.
        '''
