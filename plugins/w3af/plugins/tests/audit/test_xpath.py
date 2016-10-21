'''
test_xpath.py

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

class TestXPATH(PluginTest):
    
    target_url = 'http://moth/w3af/audit/xpath/'
    
    _run_configs = {
        'cfg': {
            'target': target_url,
            'plugins': {
                 'audit': (PluginConfig('xpath'),),
                 'discovery': (
                      PluginConfig(
                          'webSpider',
                          ('onlyForward', True, PluginConfig.BOOL)),
                  )
                 }
            }
        }
    
    def test_found_xpath(self):
        # Run the scan
        cfg = self._run_configs['cfg']
        self._scan(cfg['target'], cfg['plugins'])

        # Assert the general results
        expected_vuln_number = 4
        vulns = self.kb.getData('xpath', 'xpath')
        self.assertEquals(expected_vuln_number, len(vulns))
        self.assertEquals(all(["XPATH injection vulnerability" == vuln.getName() for vuln in vulns ]) , True)

        # Verify the specifics about the vulnerabilities
        expected = [
            ('xpath-tag.php', 'input'),
            ('xpath-attr-single.php', 'input'),
            ('xpath-attr-double.php', 'input'),
            ('xpath-or.php', 'input')
        ]

        verified_vulns = 0
        for vuln in vulns:
            if ( vuln.getURL().getFileName() , vuln.getMutant().getVar() ) in expected:
                verified_vulns += 1

        self.assertEquals(expected_vuln_number, verified_vulns)

