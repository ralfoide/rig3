#!/usr/bin/python
#-----------------------------------------------------------------------------|
"""
Unit tests for Template

Part of Rig3.
License GPL.
"""
__author__ = "ralfoide@gmail.com"

import os

from tests.rig_test_case import RigTestCase
from rig.template import Template

class MockParse(Template):
    def __init__(self, log, file=None, source=None):
        self.source = None
        super(MockParse, self).__init__(log, file=file, source=source)
    
    def _Parse(self, source):
        self.source = source

#------------------------
class TemplateTest(RigTestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

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

        filename = os.path.join(self.getTestDataPath(), "simple.html")
        m = MockParse(self.Log(), file=filename, source=None)
        self.assertIsInstance(str, m.source)
        self.assertSearch("html", m.source)


#------------------------
# Local Variables:
# mode: python
# tab-width: 4
# py-continuation-offset: 4
# py-indent-offset: 4
# sentence-end-double-space: nil
# fill-column: 79
# End:
