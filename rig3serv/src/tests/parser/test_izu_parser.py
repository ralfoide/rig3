#!/usr/bin/python
#-----------------------------------------------------------------------------|
"""
Unit tests for IzuParser

Part of Rig3.
License GPL.
"""
__author__ = "ralfoide@gmail.com"

from tests.rig_test_case import RigTestCase
from rig.parser.izu_parser import IzuParser

#------------------------
class IzuParserTest(RigTestCase):

    def setUp(self):
        self.m = IzuParser(self.Log())

    def tearDown(self):
        self.m = None

    def testSimpleParse(self):
        """
        Naive very simple test
        """
        self.assertNotEqual(None, self.m)
        
        text = "[izu-tag]\nLine 1\nLine 2\n\nLine 3"
        tags, sections = self.m.RenderStringToHtml(text)
        html = sections.get("en", "")
        self.assertEquals('<div class="izu">[izu-tag]\nLine 1\nLine 2<p>Line 3</div>', html)


#------------------------
# Local Variables:
# mode: python
# tab-width: 4
# py-continuation-offset: 4
# py-indent-offset: 4
# sentence-end-double-space: nil
# fill-column: 79
# End:
