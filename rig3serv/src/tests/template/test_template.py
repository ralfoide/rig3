#!/usr/bin/python
#-----------------------------------------------------------------------------|
"""
Unit tests for Template

Part of Rig3.
Copyright (C) 2007-2009 ralfoide gmail com

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""
__author__ = "ralfoide at gmail com"

import os
import StringIO

from tests.rig_test_case import RigTestCase
from rig.template.template import Template, _TagEnd
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
class _TagTag(Tag):
    def __init__(self):
        super(_TagTag, self).__init__(tag="tag", has_content=False)

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
        self.assertEquals("<source>", m.filename)

        filename = os.path.join(self.getTestDataPath(), "simple.html")
        m = MockParse(self.Log(), file=filename, source=None)
        self.assertIsInstance(str, m.source)
        self.assertSearch("html", m.source)
        self.assertEquals(filename, m.filename)

        buf = StringIO.StringIO("template from StringIO")
        m = MockParse(self.Log(), file=buf, source=None)
        self.assertEquals("template from StringIO", m.source)
        self.assertEquals("<file>", m.filename)

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

    def testGetNextNode_Escape(self):
        m = MockParse(self.Log(), source="")

        # [[raw expr]] is escaped with an extra [, so it transformed into a
        # literal rather than a tag.
        b = Buffer("file", "[[[raw expr]]")
        self.assertEquals(NodeLiteral("[[raw expr]]"), m._GetNextNode(b))

        # We can have as many levels of [[[[, only N-1 are generated in output.
        # However the [[[... part still generates its own literal.
        b = Buffer("file", "some [[[[[[blah foo bar]] thing")
        self.assertEquals(NodeLiteral("some "), m._GetNextNode(b))
        self.assertEquals(NodeLiteral("[[[[[blah foo bar]] thing"), m._GetNextNode(b))

        # Since the escaped tag is a literal, it doesn't have to be closed properly
        b = Buffer("file", "[[[[tag")
        self.assertEquals(NodeLiteral("[[[tag"), m._GetNextNode(b))

    def testGetNextNode_Tags(self):
        m = MockParse(self.Log(), source="")
        t = m._tags["tag"] = _TagTag()
        b = Buffer("file", "[[tag\r\n  param1 \t\t\r\n param2  \f\f \r\n]]", linesep="\r\n")
        self.assertEquals(NodeTag(t,  "param1 \t\t\r\n param2", content=None),
                          m._GetNextNode(b))

        b = Buffer("file", "word 1 [[tag 1]]  word 2  [[ tag  2  ]] word 3[[  end  ]]word 4   ")
        self.assertEquals(NodeLiteral("word 1 "), m._GetNextNode(b))
        self.assertEquals(NodeTag(t, "1", content=None), m._GetNextNode(b))
        self.assertEquals(NodeLiteral("  word 2  "), m._GetNextNode(b))
        self.assertEquals(NodeTag(t, "2", content=None), m._GetNextNode(b))
        self.assertEquals(NodeLiteral(" word 3"), m._GetNextNode(b))
        self.assertEquals(NodeTag(_TagEnd(), "", content=None), m._GetNextNode(b))
        self.assertEquals(NodeLiteral("word 4   "), m._GetNextNode(b))
        self.assertTrue(b.EndReached())

    def testGetNextNode_Expression(self):
        m = MockParse(self.Log(), source="")
        b = Buffer("file", "[[raw expr]]")
        self.assertEquals(NodeTag(TagRaw(), parameters="expr", content=None),
                          m._GetNextNode(b))
        self.assertTrue(b.EndReached())

        # When parsing an expression, we preserve *all* whitespace after the
        # beginning of the expression
        b = Buffer("file", "[[ html  a+2  ]]")
        self.assertEquals(NodeTag(TagHtml(), parameters="a+2", content=None),
                          m._GetNextNode(b))
        self.assertTrue(b.EndReached())

        b = Buffer("file", "[[   url    a + 2  ]]")
        self.assertEquals(NodeTag(TagUrl(), parameters="a + 2", content=None),
                          m._GetNextNode(b))
        self.assertTrue(b.EndReached())

        b = Buffer("file", "[[raw '  a' + '2  ']]")
        self.assertEquals(NodeTag(TagRaw(), parameters="'  a' + '2  '", content=None),
                          m._GetNextNode(b))
        self.assertTrue(b.EndReached())


#------------------------
# Local Variables:
# mode: python
# tab-width: 4
# py-continuation-offset: 4
# py-indent-offset: 4
# sentence-end-double-space: nil
# fill-column: 79
# End:
