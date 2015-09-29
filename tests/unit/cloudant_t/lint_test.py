#!/usr/bin/env python
# Copyright (c) 2015 IBM. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""
_lint_test_

Perform lint evaluation on library source code.

"""

import unittest
from pylint import epylint

class LintTests(unittest.TestCase):
    """
    Evaluate lint test output.

    """
    def test_pylint_cloudant(self):
        """
        Apply Pylint to Python-Cloudant Client Library

        """

        # We only want the Global evaluation report (RP0004)
        # for the cloudant package.
        pkg = 'cloudant'
        disable = 'RP0001,RP0002,RP0003,RP0101,RP0401,RP0402,RP0701,RP0801'
        options = '{0} -d \"{1}\"'.format(pkg, disable)
        (out, err) = epylint.py_run(options, return_std=True, script='pylint')
        err_report = [ e_line.strip() for e_line in err ]
        self.assertEqual(err_report, [])

        passed = False
        for line in out:
            if line.find('Your code has been rated at 10.00/10') == 0:
                # Found the 10.00/10 in the Global evaluation report
                passed = True
                break
        fail_msg = 'Pylint check failed. Run pylint cloudant for more details.'
        self.assertTrue(passed, fail_msg)


if __name__ == '__main__':
    unittest.main()
