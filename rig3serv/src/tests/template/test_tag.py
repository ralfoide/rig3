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

    def testTagExpression(self):
        m = TagExpression()
        self.assertEquals(None, m.Tag())
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

    def testTagIf(self):
        m = TagIf()
        self.assertEquals("if", m.Tag())
        self.assertTrue(m.HasContent())

        n = NodeTag(m, "a==1", content=NodeList().Append(NodeLiteral("some content")))
        self.assertEquals("", m.Generate(n, { "a": 42 }))
        self.assertEquals("some content", m.Generate(n, { "a": 1 }))
    
    def testTagFor(self):
        m = TagFor()
        self.assertEquals("for", m.Tag())
        self.assertTrue(m.HasContent())

#------------------------
# Local Variables:
# mode: python
# tab-width: 4
# py-continuation-offset: 4
# py-indent-offset: 4
# sentence-end-double-space: nil
# fill-column: 79
# End:
