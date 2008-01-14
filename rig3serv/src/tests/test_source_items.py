#!/usr/bin/python
#-----------------------------------------------------------------------------|
"""
Unit tests for SourceItem

Part of Rig3.
License GPL.
"""
__author__ = "ralfoide@gmail.com"

from datetime import datetime

from tests.rig_test_case import RigTestCase
from rig.source_item import SourceDir, SourceFile
from rig.parser.dir_parser import RelDir, RelFile

#------------------------
class SourceDirTest(RigTestCase):

    def testSourceDir(self):
        date = datetime.today()
        source_dir = RelDir("/tmp", "foo")
        all_files = [ "index.txt", "image.jpg" ]
        s = SourceDir(date, source_dir, all_files)
        self.assertNotEqual(None, s)
        self.assertSame(date, s.date)
        self.assertSame(source_dir, s.source_dir)
        self.assertSame(all_files, s.all_files)

#------------------------
class SourceFileTest(RigTestCase):

    def testSourceFile(self):
        date = datetime.today()
        source_file = RelFile("/tmp", "foo.txt")
        s = SourceFile(date, source_file)
        self.assertNotEqual(None, s)
        self.assertSame(date, s.date)
        self.assertSame(source_file, s.source_file)


#------------------------
# Local Variables:
# mode: python
# tab-width: 4
# py-continuation-offset: 4
# py-indent-offset: 4
# sentence-end-double-space: nil
# fill-column: 79
# End:
