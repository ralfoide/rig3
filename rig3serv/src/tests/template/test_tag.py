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

#------------------------
class TagTest(RigTestCase):

    def testTag(self):
        m = Tag("tag", has_content=False)
        self.assertEquals("tag", m.tag)
        self.assertFalse(m.has_content)

        m = Tag("tag", has_content=True)
        self.assertEquals("tag", m.tag)
        self.assertTrue(m.has_content)
        self.assertRaises(NotImplementedError, m.Generate, None, None)
    
    def testTagComment(self):
        m = TagComment()
        self.assertEquals("#", m.tag)
        self.assertFalse(m.has_content)
        self.assertEquals("", m.Generate(tag_node=None, context=None))

    def testTagIf(self):
        m = TagIf()
        self.assertEquals("if", m.tag)
        self.assertTrue(m.has_content)
    
    def testTagFor(self):
        m = TagFor()
        self.assertEquals("for", m.tag)
        self.assertTrue(m.has_content)

#------------------------
# Local Variables:
# mode: python
# tab-width: 4
# py-continuation-offset: 4
# py-indent-offset: 4
# sentence-end-double-space: nil
# fill-column: 79
# End:
