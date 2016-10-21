'''
test_os_commanding_shell.py

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


class TestOSCommandingShell(PluginTest):
    
    target_url = 'http://moth/w3af/audit/os_commanding/'
    
    _run_configs = {
        'cfg': {
            'target': target_url,
            'plugins': {
                 'audit': (PluginConfig('osCommanding'),),
                 'discovery': (
                      PluginConfig(
                          'webSpider',
                          ('onlyForward', True, PluginConfig.BOOL)),
                  )
                 }
            }
        }
    
    def test_found_exploit_osc(self):
        # Run the scan
        cfg = self._run_configs['cfg']
        self._scan(cfg['target'], cfg['plugins'])

        # Assert the general results
        vulns = self.kb.getData('osCommanding', 'osCommanding')
        self.assertEquals(4, len(vulns))
        self.assertEquals(all(["OS commanding vulnerability" == v.getName() for v in vulns ]),
                          True)

        # Verify the specifics about the vulnerabilities
        EXPECTED = [
            ('passthru.php', 'cmd'),
            ('simple_osc.php', 'cmd'),
            ('param_osc.php', 'param'),
            ('blind_osc.php', 'cmd')
        ]

        found_vulns = [ (v.getURL().getFileName() , v.getMutant().getVar()) for v in vulns]
        
        self.assertEquals( set(EXPECTED),
                           set(found_vulns)
                          )

        vuln_to_exploit_id = [v.getId() for v in vulns 
                              if v.getURL().getFileName() == 'simple_osc.php'][0]
        
        plugin = self.w3afcore.plugins.getPluginInstance( 'osCommandingShell', 'attack' )
        
        self.assertTrue( plugin.canExploit( vuln_to_exploit_id ) )
        
        exploit_result = plugin.exploit( vuln_to_exploit_id )

        self.assertGreaterEqual(len(exploit_result), 1)
        
        #
        # Now I start testing the shell itself!
        #
        shell = exploit_result[0]
        etc_passwd = shell.generic_user_input('exec cat /etc/passwd')
        
        self.assertTrue( 'root' in etc_passwd )
        
        lsp = shell.generic_user_input('lsp')
        self.assertTrue( 'apache_config_directory' in lsp )
        
        payload = shell.generic_user_input('payload apache_config_directory')
        self.assertTrue( payload is None )
        
        