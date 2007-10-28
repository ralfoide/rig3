#!/usr/bin/python
#-----------------------------------------------------------------------------|
"""
Unit tests for IzuParser

Part of Rig3.
License GPL.
"""
__author__ = "ralfoide@gmail.com"

from StringIO import StringIO

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
        f = StringIO(text)
        html, tags, cats, images = self.m.RenderFileToHtml(f)
        f.close()
        self.assertEquals("<div class='izumi'>\n[izu-tag]\nLine 1\nLine 2\n\nLine 3</div>\n", html)


#------------------------
# Local Variables:
# mode: python
# tab-width: 4
# py-continuation-offset: 4
# py-indent-offset: 4
# sentence-end-double-space: nil
# fill-column: 79
# End:
