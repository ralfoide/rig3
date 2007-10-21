#!/usr/bin/python
#-----------------------------------------------------------------------------|
"""
Unit tests for Template

Part of Rig3.
License GPL.
"""
__author__ = "ralfoide@gmail.com"

import os
import StringIO

from tests.rig_test_case import RigTestCase
from rig.template import Template, Buffer

#------------------------
class MockParse(Template):
    def __init__(self, log, file=None, source=None):
        self.filename = None
        self.source = None
        super(MockParse, self).__init__(log, file=file, source=source)
    
    def _Parse(self, filename, source):
        self.filename = filename
        self.source = source

#------------------------
class TemplateTest(RigTestCase):

    def testInit(self):
        """
        Test init of Template
        """
        self.assertRaises(TypeError, Template)
        self.assertRaises(TypeError, Template, self.Log())

    def testInitParse(self):
        """
        Test that calling the constructor with file/source gives the
        correct data to the parser.
        """
        m = MockParse(self.Log(), file=None, source="something")
        self.assertEquals("something", m.source)
        self.assertEquals("source", m.filename)

        filename = os.path.join(self.getTestDataPath(), "simple.html")
        m = MockParse(self.Log(), file=filename, source=None)
        self.assertIsInstance(str, m.source)
        self.assertSearch("html", m.source)
        self.assertEquals(filename, m.filename)

        buf = StringIO.StringIO("template from StringIO")
        m = MockParse(self.Log(), file=buf, source=None)
        self.assertEquals("template from StringIO", m.source)
        self.assertEquals("file", m.filename)

#------------------------
class BufferTest(RigTestCase):
    def testInit(self):
        m = Buffer("filename", "data", 42)
        self.assertEquals("filename", m.filename)
        self.assertEquals("data", m.data)
        self.assertEquals(42, m.offset)
        self.assertEquals(1, m.lineno)

    def testEndReached(self):
        m = Buffer("filename", "data", 0)
        self.assertFalse(m.EndReached())
        m.offset = 3
        self.assertFalse(m.EndReached())
        m.offset = 4
        self.assertTrue(m.EndReached())

    def testStartsWith(self):
        m = Buffer("filename", "# for foreach !@#", 0)
        # offset:               0 2 . 6 . . . 14
        self.assertFalse(m.StartsWith("for"))
        self.assertTrue(m.StartsWith("#"))
        m.offset = 2
        self.assertTrue(m.StartsWith("for", whitespace=False))
        self.assertTrue(m.StartsWith("for", whitespace=True))
        m.offset = 6
        self.assertTrue(m.StartsWith("for", whitespace=False))
        self.assertFalse(m.StartsWith("for", whitespace=True))
        m.offset = 14
        self.assertTrue(m.StartsWith("!@#", whitespace=True))

#------------------------
# Local Variables:
# mode: python
# tab-width: 4
# py-continuation-offset: 4
# py-indent-offset: 4
# sentence-end-double-space: nil
# fill-column: 79
# End:
