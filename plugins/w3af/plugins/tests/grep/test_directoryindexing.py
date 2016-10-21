'''
test_directoryindexing.py

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

class TestDirectoryIndexing(PluginTest):
    
    dir_indexing_url = 'http://moth/w3af/grep/directory_indexing/'
    
    _run_configs = {
        'cfg1': {
            'target': dir_indexing_url,
            'plugins': {
                'grep': (PluginConfig('directoryIndexing'),)
            }
        }
    }
    
    def test_found_vuln(self):
        cfg = self._run_configs['cfg1']
        self._scan(cfg['target'], cfg['plugins'])
        vulns = self.kb.getData('directoryIndexing', 'directory')
        self.assertEquals(1, len(vulns))
        v = vulns[0]
        self.assertEquals(self.dir_indexing_url, str(v.getURL()))
        self.assertEquals(severity.LOW, v.getSeverity())
        self.assertEquals(
                  'Directory indexing - /w3af/grep/directory_indexing/',
                  v.getName()
                  )