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
from rig.template import Template, Buffer, NodeLiteral, NodeTag, NodeList, NodeVariable

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

    def testGetNextNode(self):
        m = MockParse(self.Log(), source="")
        b = Buffer("file", "literal string")
        self.assertEquals(NodeLiteral("literal string"), m._GetNextNode(b))

        b = Buffer("file", "[[tag")
        self.assertRaises(SyntaxError, m._GetNextNode, b)
        
        b = Buffer("file", "[[tag\r\n  param1 \t\t\f\r\n param2  \f\f \r\n]]")
        self.assertEquals(NodeTag("tag", [ "param1", "param2" ], content=None),
                          m._GetNextNode(b))


#------------------------
class BufferTest(RigTestCase):

    def testInit(self):
        m = Buffer("filename", "data", 42)
        self.assertEquals("filename", m.filename)
        self.assertEquals("data", m.data)
        self.assertEquals(42, m.offset)
        self.assertEquals(1, m.lineno)

    def testConvertLineSep(self):
        # Requires offset=0 before converting lines as such a conversion would invalidate
        # the offset (no attemp is made to convert it too)
        m = Buffer("filename", "data", 42)
        self.assertRaises(RuntimeError, m.ConvertLineSep)

        m = Buffer("filename", "data", 0)
        self.assertSame(m, m.ConvertLineSep())
        self.assertEquals("data", m.data)
        self.assertEquals(0, m.offset)

        m = Buffer("filename", "AAA\r\nBBB\r\n\r\nCCC", linesep="\n")
        m.ConvertLineSep()
        self.assertEquals("AAA\nBBB\n\nCCC", m.data)

        m = Buffer("filename", "AAA\r\nBBB\r\n\r\nCCC", linesep="\r\n")
        m.ConvertLineSep()
        self.assertEquals("AAA\r\nBBB\r\n\r\nCCC", m.data)

        m = Buffer("filename", "AAA\rBBB\r\rCCC", linesep="\r\n")
        m.ConvertLineSep()
        self.assertEquals("AAA\r\nBBB\r\n\r\nCCC", m.data)

    def testEndReached(self):
        m = Buffer("filename", "data")
        self.assertFalse(m.EndReached())
        m.offset = 3
        self.assertFalse(m.EndReached())
        m.offset = 4
        self.assertTrue(m.EndReached())

    def testStartsWith(self):
        m = Buffer("filename", "# for foreach !@#")
        # offset:               0 2 . 6 . . . 14
        self.assertFalse(m.StartsWith(""))
        self.assertFalse(m.StartsWith("for"))
        self.assertTrue(m.StartsWith("#"))
        self.assertEquals(0, m.offset)

        self.assertTrue(m.StartsWith("#", consume=True))
        self.assertEquals(1, m.offset)
        m.offset = 0
        self.assertTrue(m.StartsWith("#", whitespace=True, consume=True))
        self.assertEquals(2, m.offset)

        self.assertTrue(m.StartsWith("for", whitespace=False))
        self.assertTrue(m.StartsWith("for", whitespace=True))
        self.assertEquals(2, m.offset)
        self.assertTrue(m.StartsWith("for", whitespace=True, consume=True))
        self.assertEquals(6, m.offset)

        self.assertTrue(m.StartsWith("for", whitespace=False))
        self.assertFalse(m.StartsWith("for", whitespace=True, consume=True))
        self.assertEquals(6, m.offset)

        m.offset = 14
        self.assertTrue(m.StartsWith("!@#", whitespace=True, consume=True))
        self.assertTrue(m.EndReached())

    def testSkipTo(self):
        m = Buffer("filename", "some string")
        # offset:               0 2 .5. 8 10
        self.assertEquals("", m.SkipTo(""))
        self.assertEquals("some ", m.SkipTo("st"))
        self.assertEquals(5, m.offset)

        # "st" is still at the current's buffer pos. This is a nop.
        self.assertEquals("", m.SkipTo("st"))
        self.assertEquals(5, m.offset)

        # try again, past the "st" pattern
        m.offset += 1
        self.assertEquals("tring", m.SkipTo("st"))
        self.assertTrue(m.EndReached())

        m = Buffer("filename", "1\n2\n3\n\n5\n6", linesep="\n")
        self.assertEquals(1, m.lineno)
        self.assertEquals("1\n", m.SkipTo("2"))
        self.assertEquals(2, m.lineno)
        self.assertEquals("2\n3\n\n", m.SkipTo("5"))
        self.assertEquals(5, m.lineno)
        self.assertEquals("5\n", m.SkipTo("6"))
        self.assertEquals(6, m.lineno)
        self.assertEquals("", m.SkipTo("6"))
        self.assertEquals(6, m.lineno)

    def testNextWord(self):
        m = Buffer("filename", "some string")
        self.assertEquals("some", m.NextWord())
        self.assertEquals("string", m.NextWord())
        self.assertTrue(m.EndReached())
        self.assertEquals("", m.NextWord())
        self.assertTrue(m.EndReached())

        m = Buffer("filename", "\n\nsome\n \nstring\n\n", linesep="\n")
        self.assertEquals(1, m.lineno)
        self.assertEquals("some", m.NextWord())
        self.assertEquals(3, m.lineno)
        self.assertEquals("string", m.NextWord())
        self.assertEquals(5, m.lineno)
        self.assertFalse(m.EndReached())  # end line seps are not parsed yet
        self.assertEquals("", m.NextWord())
        self.assertEquals(7, m.lineno)
        self.assertTrue(m.EndReached())

        m = Buffer("filename", "\r\nsome \r\nstring\r\n", linesep="\r\n")
        self.assertEquals(1, m.lineno)
        self.assertEquals("some", m.NextWord())
        self.assertEquals(2, m.lineno)
        self.assertEquals("string", m.NextWord())
        self.assertEquals(3, m.lineno)
        self.assertFalse(m.EndReached())  # end line seps are not parsed yet
        self.assertEquals("", m.NextWord())
        self.assertEquals(4, m.lineno)
        self.assertTrue(m.EndReached())


#------------------------
class NodeTest(RigTestCase):

    def testEquality(self):
        self.assertEquals(NodeLiteral("abc"), NodeLiteral("abc"))

        content = NodeList()
        content.Append(NodeLiteral("abc"))
        content.Append(NodeLiteral("second"))
        
        self.assertEquals(content, NodeList([ NodeLiteral("abc"),
                                              NodeLiteral("second") ]))

        self.assertEquals(NodeTag("for", [ "param1", "param2" ], content),
                          NodeTag("for", [ "param1", "param2" ], content))

        self.assertEquals(NodeVariable([ "var", "prop", "prop2" ],
                                       [ "raw", "html" ]),
                          NodeVariable([ "var", "prop", "prop2" ], 
                                       [ "raw", "html" ]))


#------------------------
# Local Variables:
# mode: python
# tab-width: 4
# py-continuation-offset: 4
# py-indent-offset: 4
# sentence-end-double-space: nil
# fill-column: 79
# End:
