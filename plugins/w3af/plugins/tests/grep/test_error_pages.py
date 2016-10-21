'''
test_error_pages.py

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

from ..helper import PluginTest, PluginConfig
import core.data.constants.severity as severity

class TestErrorPages(PluginTest):
    
    target_url = 'http://moth/w3af/grep/error_pages/error_page.html'
    
    _run_configs = {
        'cfg': {
            'target': target_url,
            'plugins': {
                'grep': (PluginConfig('errorPages'),)
            }
        }
    }
    
    def test_found_vuln(self):
        cfg = self._run_configs['cfg']
        self._scan(cfg['target'], cfg['plugins'])

        infos = self.kb.getData('errorPages', 'errorPage')
        info = infos[0]

        self.assertEquals(1, len(infos))
        self.assertEquals(self.target_url, str(info.getURL()))
        self.assertEquals(severity.INFORMATION, info.getSeverity())
        self.assertTrue(info.getName().startswith('Descriptive error page'))

        '''
        infos = self.kb.getData('errorPages', 'server')
        info = infos[0]

        self.assertEquals(1, len(infos))
        self.assertEquals(self.target_url, str(info.getURL()))
        self.assertEquals(severity.INFORMATION, info.getSeverity())
        self.assertTrue(info.getName().startswith('Error page with information disclosure'))
        '''
