'''
osCommanding.py

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
from __future__ import with_statement

import core.controllers.outputManager as om

# options
from core.data.options.option import option
from core.data.options.optionList import optionList

from core.controllers.basePlugin.baseAuditPlugin import baseAuditPlugin
from core.controllers.delay_detection.exact_delay import exact_delay
from core.controllers.delay_detection.delay import delay
from core.data.fuzzer.fuzzer import createMutants
from core.data.esmre.multi_in import multi_in

# kb stuff
import core.data.kb.vuln as vuln
import core.data.constants.severity as severity
import core.data.kb.knowledgeBase as kb
import core.data.kb.config as cf


class osCommanding(baseAuditPlugin):
    '''
    Find OS Commanding vulnerabilities.
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''

    FILE_PATTERNS = (
        "root:x:0:0:",  
        "daemon:x:1:1:",
        ":/bin/bash",
        ":/bin/sh",

        # /etc/passwd in AIX
        "root:!:x:0:0:",
        "daemon:!:x:1:1:",
        ":usr/bin/ksh",

        # boot.ini
        "[boot loader]",
        "default=multi(",
        "[operating systems]",
            
        # win.ini
        "[fonts]",
    )
    _multi_in = multi_in( FILE_PATTERNS )
    
    def __init__(self):
        baseAuditPlugin.__init__(self)
        
        #
        #   Some internal variables
        #
        self._special_chars = ['', '&&', '|', ';']
        # The wait time of the unfuzzed request
        self._original_wait_time = 0
        self._file_compiled_regex = []
                

    def audit(self, freq ):
        '''
        Tests an URL for OS Commanding vulnerabilities.
        
        @param freq: A fuzzableRequest
        '''
        om.out.debug( 'osCommanding plugin is testing: ' + freq.getURL() )
        
        # We are implementing two different ways of detecting OS Commanding
        # vulnerabilities:
        #       - Time delays
        #       - Writing a known file to the HTML output
        # The basic idea is to be able to detect ANY vulnerability, so we use ALL
        # of the known techniques
        #
        # Please note that I'm running the echo ones first in order to get them into
        # the KB before the ones with time delays so that the osCommanding exploit
        # can (with a higher degree of confidence) exploit the vulnerability
        #
        # This also speeds-up the detection process a little bit in the cases where
        # there IS a vulnerability present and can be found with both methods.
        self._with_echo(freq)
        self._with_time_delay(freq)
    
    def _with_echo(self, freq):
        '''
        Tests an URL for OS Commanding vulnerabilities using cat/type to write the 
        content of a known file (i.e. /etc/passwd) to the HTML.
        
        @param freq: A fuzzableRequest
        '''
        original_response = self._uri_opener.send_mutant(freq)
        # Prepare the strings to create the mutants
        command_list = self._get_echo_commands()
        only_command_strings = [ v.get_command() for v in command_list ]
        mutants = createMutants( freq , only_command_strings, oResponse=original_response )

        for mutant in mutants:

            # Only spawn a thread if the mutant has a modified variable
            # that has no reported bugs in the kb
            if self._has_no_bug(mutant):
                args = (mutant,)
                kwds = {'callback': self._analyze_echo }
                self._run_async(meth=self._uri_opener.send_mutant, args=args,
                                                                    kwds=kwds)
        self._join()
                
    def _analyze_echo( self, mutant, response ):
        '''
        Analyze results of the _send_mutant method that was sent in the _with_echo method.
        '''
        with self._plugin_lock:
            
            #
            #   I will only report the vulnerability once.
            #
            if self._has_no_bug(mutant):
                
                for file_pattern_match in self._multi_in.query( response.getBody() ):
                    
                    if file_pattern_match not in mutant.getOriginalResponseBody():
                        # Search for the correct command and separator
                        sentOs, sentSeparator = self._get_os_separator(mutant)

                        # Create the vuln obj
                        v = vuln.vuln( mutant )
                        v.setPluginName(self.getName())
                        v.setName( 'OS commanding vulnerability' )
                        v.setSeverity(severity.HIGH)
                        v['os'] = sentOs
                        v['separator'] = sentSeparator
                        v.setDesc( 'OS Commanding was found at: ' + mutant.foundAt() )
                        v.setDc( mutant.getDc() )
                        v.setId( response.id )
                        v.setURI( response.getURI() )
                        v.addToHighlight( file_pattern_match )
                        kb.kb.append( self, 'osCommanding', v )
                        break
    
    def _get_os_separator(self, mutant):
        '''
        @parameter mutant: The mutant that is being analyzed.
        @return: A tuple with the OS and the command separator
        that was used to generate the mutant.
        '''
        # Retrieve the data I need to create the vuln and the info objects
        command_list = self._get_echo_commands()
        
        ### BUGBUG: Are you sure that this works as expected?!?!?!
        for comm in command_list:
            if comm.get_command() in mutant.getModValue():
                os = comm.get_OS()
                separator = comm.get_separator()
        return os, separator

    def _with_time_delay(self, freq):
        '''
        Tests an URL for OS Commanding vulnerabilities using time delays.
        
        @param freq: A fuzzableRequest
        '''
        fake_mutants = createMutants(freq, ['',])
        
        for mutant in fake_mutants:
            
            if self._has_bug(mutant):
                continue
            
            for delay_obj in self._get_wait_commands():
                
                ed = exact_delay(mutant, delay_obj, self._uri_opener)
                success, responses = ed.delay_is_controlled()
                
                if success:
                    v = vuln.vuln( mutant )
                    v.setPluginName(self.getName())
                    v.setName( 'OS commanding vulnerability' )
                    v.setSeverity(severity.HIGH)
                    v['os'] = delay_obj.get_OS()
                    v['separator'] = delay_obj.get_separator()
                    v.setDesc( 'OS Commanding was found at: ' + mutant.foundAt() )
                    v.setDc( mutant.getDc() )
                    v.setId( [r.id for r in responses] )
                    v.setURI( r.getURI() )
                    kb.kb.append( self, 'osCommanding', v )
                    
                    break

    def end(self):
        '''
        This method is called when the plugin wont be used anymore.
        '''
        self._join()
        self.printUniq(kb.kb.getData('osCommanding', 'osCommanding'), 'VAR')
    
    def _get_echo_commands(self):
        '''
        @return: This method returns a list of commands to try to execute in order
        to print the content of a known file.
        '''
        commands = []
        for special_char in self._special_chars:
            # Unix
            cmd_string = special_char + "/bin/cat /etc/passwd"
            commands.append( base_command(cmd_string, 'unix', special_char))
            # Windows
            cmd_string = special_char + "type %SYSTEMROOT%\\win.ini"
            commands.append( base_command(cmd_string, 'windows', special_char))
        
        # Execution quotes
        commands.append( base_command("`/bin/cat /etc/passwd`", 'unix', '`'))		
        # FoxPro uses run to run os commands. I found one of this vulns !!
        commands.append( base_command("run type %SYSTEMROOT%\\win.ini", 'windows', 'run'))
        
        # Now I filter the commands based on the targetOS:
        targetOS = cf.cf.getData('targetOS').lower()
        commands = [ c for c in commands if c.get_OS() == targetOS or targetOS == 'unknown']

        return commands
    
    def _get_wait_commands( self ):
        '''
        @return: This method returns a list of commands to try to execute in order
        to introduce a time delay.
        '''
        commands = []
        for special_char in self._special_chars:
            # Windows
            cmd_fmt = special_char + 'ping -n %s localhost'
            delay_cmd = ping_delay( cmd_fmt, 'windows', special_char)
            commands.append( delay_cmd )
            
            # Unix
            cmd_fmt = special_char + 'ping -c %s localhost'
            delay_cmd = ping_delay( cmd_fmt, 'unix', special_char)
            commands.append( delay_cmd )
            
            # This is needed for solaris 10
            cmd_fmt = special_char + '/usr/sbin/ping -s localhost %s'
            delay_cmd = ping_delay( cmd_fmt, 'unix', special_char)
            commands.append( delay_cmd )
        
        # Using execution quotes
        commands.append( ping_delay( '`ping -n %s localhost`', 'windows', '`'))
        commands.append( ping_delay( '`ping -c %s localhost`', 'unix', '`'))
        
        # FoxPro uses the "run" macro to exec os commands. I found one of this vulns !!
        commands.append( ping_delay( 'run ping -n %s localhost', 'windows', 'run '))
        
        # Now I filter the commands based on the targetOS:
        targetOS = cf.cf.getData('targetOS').lower()
        commands = [ c for c in commands if c.get_OS() == targetOS or targetOS == 'unknown']
        
        return commands
        
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
        This plugin will find OS commanding vulnerabilities. The detection is 
        performed using two different techniques:
            - Time delays
            - Writing a known file to the HTML output
        
        With time delays, the plugin sends specially crafted requests that,
        if the vulnerability is present, will delay the response for 5 seconds
        (ping -c 5 localhost). 
        
        When using the second technique, the plugin sends specially crafted requests
        that, if the vulnerability is present, will print the content of a known file
        (i.e. /etc/passwd) to the HTML output
        
        This plugin has a rather long list of command separators, like ";" and "`" to
        try to match all programming languages, platforms and installations.
        '''


class base_command:
    '''
    Defines a command that is going to be sent to the remote web app.
    '''
    def __init__( self, comm, os, sep ):
        self._comm = comm
        self._os = os
        self._sep = sep
    
    def get_OS( self ):
        '''
        @return: The OS
        '''
        return self._os
        
    def get_command( self ):
        '''
        @return: The Command to be executed
        '''
        return self._comm
        
    def get_separator( self ):
        '''
        @return: The separator, could be one of ; && | etc.
        '''
        return self._sep

class ping_delay(base_command, delay):
    def __init__(self, delay_fmt, os, sep):
        base_command.__init__(self, delay_fmt, os, sep)
        delay.__init__(self, delay_fmt)
        self._delay_delta = 1

