'''
test_fileupload.py

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

class TestFileUpload(PluginTest):
    
    file_upload_url = 'http://moth/w3af/audit/file_upload/'
    
    _run_configs = {
        'cfg': {
            'target': file_upload_url,
            'plugins': {
                'audit': (
                    PluginConfig(
                        'fileUpload', ('extensions',
                         ['gif', 'html', 'bmp', 'jpg', 'png', 'txt'],
                         PluginConfig.LIST)
                     ),)
            },}
    }
    
    def test_reported_file_uploads(self):
        cfg = self._run_configs['cfg']
        self._scan(cfg['target'], cfg['plugins'])
        fuvulns = self.kb.getData('fileUpload', 'fileUpload')
        self.assertEquals(1, len(fuvulns))
        
        v = fuvulns[0]
        self.assertEquals(v.getName(), 'Insecure file upload')
        self.assertEquals(str(v.getURL().getDomainPath()), self.file_upload_url)