#!/usr/bin/python
#-----------------------------------------------------------------------------|
"""
Unit tests for SourceReader

Part of Rig3.
License GPL.
"""
__author__ = "ralfoide@gmail.com"

import os
from datetime import datetime

from tests.rig_test_case import RigTestCase
from rig.parser.dir_parser import RelDir
from rig.site_base import DEFAULT_THEME
from rig.sites_settings import SiteSettings
from rig.source_reader import SourceReaderBase, SourceDirReader
from rig.source_item import SourceDir

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
            [ ( RelDir(self.path, "2006-05_Movies"),
                RelDir(self._tempdir, "2006-05_Movies"),
                [ "index.html" ] ),
              ( RelDir(self.path, "2006-08-05 20.00.38  Progress"),
                RelDir(self._tempdir, "2006-08-05 20.00.38  Progress"),
                [ "index.html" ] ),
              ( RelDir(self.path, "2007-10-07 11.00_Folder 2"),
                RelDir(self._tempdir, "2007-10-07 11.00_Folder 2"),
                [ "index.izu"] ),
              ( RelDir(self.path, "2007-10-07_Folder 1"),
                RelDir(self._tempdir, "2007-10-07_Folder 1"),
                [ "T12896_tiny_jpeg.jpg", "index.izu" ] ),
             ],
            self.m.update_needed_requests)

        self.assertListEquals(
            [ SourceDir(datetime.fromtimestamp(2),
                        RelDir(self.path, "2006-05_Movies"),
                        [ "index.html" ] ), 
              SourceDir(datetime.fromtimestamp(3),
                        RelDir(self.path, "2006-08-05 20.00.38  Progress"),
                        [ "index.html" ] ), 
              SourceDir(datetime.fromtimestamp(4),
                        RelDir(self.path, "2007-10-07 11.00_Folder 2"),
                        [ "index.izu"] ), 
              SourceDir(datetime.fromtimestamp(5),
                        RelDir(self.path, "2007-10-07_Folder 1"),
                        [ "T12896_tiny_jpeg.jpg", "index.izu" ] ) ], 
            p)

#------------------------
# Local Variables:
# mode: python
# tab-width: 4
# py-continuation-offset: 4
# py-indent-offset: 4
# sentence-end-double-space: nil
# fill-column: 79
# End:
