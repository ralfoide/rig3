#!/usr/bin/python
#-----------------------------------------------------------------------------|
"""
Extended TestCase for rig3 tests.

Part of Rig3.
License GPL.
"""
__author__ = "ralfoide@gmail.com"

import os
import re
import unittest
import StringIO
import tempfile

from rig.log import Log

IS_VERBOSE = False

#------------
class RigTestCase(unittest.TestCase):

    def __init__(self, methodName='runTest'):
        self.__log = None
        unittest.TestCase.__init__(self, methodName)

    def SetVerbose(verbose):
        """
        Static methods that sets the global verbosity flag.
        """
        global IS_VERBOSE
        IS_VERBOSE = verbose
    setVerbose = staticmethod(SetVerbose)

    def IsVerbose(self):
        """
        Convenience method that indicates if the current unit tests are
        running in verbose mode.
        """
        global IS_VERBOSE
        return IS_VERBOSE

    def getTestDataPath(self):
        f = __file__
        return os.path.realpath(os.path.join(os.path.dirname(f), "..", "..", "testdata"))

    def Log(self):
        """
        Creates or returns a rig3 Log object.
        """
        if self.__log is None:
            self._str = StringIO.StringIO()
            # Configure the logger to use the StringIO has file output
            # Fix the date so that it doesn't affect tests
            # Fix the format so that it be independant of the date, line number and
            # of the default formatting in the default configuration.
            self.__log = Log(file=self._str,
                             verbose_level=self.IsVerbose() and Log.LEVEL_VERY_VERBOSE or Log.LEVEL_NORMAL,
                             use_stderr=self.IsVerbose(),
                             format="%(levelname)s %(filename)s [%(asctime)s] %(message)s",
                             date="%H:%M:%S")
        return self.__log

    def MakeTempDir(self):
        """
        Utility to create a temp directory. Use RemoveDir() to remove it later.
        Really, just a wrapper around tempfile.mkdtemp. Beause the directory is
        new, we are pretty much guaranteed it will be empty.
        """
        return tempfile.mkdtemp()
    
    def RemoveDir(self, dir_path):
        """
        Assuming dir_path points to an existing directory, removes all
        files and sub-directories recursively, then removes the actual
        directory itself.
        
        This is different from os.removedirs() which can only deal with
        *empty* directories :-(
        """
        try:
            if dir_path and os.path.exists(dir_path) and os.path.isdir(dir_path):
                for n in os.listdir(dir_path):
                    p = os.path.join(dir_path, n)
                    if os.path.isdir(p):
                        self.RemoveDir(p)
                    else:
                        os.unlink(p)
                os.rmdir(dir_path)
        except OSError, e:
            self.Log().Exception("RemoveDir '%s' failed: %s", dir_path, e)


    # Fancy asserts

    def assertSame(self, expected, actual, msg=None):
        """
        Asserts that the two reference point to the same object, not just
        equal objects. This compares the internal object ids.
        """
        msg = "%s\nExpected: %s\nActual  : %s" % \
              (msg or "assertSame failed", expected, actual)
        self.assertEquals(id(expected), id(actual), msg)

    def assertSearch(self, expected_regexp, actual, msg=None):
        """
        Asserts that the expected regexp can be found in the actual string
        using a free search, not a complete match.
        Parameters:
        - expected_regexp (string): A regexp string to search for.
        - actual (string): The actual value to search within.
        """
        msg = "%s\nExpected regexp: %s\nActual  : %s" % \
              (msg or "assertSearch failed", expected_regexp, actual)
        self.assertTrue(re.search(expected_regexp, actual), msg)

    def assertNotSearch(self, unwanted_regexp, actual, msg=None):
        """
        Asserts that the expected regexp cannot be found in the actual string
        using a free search, not a complete match.
        Parameters:
        - expected_regexp (string): A regexp string to search for.
        - actual (string): The actual value to search within.
        """
        msg = "%s\nUnwanted regexp: %s\nActual  : %s" % \
              (msg or "assertNotSearch failed", unwanted_regexp, actual)
        self.assertFalse(re.search(unwanted_regexp, actual), msg)

    def assertMatches(self, expected_regexp, actual, msg=None):
        """
        Asserts that the actual string value matches the expected regexp
        at least at the beginning of the string. If you want a perfect full
        match you need to use the end-of-string $ anchor.
        Parameters:
        - expected_regexp (string): A regexp string to match.
        - actual (string): The actual value to match with.
        """
        msg = "%s\nExpected regexp: %s\nActual  : %s" % \
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
        """
        Asserts that two dictionaries are equal.
        This also asserts that both expected and actual values are
        really dictionary.
        """
        msg = "%s\nExpected: %s\nActual  : %s" % \
                (msg or "assertDictEquals failed", repr(expected), repr(actual))
        self.assertTrue(isinstance(actual, dict), msg)
        self.assertTrue(isinstance(expected, dict), msg)
        self.assertEquals(expected, actual, msg)

    def assertListEquals(self, expected, actual, msg=None, sort=False):
        """
        Asserts that two lists are equal.
        This also asserts that both expected and actual values are
        really list.
        
        Sometimes the order of lists should not matter. The 'sort' argument
        controls that:
        - False: the default list equality is used, which is by default order-sensitive.
        - True: both lists are *duplicated* then sorted using list.sort()
        - A non boolean: both lists are duplicated then sorted and the sort argument is used
          as the 'cmp' comparator for the sort operation, typically a lambda, e.g.
           sort=lambda x, y : x < y
        """
        msg = "%s\nExpected: %s\nActual  : %s" % \
                (msg or "assertListEquals failed", repr(expected), repr(actual))
        self.assertTrue(isinstance(actual, list), msg)
        self.assertTrue(isinstance(expected, list), msg)
        if sort is not False:
            expected = list(expected)
            actual = list(actual)
            if sort is True:
                expected.sort()
                actual.sort()
            else:
                expected.sort(cmp=sort)
                actual.sort(cmp=sort)
        self.assertEquals(expected, actual, msg)

    def assertHtmlEquals(self, expected, actual, msg=None):
        """
        Compares to string after HTML normalization.
        See NormalizeHtml for details.
        """
        msg = "%s\nExpected: %s\nActual  : %s" % \
                (msg or "assertHtmlEquals failed", repr(expected), repr(actual))
        actual = self.NormalizeHtml(actual)
        expected = self.NormalizeHtml(expected)
        self.assertEquals(expected, actual, msg)

    def assertHtmlMatches(self, expected_regexp, actual, msg=None):
        """
        Similar to assertHtmlEquals, compares to HTML normalized strings.
        However the expected_regexp string is considered as a regexp and a
        strict match is expected with the actual string -- that is it must
        match the *beginning* of actual. Use a $ anchor to also force matching
        the end. 
        """
        msg = "%s\nExpected: %s\nActual  : %s" % \
                (msg or "assertHtmlMatches failed", repr(expected_regexp), repr(actual))
        actual = self.NormalizeHtml(actual)
        expected_regexp = self.NormalizeHtml(expected_regexp)
        self.assertMatches(expected_regexp, actual, msg)

    # Internal Utilities
    
    def NormalizeHtml(self, str):
        """
        Normalize HTML for comparison. The strings are "normalized" to help make
        comparisons more meaningful:
        - \n or \r\n is irrelevant and thus removed (or more exactly replaced by a space)
        - spaces are collapsed
        - spaces before or after tag delimiters < /> or < > are removed.
        - tag names are changed to lower case
        """
        str = re.sub("[\r\n]+", " ", str)
        str = re.sub(" +", " ", str)
        str = re.sub(" <", "<", str)
        str = re.sub("> ", ">", str)
        str = re.sub("</?[a-zA-Z0-9]+", lambda x: x.group(0).lower(), str)
        return str

#------------------------
# Local Variables:
# mode: python
# tab-width: 4
# py-continuation-offset: 4
# py-indent-offset: 4
# sentence-end-double-space: nil
# fill-column: 79
# End:
