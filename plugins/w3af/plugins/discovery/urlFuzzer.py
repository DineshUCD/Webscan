'''
urlFuzzer.py

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
from itertools import chain

from core.controllers.basePlugin.baseDiscoveryPlugin import baseDiscoveryPlugin
from core.controllers.coreHelpers.fingerprint_404 import is_404
from core.controllers.w3afException import w3afException
from core.data.bloomfilter.bloomfilter import scalable_bloomfilter
from core.data.fuzzer.fuzzer import createRandAlNum
from core.data.options.option import option
from core.data.options.optionList import optionList
from core.data.parsers.urlParser import url_object
import core.controllers.outputManager as om
import core.data.kb.info as info
import core.data.kb.knowledgeBase as kb


class urlFuzzer(baseDiscoveryPlugin):
    '''
    Try to find backups, and other related files.
    @author: Andres Riancho ( andres.riancho@gmail.com )  
    '''
    _appendables = ('~', '.tar.gz', '.gz', '.7z', '.cab', '.tgz',
        '.gzip', '.bzip2', '.inc', '.zip', '.rar', '.jar', '.java',
        '.class', '.properties', '.bak', '.bak1', '.bkp', '.back',
        '.backup', '.backup1', '.old', '.old1', '.$$$'
        )
    _backup_exts = ('tar.gz', '7z', 'gz', 'cab', 'tgz', 'gzip',
        'bzip2', 'zip', 'rar'
        )
    _file_types = (
        'inc', 'fla', 'jar', 'war', 'java', 'class', 'properties',
        'bak', 'bak1', 'backup', 'backup1', 'old', 'old1', 'c', 'cpp',
        'cs', 'vb', 'phps', 'disco', 'ori', 'orig', 'original'
        )
    
    def __init__(self):
        baseDiscoveryPlugin.__init__(self)
        
        self._first_time = True
        self._fuzzImages = False
        self._headers = {}
        self._seen = scalable_bloomfilter()
        
    def discover(self, fuzzableRequest):
        '''
        Searches for new Url's using fuzzing.
        
        @parameter fuzzableRequest: A fuzzableRequest instance that contains (among other things) the URL to test.
        '''
        self._fuzzable_requests = []
            
        url = fuzzableRequest.getURL()
        self._headers = {'Referer': url}
        
        if self._first_time:
            self._verify_head_enabled(url)
            self._first_time = False
        
        # First we need to delete fragments and query strings from URL.
        url = url.uri2url()

        # And we mark this one as a "do not return" URL, because the
        # core already found it using another technique.
        self._seen.add(url)
        
        self._verify_head_enabled(url)
        if self._head_enabled():
            response = self._uri_opener.HEAD(url, cache=True, headers=self._headers)
        else:
            response = self._uri_opener.GET(url, cache=True, headers=self._headers)

        if response.is_text_or_html() or self._fuzzImages:
            om.out.debug('urlFuzzer is testing "%s"' % url)
            
            mutants = chain(self._mutate_by_appending(url),
                            self._mutate_path(url),
                            self._mutate_file_type(url),
                            self._mutate_domain_name(url))
            for mutant in mutants:
                self._run_async(meth=self._do_request, args=(url, mutant))
            self._join()
        
        return self._fuzzable_requests

    def _do_request(self, url, mutant):
        '''
        Perform a simple GET to see if the result is an error or not, and then
        run the actual fuzzing.
        '''
        response = self._uri_opener.GET(mutant, cache=True, headers=self._headers)

        if not (is_404(response) or
                response.getCode() in (403, 401) or
                self._return_without_eval(mutant)):
            fr_list = self._createFuzzableRequests(response)
            self._fuzzable_requests.extend(fr_list)
            #
            #   Save it to the kb (if new)!
            #
            if response.getURL() not in self._seen and response.getURL().getFileName():
                i = info.info()
                i.setPluginName(self.getName())
                i.setName('Potentially interesting file')
                i.setURL(response.getURL())
                i.setId(response.id)
                i.setDesc('A potentially interesting file was found at: "' + response.getURL() + '".')
                kb.kb.append(self, 'files', i)
                om.out.information(i.getDesc())
                
                # Report only once
                self._seen.add(response.getURL())
    
    def _return_without_eval(self, uri):
        '''
        This method tries to lower the false positives. 
        '''     
        if not uri.hasQueryString():
            return False
        
        uri.setFileName(uri.getFileName() + createRandAlNum(7))
            
        try:
            response = self._uri_opener.GET(
                                   uri, cache=True, headers=self._headers)
        except w3afException, e:
            msg = 'An exception was raised while requesting "' + uri + '" , the error message is: '
            msg += str(e)
            om.out.error(msg)
        else:
            if not is_404(response):
                return True
        return False
    
    def _mutate_domain_name(self, url):
        '''
        If the url is : "http://www.foobar.com/asd.txt" this method returns:
            - http://www.foobar.com/foobar.zip
            - http://www.foobar.com/foobar.rar
            - http://www.foobar.com/www.foobar.zip
            - http://www.foobar.com/www.foobar.rar
            - etc...
        
        @parameter url: An url_object to transform.
        @return: A list of url_object's that mutate the original url passed as parameter.

        >>> from core.data.parsers.urlParser import url_object
        >>> u = urlFuzzer()
        >>> url = url_object('http://www.w3af.com/')
        >>> mutants = list(u._mutate_domain_name(url))
        >>> url_object('http://www.w3af.com/www.tar.gz') in mutants
        True
        >>> url_object('http://www.w3af.com/www.w3af.tar.gz') in mutants
        True
        >>> url_object('http://www.w3af.com/www.w3af.com.tar.gz') in mutants
        True
        >>> len(mutants) > 20
        True
        
        '''
        domain = url.getDomain()
        domain_path = url.getDomainPath()
        
        splitted_domain = domain.split('.')
        for i in xrange(len(splitted_domain)):
            filename = '.'.join(splitted_domain[0: i + 1])
            
            for extension in self._backup_exts:
                filename_ext = filename + '.' + extension
                
                domain_path_copy = domain_path.copy()
                domain_path_copy.setFileName(filename_ext)
                yield domain_path_copy
        
    def _mutate_by_appending(self, url):
        '''
        Adds something to the end of the url (mutate the file being requested)
        
        @parameter url: An url_object to transform.
        @return: A list of url_object's that mutate the original url passed as parameter.

        >>> from core.data.parsers.urlParser import url_object
        >>> u = urlFuzzer()
        >>> url = url_object( 'http://www.w3af.com/' )
        >>> mutants = u._mutate_by_appending( url )
        >>> list(mutants)
        []
        
        >>> url = url_object( 'http://www.w3af.com/foo.html' )
        >>> mutants = u._mutate_by_appending( url )
        >>> url_object( 'http://www.w3af.com/foo.html~' ) in mutants
        True
        >>> len(list(mutants)) > 20
        True

        '''
        if not url.url_string.endswith('/') and url.url_string.count('/') >= 3:
            #
            #   Only get here on these cases:
            #       - http://host.tld/abc
            #       - http://host.tld/abc/def.html
            #
            #   And not on these:
            #       - http://host.tld
            #       - http://host.tld/abc/
            #
            for to_append in self._appendables:
                url_copy = url.copy()
                filename = url_copy.getFileName()
                filename += to_append
                url_copy.setFileName(filename)
                yield url_copy
    
    def _mutate_file_type(self, url):
        '''
        If the url is : "http://www.foobar.com/asd.txt" this method returns:
            - http://www.foobar.com/asd.zip
            - http://www.foobar.com/asd.tgz
            - etc...
        
        @parameter url: An url_object to transform.
        @return: A list of url_object's that mutate the original url passed as parameter.

        >>> from core.data.parsers.urlParser import url_object
        >>> u = urlFuzzer()
        >>> list(u._mutate_file_type(url_object('http://www.w3af.com/')))
        []
        
        >>> url = url_object('http://www.w3af.com/foo.html')
        >>> mutants = list(u._mutate_file_type( url))
        >>> url_object('http://www.w3af.com/foo.tar.gz') in mutants
        True
        >>> url_object('http://www.w3af.com/foo.disco') in mutants
        True
        >>> len(mutants) > 20
        True

        '''
        extension = url.getExtension()
        if extension:
            for filetype in chain(self._backup_exts, self._file_types):
                url_copy = url.copy()
                url_copy.setExtension(filetype)
                yield url_copy

    def _mutate_path(self, url):
        '''
        Mutate the path instead of the file.
        
        @parameter url: An url_object to transform.
        @return: A list of url_object's that mutate the original url passed as parameter.

        >>> from core.data.parsers.urlParser import url_object
        >>> u = urlFuzzer()
        >>> url = url_object( 'http://www.w3af.com/' )
        >>> list(u._mutate_path(url))
        []
        
        >>> url = url_object( 'http://www.w3af.com/foo.html' )
        >>> list(u._mutate_path(url))
        []
        
        >>> url = url_object('http://www.w3af.com/foo/bar.html' )
        >>> mutants = list(u._mutate_path(url))
        >>> url_object('http://www.w3af.com/foo.tar.gz') in mutants
        True
        >>> url_object('http://www.w3af.com/foo.old') in mutants
        True
        >>> url_object('http://www.w3af.com/foo.zip') in mutants
        True
        '''
        url_string = url.url_string
        
        if url_string.count('/') > 3:
            # Create the new path
            url_string = url_string[:url_string.rfind('/')]
            to_append_list = self._appendables
            for to_append in to_append_list:
                newurl = url_object(url_string + to_append)
                yield newurl
        
    def _verify_head_enabled(self, url):
        '''
        Verifies if the requested URL permits a HEAD request.
        This was saved inside the KB by the plugin allowedMethods
        
        @return : Sets self._head to the correct value, nothing is returned.
        '''
        if 'HEAD' in kb.kb.getData('allowedMethods' , 'methods'):
            self._head = True
        else:
            self._head = False
        
    def _head_enabled(self):
        return self._head
    
    def getOptions(self):
        '''
        @return: A list of option objects for this plugin.
        '''
        d1 = 'Apply URL fuzzing to all URLs, including images, videos, zip, etc.'
        h1 = 'Don\'t change this unless you read the plugin code.'
        o1 = option('fuzzImages', self._fuzzImages, d1, 'boolean', help=h1)
        
        ol = optionList()
        ol.add(o1)
        return ol

    def setOptions(self, optionsMap):
        '''
        This method sets all the options that are configured using the user interface 
        generated by the framework using the result of getOptions().
        
        @parameter OptionList: A dictionary with the options for the plugin.
        @return: No value is returned.
        ''' 
        self._fuzzImages = optionsMap['fuzzImages'].getValue()
    
    def getPluginDeps(self):
        '''
        @return: A list with the names of the plugins that should be run before the
        current one.
        '''
        return ['discovery.allowedMethods']
    
    def getLongDesc(self):
        '''
        @return: A DETAILED description of the plugin functions and features.
        '''
        return '''
        This plugin will try to find new URL's based on the input. If the input is for example:
            - http://a/a.html
            
        The plugin will request:
            - http://a/a.html.tgz
            - http://a/a.tgz
            - http://a/a.zip
            ... etc
        
        If the response is different from the 404 page (whatever it may be, automatic detection is 
        performed), then we have found a new URL. This plugin searches for backup files, source code
        , and other common extensions.
        
        One configurable parameter exist:
            - fuzzImages
        '''
