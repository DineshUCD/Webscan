'''
pdfParser.py

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
from core.data.parsers.baseparser import BaseParser
from core.data.parsers.urlParser import url_object


try:
    from extlib.pyPdf import pyPdf as pyPdf
except ImportError:
    import pyPdf
    
import StringIO
import re


class pdfParser(BaseParser):
    '''
    This class parses pdf documents to find mails and URLs. It's based in the pyPdf library.
    
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''
    def __init__(self, httpResponse):
        super(pdfParser, self).__init__(httpResponse)
        # Work !
        self._pre_parse(httpResponse.body)
        
    def _pre_parse(self, document):
        content_text = self.getPDFContent(document)
        self._parse(content_text)
    
    def _parse(self, content_text):

        # Get the URLs using a regex
        for x in re.findall(BaseParser.URL_RE, content_text):
            try:
                self._re_urls.add( url_object(x[0]) )
            except ValueError:
                pass
        
        # Get the mail addys
        self._findEmails(content_text)
        
    def getPDFContent(self, documentString):
        content = u""
        if documentString:
            # Load PDF into pyPDF
            pdfreader = pyPdf.PdfFileReader(StringIO.StringIO(documentString))
            try:
                content = u"\n".join(p.extractText() for p in pdfreader.pages)
            except Exception, e:
                om.out.debug('Exception in getPDFContent(), error: ' + str(e))
        return content
    
    def getReferences( self ):
        '''
        Searches for references on a page. w3af searches references in every html tag, including:
            - a
            - forms
            - images
            - frames
            - etc.
        
        @return: Two lists, one with the parsed URLs, and one with the URLs that came out of a
        regular expression. The second list if less trustworthy.
        '''
        return ([], list(self._re_urls))
        
    getReferencesOfTag = getForms = getComments = \
    getMetaRedir = getMetaTags = lambda *args, **kwds: []