'''
test_all_false_positive.py

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
from nose.plugins.skip import Skip, SkipTest


class TestAllFP(PluginTest):
    
    target_url = 'http://moth/w3af/core/base_false_positive/'
    
   
    def test_false_positive(self):
        raise SkipTest('FIXME: This test takes too long to run.')
    
        audit_plugin_names = self.w3afcore.plugins.getPluginList('audit')

        for audit_plugin in audit_plugin_names:
            run_config = {
                'target': self.target_url,
                'plugins': {
                     'audit': (PluginConfig(audit_plugin),),
                     'discovery': (
                         PluginConfig(
                             'webSpider',
                             ('onlyForward', True, PluginConfig.BOOL)),
                     )                 
                     }
                }
            
            # I tried to do this in the right way, with test generators,
            # but they didn't seem to work for me.
            self.setUp()
            
            target = run_config['target']
            plugins = run_config['plugins']
            self._scan(target, plugins)
    
            vulns = self.kb.getAllVulns()
            infos = self.kb.getAllInfos()
            
            vulns = [str(v) for v in vulns]
            infos = [str(i) for i in infos]
            
            msg_v = 'audit.%s found a vulnerability in "%s"' % (audit_plugin, ','.join(vulns) )
            msg_i = 'audit.%s found a vulnerability in "%s"' % (audit_plugin, ','.join(infos) )
            
            self.assertEquals( len(vulns) , 0, msg_v)
            self.assertEquals( len(infos) , 0, msg_i)
            
            