#!/usr/bin/python
#-----------------------------------------------------------------------------|
"""
Unit tests for SourceReader

Part of Rig3.
License GPL.
"""
__author__ = "ralfoide@gmail.com"

import os

from tests.rig_test_case import RigTestCase
from rig.parser.dir_parser import RelDir
from rig.site_base import DEFAULT_THEME
from rig.sites_settings import SiteSettings
from rig.source_reader import SourceReaderBase, SourceDirReader

#------------------------
class SourceReaderBaseTest(RigTestCase):

    def setUp(self):
        self._tempdir = self.MakeTempDir()
        path = os.path.join(self.getTestDataPath(), "album")
        self.m = SourceReaderBase(self.Log(), None, path)

    def tearDown(self):
        self.m = None

    def testParse(self):
        self.assertRaises(NotImplementedError, self.m.Parse, self._tempdir)

#------------------------
class MockSourceDirReader(SourceDirReader):
    def __init__(self, log, settings, path):
        super(MockSourceDirReader, self).__init__(log, settings, path)
        self.update_needed_requests = []
        self._dir_time_stamp = 1

    def _UpdateNeeded(self, source_dir, dest_dir, all_files):
        self.update_needed_requests.append( ( source_dir, dest_dir, all_files ) )
        return True

    def _DirTimeStamp(self, dir):
        self._dir_time_stamp += 1
        return self._dir_time_stamp
    

class SourceDirReaderTest(RigTestCase):
    
    def setUp(self):
        self._tempdir = self.MakeTempDir()
        self.path = os.path.join(self.getTestDataPath(), "album")
        source = SourceDirReader(self.Log(), None, self.path)
        self.s = SiteSettings(public_name="Test Album",
                              source_list=[ source ],
                              dest_dir=self._tempdir,
                              theme=DEFAULT_THEME,
                              base_url="http://www.example.com",
                              rig_url="http://example.com/photos/")
        self.m = MockSourceDirReader(self.Log(), self.s, self.path)

    def tearDown(self):
        self.m = None

    def testParse(self):
        p = self.m.Parse(self._tempdir)
        
        self.assertListEquals(
            [ ( RelDir(self.path, ""),
                RelDir(self._tempdir, ""),
                [] ),
              ( RelDir(self.path, "2006-05_Movies"),
                RelDir(self._tempdir, "2006-05_Movies"),
                [ "index.html" ] ),
              ( RelDir(self.path, "2006-08-05 20.00.38  Progress"),
                RelDir(self._tempdir, "2006-08-05 20.00.38  Progress"),
                [ "index.html" ] ),
              ( RelDir(self.path, "2007-10-07 11.00_Folder 2"),
                RelDir(self._tempdir, "2007-10-07 11.00_Folder 2"),
                [ "index.izu"]),
              ( RelDir(self.path, "2007-10-07_Folder 1"),
                RelDir(self._tempdir, "2007-10-07_Folder 1"),
                [ "T12896_tiny_jpeg.jpg", "index.izu" ] ),
             ],
            self.m.update_needed_requests)

#===============================================================================
#        self.assertIsInstance(DirParser, p)
#        self.assertListEquals([], p.Files())
#        self.assertEquals(4, len(p.SubDirs()))
#        self.assertIsInstance(DirParser, p.SubDirs()[0])
#        self.assertIsInstance(DirParser, p.SubDirs()[1])
#        self.assertIsInstance(DirParser, p.SubDirs()[2])
#        self.assertIsInstance(DirParser, p.SubDirs()[3])
#        self.assertEquals("2006-05_Movies", p.SubDirs()[0].AbsSourceDir().rel_curr)
#        self.assertEquals("2006-08-05 20.00.38  Progress", p.SubDirs()[1].AbsSourceDir().rel_curr)
#        self.assertEquals("2007-10-07 11.00_Folder 2", p.SubDirs()[2].AbsSourceDir().rel_curr)
#        self.assertEquals("2007-10-07_Folder 1", p.SubDirs()[3].AbsSourceDir().rel_curr)
#        self.assertListEquals([ "index.html"], p.SubDirs()[0].Files())
#        self.assertListEquals([ "index.html"], p.SubDirs()[1].Files())
#        self.assertListEquals([ "index.izu"], p.SubDirs()[2].Files())
#        self.assertListEquals([ "T12896_tiny_jpeg.jpg", "index.izu"], p.SubDirs()[3].Files())
#        self.assertListEquals([], p.SubDirs()[0].SubDirs())
#        self.assertListEquals([], p.SubDirs()[1].SubDirs())
#        self.assertListEquals([], p.SubDirs()[2].SubDirs())
#        self.assertListEquals([], p.SubDirs()[3].SubDirs())
#===============================================================================

#------------------------
# Local Variables:
# mode: python
# tab-width: 4
# py-continuation-offset: 4
# py-indent-offset: 4
# sentence-end-double-space: nil
# fill-column: 79
# End:
