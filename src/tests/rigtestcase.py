#!/usr/bin/python
#-----------------------------------------------------------------------------|
"""
Extended TestCase for rig3 tests.

Part of Rig3.
License GPL.
"""
__author__ = "ralfoide@gmail.com"

import re
import unittest
import StringIO

from rig.log import Log

IS_VERBOSE = False

#------------
class RigTestCase(unittest.TestCase):

    def __init__(self, methodName='runTest'):
        self._log = None
        unittest.TestCase.__init__(self, methodName)

    def isVerbose(self):
        """
        Convenience method that indicates if the current unit tests are
        running in verbose mode.
        """
        return IS_VERBOSE

    def log(self):
        """
        Creates or returns a rig3 Log object.
        """
        if self._log is None:
            self._str = StringIO.StringIO()
            # Configure the logger to use the StringIO has file output
            # Fix the date so that it doesn't affect tests
            # Fix the format so that it be independant of the date, line number and
            # of the default formatting in the default configuration.
            self._log = Log(file=self._str,
                            use_stderr=self.isVerbose(),
                            format="%(levelname)s %(filename)s [%(asctime)s] %(message)s",
                            date="%H:%M:%S")
        return self._log


    def assertMatches(self, expected_regexp, actual, msg=None):
        """
        Asserts that the actual string value matches the expected regexp.
        Parameters:
        - expected_regexp (string): A regexp string to match.
        - actual (string): The actual value to match with.
        """
        msg = "%s\nExpected regexp: %s\nActual: %s" % \
              (msg or "assertMatches failed", expected_regexp, actual)
        self.assertTrue(re.match(expected_regexp, actual), msg)

    def assertIsInstance(self, expected_types, actual, msg=None):
        """
        Asserts that the actual data is of the expected instance type.
        Test is done using isinstance(actual, expected).
        Parameters:
        - expected_type (type or list of types): One type or a list of types to
                                                 expect.
        - actual (expression): An expression which type is to be expected.
        """
        msg = "%s\nExpected types: %s\nActual type: %s" % \
                (msg or "assertIsInstance failed", repr(expected_types), repr(actual))
        self.assertTrue(isinstance(actual, expected_types), msg)

    def assertDictEquals(self, expected, actual, msg=None):
        msg = "%s\nExpected: %s\nActual: %s" % \
                (msg or "assertDictEquals failed", repr(expected), repr(actual))
        self.assertTrue(isinstance(actual, dict), msg)
        self.assertTrue(isinstance(expected, dict), msg)
        self.assertEquals(expected, actual, msg)

    def assertListEquals(self, expected, actual, msg=None):
        msg = "%s\nExpected: %s\nActual: %s" % \
                (msg or "assertListEquals failed", repr(expected), repr(actual))
        self.assertTrue(isinstance(actual, list), msg)
        self.assertTrue(isinstance(expected, list), msg)
        self.assertEquals(expected, actual, msg)


#------------------------
# Local Variables:
# mode: python
# tab-width: 4
# py-continuation-offset: 4
# py-indent-offset: 4
# sentence-end-double-space: nil
# fill-column: 79
# End:
