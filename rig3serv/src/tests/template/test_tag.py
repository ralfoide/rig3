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

from tests.rig_test_case import RigTestCase
from rig.template.buffer import Buffer
from rig.template.tag import *
from rig.template.node import *

#------------------------
class TagTest(RigTestCase):

    def testTag(self):
        m = Tag("tag", has_content=False)
        self.assertEquals("tag", m.Tag())
        self.assertFalse(m.HasContent())

        m = Tag("tag", has_content=True)
        self.assertEquals("tag", m.Tag())
        self.assertTrue(m.HasContent())
        self.assertRaises(NotImplementedError, m.Generate, self.Log(), None, None)

    def testTagComment(self):
        m = TagComment()
        self.assertEquals("#", m.Tag())
        self.assertFalse(m.HasContent())
        n = NodeTag(m, "ignored params", content=None)
        self.assertEquals("", m.Generate(self.Log(), n, context={}))

    def testTagRaw(self):
        m = TagRaw()
        self.assertEquals("raw", m.Tag())
        self.assertFalse(m.HasContent())

        n = NodeTag(m, "a+1", content=None)
        self.assertEquals("43", m.Generate(self.Log(), n, { "a": 42 }))

        n = NodeTag(m, "a==1", content=None)
        self.assertEquals("False", m.Generate(self.Log(), n, { "a": 42 }))

        n = NodeTag(m, "s", content=None)
        self.assertEquals("some string", m.Generate(self.Log(), n, { "a": 42, "s": "some string" }))

        d = { "a": 42 }
        n = NodeTag(m, "d['a']+1", content=None)
        self.assertEquals("43", m.Generate(self.Log(), n, { "d": d }))

    def testTagHtml(self):
        m = TagHtml()
        self.assertEquals("html", m.Tag())
        self.assertFalse(m.HasContent())

        n = NodeTag(m, "s", content=None)
        self.assertEquals("some string", m.Generate(self.Log(), n, { "s": "some string" }))
        self.assertEquals("`~!@#$%^&amp;*()-=_+[]{};:'\",./&lt;&gt;?",
                          m.Generate(self.Log(), n, { "s": "`~!@#$%^&*()-=_+[]{};:'\",./<>?" }))
        self.assertEquals('&lt;script&gt;&lt;img url="foo?a=1&amp;b=2"/&gt;&lt;/script&gt;',
                          m.Generate(self.Log(), n, { "s": '<script><img url="foo?a=1&b=2"/></script>' }))

    def testTagUrl(self):
        m = TagUrl()
        self.assertEquals("url", m.Tag())
        self.assertFalse(m.HasContent())

        n = NodeTag(m, "s", content=None)
        self.assertEquals("some-string",   m.Generate(self.Log(), n, { "s": "some-string" }))
        self.assertEquals("some%20string", m.Generate(self.Log(), n, { "s": "some string" }))
        self.assertEquals("local#anchor",  m.Generate(self.Log(), n, { "s": "local#anchor" }))
        self.assertEquals("http://example.com:8888",
                          m.Generate(self.Log(), n, { "s": "http://example.com:8888" }))
        self.assertEquals("http://example.com/path/1",
                          m.Generate(self.Log(), n, { "s": "http://example.com/path/1" }))
        self.assertEquals("http://example.com/path/1#anchor",
                          m.Generate(self.Log(), n, { "s": "http://example.com/path/1#anchor" }))
        self.assertEquals("https://user%20name:pass@ex%3Fample.com:80/cgi%3Fa%3D1%26b%3D2",
                          m.Generate(self.Log(), n, { "s": "https://user name:pass@ex?ample.com:80/cgi?a=1&b=2" }))

    def testTagIf(self):
        m = TagIf()
        self.assertEquals("if", m.Tag())
        self.assertTrue(m.HasContent())

        n = NodeList([ NodeLiteral("some content") ])
        n = NodeTag(m, "a==1", content=n)
        self.assertEquals("", m.Generate(self.Log(), n, { "a": 42 }))
        self.assertEquals("some content", m.Generate(self.Log(), n, { "a": 1 }))

    def testTagFor(self):
        m = TagFor()
        self.assertEquals("for", m.Tag())
        self.assertTrue(m.HasContent())

        n = NodeList([ NodeLiteral("some content") ])
        n = NodeTag(m, "v in a", content=n)
        self.assertEquals("some contentsome contentsome content",
                          m.Generate(self.Log(), n, { "a": [ 42, 43, 44 ] }))

        n = NodeList([ NodeLiteral("value is "),
                       NodeTag(TagRaw(), "'%03d ' % v", content=None) ])
        n = NodeTag(m, "v in a", content=n)
        self.assertEquals("value is 042 value is 043 value is 044 ",
                          m.Generate(self.Log(), n, { "a": [ 42, 43, 44 ] }))

    def testTagInsert(self):
        m = TagInsert()
        self.assertEquals("insert", m.Tag())
        self.assertFalse(m.HasContent())

        # insert with an empty expression does nothing
        n = NodeTag(m, "mypath", content=None)
        self.assertEquals("", m.Generate(self.Log(), n, { "mypath": "" }))
        self.assertEquals("", m.Generate(self.Log(), n, { "mypath": None }))

        alt_header = os.path.join(self.getTestDataPath(), "templates", "default", "alt_header.html")
        self.assertHtmlEquals(" Name is My Name Title is My Title ",
                              m.Generate(self.Log(), n, { "mypath": alt_header, "public_name": "My Name", "title": "My Title" }))


#------------------------
# Local Variables:
# mode: python
# tab-width: 4
# py-continuation-offset: 4
# py-indent-offset: 4
# sentence-end-double-space: nil
# fill-column: 79
# End:
