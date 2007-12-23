#!/usr/bin/python
#-----------------------------------------------------------------------------|
"""
Unit tests for SourceReader

Part of Rig3.
License GPL.
"""
__author__ = "ralfoide@gmail.com"

from tests.rig_test_case import RigTestCase
from rig.source_reader import SourceReader

#------------------------
class SourceReaderBaseTest(RigTestCase):

    def setUp(self):
        self.m = SourceReader(self.Log())

    def tearDown(self):
        self.m = None

    def testInit(self):
        """
        Test init of SourceReader
        """
        self.assertNotEqual(None, self.m)

class SourceDirReaderTest(RigTestCase):
    
    def setUp(self):
        self._tempdir = self.MakeTempDir()
        path = os.path.join(self.getTestDataPath(), "album")
        self.m = SourceDirReader(self.Log(), settings, path)

    def tearDown(self):
        self.m = None

    def testParse(self):
        m = MockSiteBase(self, self.Log(), False, self.s)
        p = m._Parse(m._settings.source_dir, m._settings.dest_dir)
        self.assertIsInstance(DirParser, p)
        self.assertListEquals([], p.Files())
        self.assertEquals(4, len(p.SubDirs()))
        self.assertIsInstance(DirParser, p.SubDirs()[0])
        self.assertIsInstance(DirParser, p.SubDirs()[1])
        self.assertIsInstance(DirParser, p.SubDirs()[2])
        self.assertIsInstance(DirParser, p.SubDirs()[3])
        self.assertEquals("2006-05_Movies", p.SubDirs()[0].AbsSourceDir().rel_curr)
        self.assertEquals("2006-08-05 20.00.38  Progress", p.SubDirs()[1].AbsSourceDir().rel_curr)
        self.assertEquals("2007-10-07 11.00_Folder 2", p.SubDirs()[2].AbsSourceDir().rel_curr)
        self.assertEquals("2007-10-07_Folder 1", p.SubDirs()[3].AbsSourceDir().rel_curr)
        self.assertListEquals([ "index.html"], p.SubDirs()[0].Files())
        self.assertListEquals([ "index.html"], p.SubDirs()[1].Files())
        self.assertListEquals([ "index.izu"], p.SubDirs()[2].Files())
        self.assertListEquals([ "T12896_tiny_jpeg.jpg", "index.izu"], p.SubDirs()[3].Files())
        self.assertListEquals([], p.SubDirs()[0].SubDirs())
        self.assertListEquals([], p.SubDirs()[1].SubDirs())
        self.assertListEquals([], p.SubDirs()[2].SubDirs())
        self.assertListEquals([], p.SubDirs()[3].SubDirs())

#------------------------
# Local Variables:
# mode: python
# tab-width: 4
# py-continuation-offset: 4
# py-indent-offset: 4
# sentence-end-double-space: nil
# fill-column: 79
# End:
