#!/usr/bin/python
#-----------------------------------------------------------------------------|
"""
Unit tests for Kid

Part of Rig3.
License GPL.
"""
__author__ = "ralfoide@gmail.com"

import os

from tests.rig_test_case import RigTestCase
from rig.empty import Empty

#------------------------
class SimpleKidTest(RigTestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def testSimpleKidTemplate(self):
        """
        Test we can render something simple using the Kid templating system.
        
        If not present, get it here: http://www.kid-templating.org/
        """
        import kid
        filename = os.path.join(self.getTestDataPath(), "simple_kid.xml")
        keywords = { "foo": "MyFoo", "bar": "MyBar" }
        template = kid.Template(file=filename, **keywords)

        result = template.serialize()
        expected = """<?xml version="1.0" encoding="utf-8"?>
                      <html xmlns="http://www.w3.org/1999/xhtml">
                      <head>
                          <title>Test-Title</title>
                      </head>
                      <body>
                          Kid Test.
                          Title is Test-Title.
                          Title is <span>TEST-TITLE</span>.
                          <div>TEST-TITLE</div>.
                        
                          From caller: MyFoo, MyBar.
                      </body>
                      </html>"""
        self.assertHtmlEquals(expected, result)

        result = template.serialize(output="html")
        expected = """<!DOCTYPE [^>]+>
                      <html>
                      <head>
                          <meta [^>]+>
                          <title>Test-Title</title>
                      </head>
                      <body>
                          Kid Test.
                          Title is Test-Title.
                          Title is <span>TEST-TITLE</span>.
                          <div>TEST-TITLE</div>.
                        
                          From caller: MyFoo, MyBar.
                      </body>
                      </html>"""
        self.assertHtmlMatches(expected, result)


#------------------------
# Local Variables:
# mode: python
# tab-width: 4
# py-continuation-offset: 4
# py-indent-offset: 4
# sentence-end-double-space: nil
# fill-column: 79
# End:
