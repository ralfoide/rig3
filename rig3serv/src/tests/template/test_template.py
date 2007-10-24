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
from rig.template.template import Template
from rig.template.buffer import Buffer
from rig.template.node import *
from rig.template.tag import *

#------------------------
class MockParse(Template):
    """
    A mock Template that overrides the _Parse method just to check if the
    constructor calls it adequately.
    """
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
        m = MockParse(self.Log(), file=None, source="something")
        self.assertSame(self.Log(), m._log)
        self.assertIsInstance(dict, m._tags)
        self.assertIsInstance(dict, m._filters)

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

    def testTags(self):
        m = MockParse(self.Log(), file=None, source="something")
        self.assertIsInstance(dict, m._tags)
        self.assertTrue("#" in m._tags, "Missing key '#' in %s" % m._tags)
        self.assertTrue("end" in m._tags, "Missing key 'end' in %s" % m._tags)
        self.assertTrue("for" in m._tags, "Missing key 'for' in %s" % m._tags)
        self.assertTrue("if" in m._tags, "Missing key 'if' in %s" % m._tags)
        self.assertIsInstance(TagComment, m._tags["#"])
        self.assertIsInstance(TagFor, m._tags["for"])
        self.assertIsInstance(TagIf, m._tags["if"])
        self.assertIsInstance(Tag, m._tags["end"])

    def testGetNextNode(self):
        m = MockParse(self.Log(), source="")
        b = Buffer("file", "literal string")
        self.assertEquals(NodeLiteral("literal string"), m._GetNextNode(b))

        b = Buffer("file", "[[tag")
        self.assertRaises(SyntaxError, m._GetNextNode, b)
        
        b = Buffer("file", "[[tag\r\n  param1 \t\t\f\r\n param2  \f\f \r\n]]")
        m._tags["tag"] = Tag(tag=None, has_content=False)
        self.assertEquals(NodeTag("tag", None, [ "param1", "param2" ], content=None),
                          m._GetNextNode(b))


#------------------------
# Local Variables:
# mode: python
# tab-width: 4
# py-continuation-offset: 4
# py-indent-offset: 4
# sentence-end-double-space: nil
# fill-column: 79
# End:
