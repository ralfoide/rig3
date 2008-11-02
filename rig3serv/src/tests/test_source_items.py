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
from rig.source_item import SourceDir, SourceFile, SourceSettings
from rig.parser.dir_parser import RelDir, RelFile

#------------------------
class SourceDirTest(RigTestCase):

    def testSourceDir(self):
        date = datetime.today()
        rel_dir = RelDir("/tmp", "foo")
        all_files = [ "index.txt", "image.jpg" ]
        s = SourceDir(date, rel_dir, all_files)
        self.assertNotEquals(None, s)
        self.assertSame(date, s.date)
        self.assertSame(rel_dir, s.rel_dir)
        self.assertSame(all_files, s.all_files)

    def testEqAndHash(self):
        date1 = datetime.today()
        s1 = SourceDir(date1, RelFile("/tmp", "foo.txt"), ["file1", "file2"])
        s2 = SourceDir(date1, RelFile("/tmp", "foo.txt"), ["file1", "file2"])

        # 2 equal but different objects
        self.assertNotSame(s1, s2)
        self.assertEquals(s1, s2)
        self.assertEquals(hash(s1), hash(s2))

        # with same path but a different date
        date2 = datetime.fromtimestamp(1) # e.g. 'Wed Dec 31 16:00:01 1969'
        s2 = SourceDir(date2, RelFile("/tmp", "foo.txt"), ["file1", "file2"])
        self.assertNotEquals(s1, s2)
        self.assertNotEquals(hash(s1), hash(s2))

        # with same date but different path
        s2 = SourceDir(date1, RelFile("/tmp", "blah.txt"), ["file1", "file2"])
        self.assertNotEquals(s1, s2)
        self.assertNotEquals(hash(s1), hash(s2))

        # with different all-files list
        s2 = SourceDir(date1, RelFile("/tmp", "foo.txt"), ["abc", "def", "123"])
        self.assertNotEquals(s1, s2)
        self.assertNotEquals(hash(s1), hash(s2))

        # same date/path but different source settings
        s2 = SourceDir(date1, RelFile("/tmp", "foo.txt"), ["file1", "file2"],
                        source_settings=SourceSettings(rig_base="/rig/base"))
        self.assertNotEquals(s1, s2)
        self.assertNotEquals(hash(s1), hash(s2))

        # and different categories
        s2 = SourceDir(date1, RelFile("/tmp", "foo.txt"), ["file1", "file2"])
        self.assertEquals(s1, s2)
        self.assertEquals(hash(s1), hash(s2))
        s2.categories = ["foo", "bar"]
        self.assertNotEquals(s1, s2)
        self.assertNotEquals(hash(s1), hash(s2))

#------------------------
class SourceFileTest(RigTestCase):

    def testSourceFile(self):
        date = datetime.today()
        rel_file = RelFile("/tmp", "foo.txt")
        s = SourceFile(date, rel_file)
        self.assertNotEquals(None, s)
        self.assertSame(date, s.date)
        self.assertSame(rel_file, s.rel_file)

    def testEqAndHash(self):
        date1 = datetime.today()
        s1 = SourceFile(date1, RelFile("/tmp", "foo.txt"))
        s2 = SourceFile(date1, RelFile("/tmp", "foo.txt"))

        # 2 equal but different objects
        self.assertNotSame(s1, s2)
        self.assertEquals(s1, s2)
        self.assertEquals(hash(s1), hash(s2))

        # with same path but a different date
        date2 = datetime.fromtimestamp(1) # e.g. 'Wed Dec 31 16:00:01 1969'
        s2 = SourceFile(date2, RelFile("/tmp", "foo.txt"))
        self.assertNotEquals(s1, s2)
        self.assertNotEquals(hash(s1), hash(s2))

        # with same date but different path
        s2 = SourceFile(date1, RelFile("/tmp", "blah.txt"))
        self.assertNotEquals(s1, s2)
        self.assertNotEquals(hash(s1), hash(s2))

        # same date/path but different source settings
        s2 = SourceFile(date1, RelFile("/tmp", "foo.txt"),
                        source_settings=SourceSettings(rig_base="/rig/base"))
        self.assertNotEquals(s1, s2)
        self.assertNotEquals(hash(s1), hash(s2))

        # and different categories
        s2 = SourceFile(date1, RelFile("/tmp", "foo.txt"))
        self.assertEquals(s1, s2)
        self.assertEquals(hash(s1), hash(s2))
        s2.categories = ["foo", "bar"]
        self.assertNotEquals(s1, s2)
        self.assertNotEquals(hash(s1), hash(s2))
        
        

#------------------------
# Local Variables:
# mode: python
# tab-width: 4
# py-continuation-offset: 4
# py-indent-offset: 4
# sentence-end-double-space: nil
# fill-column: 79
# End:
