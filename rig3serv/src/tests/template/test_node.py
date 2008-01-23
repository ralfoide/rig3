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
from rig.template.node import *
from rig.template.tag import Tag

#------------------------
class NodeTest(RigTestCase):

    def testEquality(self):
        self.assertEquals(NodeLiteral("abc"), NodeLiteral("abc"))

        content = NodeList()
        content.Append(NodeLiteral("abc"))
        content.Append(NodeLiteral("second"))
        
        self.assertEquals(content, NodeList([ NodeLiteral("abc"),
                                              NodeLiteral("second") ]))

        self.assertEquals(NodeTag(Tag("for", True), [ "param1", "param2" ], content),
                          NodeTag(Tag("for", True), [ "param1", "param2" ], content))


#------------------------
# Local Variables:
# mode: python
# tab-width: 4
# py-continuation-offset: 4
# py-indent-offset: 4
# sentence-end-double-space: nil
# fill-column: 79
# End:
