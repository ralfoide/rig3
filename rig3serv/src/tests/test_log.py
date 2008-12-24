#!/usr/bin/python
#-----------------------------------------------------------------------------|
"""
Unit tests for Log

Part of Rig3.
License GPL.
"""
__author__ = "ralfoide at gmail com"

import StringIO

from tests.rig_test_case import RigTestCase
from rig.log import Log

#------------------------
class LogTest(RigTestCase):

    def setUp(self):
        self._str = StringIO.StringIO()
        # Configure the logger to use the StringIO has file output
        # Fix the date so that it doesn't affect tests
        # Fix the format so that it be independant of the date, line number and
        # of the default formatting in the default configuration.
        self._log = Log(file=self._str,
                        verbose_level=Log.LEVEL_MOSLTY_SILENT,
                        use_stderr=self.IsVerbose(),
                        format="%(levelname)s %(filename)s [%(asctime)s] %(message)s",
                        date="1901/01/02 12:13:14")

    def tearDown(self):
        self._log.Close()
        pass

    def testLogging(self):
        self.assertNotEquals(None, self._log)
        self.assertEquals("", self._str.getvalue())
        self._log.Warn("test_simple")
        self.assertMatches(r"WARNING (?:.*[/\\])?test_log\.py \[1901/01/02 12:13:14\] test_simple\n",
                           self._str.getvalue())

#------------------------
# Local Variables:
# mode: python
# tab-width: 4
# py-continuation-offset: 4
# py-indent-offset: 4
# sentence-end-double-space: nil
# fill-column: 79
# End:
