#!/usr/bin/python
#-----------------------------------------------------------------------------|
"""
Unit tests for Template

Part of Rig3.
License GPL.
"""
__author__ = "ralfoide@gmail.com"


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
        self.assertRaises(NotImplementedError, m.Generate, None, None)
    
    def testTagComment(self):
        m = TagComment()
        self.assertEquals("#", m.Tag())
        self.assertFalse(m.HasContent())
        n = NodeTag(m, "ignored params", content=None)
        self.assertEquals("", m.Generate(n, context={}))

    def testTagRaw(self):
        m = TagRaw()
        self.assertEquals("raw", m.Tag())
        self.assertFalse(m.HasContent())
        
        n = NodeTag(m, "a+1", content=None)
        self.assertEquals("43", m.Generate(n, { "a": 42 }))

        n = NodeTag(m, "a==1", content=None)
        self.assertEquals("False", m.Generate(n, { "a": 42 }))

        n = NodeTag(m, "s", content=None)
        self.assertEquals("some string", m.Generate(n, { "a": 42, "s": "some string" }))

        d = { "a": 42 }
        n = NodeTag(m, "d['a']+1", content=None)
        self.assertEquals("43", m.Generate(n, { "d": d }))

    def testTagHtml(self):
        m = TagHtml()
        self.assertEquals("html", m.Tag())
        self.assertFalse(m.HasContent())

        n = NodeTag(m, "s", content=None)
        self.assertEquals("some string", m.Generate(n, { "s": "some string" }))
        self.assertEquals("`~!@#$%^&amp;*()-=_+[]{};:'\",./&lt;&gt;?",
                          m.Generate(n, { "s": "`~!@#$%^&*()-=_+[]{};:'\",./<>?" }))
        self.assertEquals('&lt;script&gt;&lt;img url="foo?a=1&amp;b=2"/&gt;&lt;/script&gt;',
                          m.Generate(n, { "s": '<script><img url="foo?a=1&b=2"/></script>' }))

    def testTagUrl(self):
        m = TagUrl()
        self.assertEquals("url", m.Tag())
        self.assertFalse(m.HasContent())

        n = NodeTag(m, "s", content=None)
        self.assertEquals("some-string", m.Generate(n, { "s": "some-string" }))
        self.assertEquals("some%20string", m.Generate(n, { "s": "some string" }))
        self.assertEquals("http://alfray.com/path/1",
                          m.Generate(n, { "s": "http://alfray.com/path/1" }))
        self.assertEquals("https://ralf%20oide:pass@alf%3Fray.com:80/cgi%3Fa%3D1%26b%3D2",
                          m.Generate(n, { "s": "https://ralf oide:pass@alf?ray.com:80/cgi?a=1&b=2" }))

    def testTagIf(self):
        m = TagIf()
        self.assertEquals("if", m.Tag())
        self.assertTrue(m.HasContent())

        n = NodeList([ NodeLiteral("some content") ])
        n = NodeTag(m, "a==1", content=n)
        self.assertEquals("", m.Generate(n, { "a": 42 }))
        self.assertEquals("some content", m.Generate(n, { "a": 1 }))
    
    def testTagFor(self):
        m = TagFor()
        self.assertEquals("for", m.Tag())
        self.assertTrue(m.HasContent())

        n = NodeList([ NodeLiteral("some content") ])
        n = NodeTag(m, "v in a", content=n)
        self.assertEquals("some contentsome contentsome content",
                          m.Generate(n, { "a": [ 42, 43, 44 ] }))

        n = NodeList([ NodeLiteral("value is "),
                       NodeTag(TagRaw(), "'%03d ' % v", content=None) ])
        n = NodeTag(m, "v in a", content=n)
        self.assertEquals("value is 042 value is 043 value is 044 ",
                          m.Generate(n, { "a": [ 42, 43, 44 ] }))

#------------------------
# Local Variables:
# mode: python
# tab-width: 4
# py-continuation-offset: 4
# py-indent-offset: 4
# sentence-end-double-space: nil
# fill-column: 79
# End:
