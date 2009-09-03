#!/usr/bin/python
#-----------------------------------------------------------------------------|
"""
Unit tests for SourceReader

Part of Rig3.
Copyright (C) 2007-2009 ralfoide gmail com

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""
__author__ = "ralfoide at gmail com"

import os
from datetime import datetime

from tests.rig_test_case import RigTestCase
from rig.parser.dir_parser import RelDir, RelFile
from rig.site_base import DEFAULT_THEME
from rig.sites_settings import SiteSettings
from rig.source_reader import SourceReaderBase, SourceDirReader, SourceFileReader, SourceBlogReader
from rig.source_item import SourceDir, SourceFile, SourceSettings

#------------------------
class SourceReaderBaseTest(RigTestCase):

    def setUp(self):
        self._tempdir = self.MakeTempDir()
        path = os.path.join(self.getTestDataPath(), "album")
        self.m = SourceReaderBase(self.Log(),
                                  site_settings=None,
                                  source_settings=None,
                                  path=path)

    def tearDown(self):
        self.m = None
        self.RemoveDir(self._tempdir)

    def testParse(self):
        self.assertRaises(NotImplementedError, self.m.Parse, self._tempdir)


#------------------------
class MockSourceBlogReader(SourceBlogReader):
    def __init__(self, log, settings, source_settings, path):
        super(MockSourceBlogReader, self).__init__(log, settings, source_settings, path)
        self._dir_time_stamp = 0
        self._file_time_stamp = 0

    def _DirTimeStamp(self, dir):
        self._dir_time_stamp += 1
        return self._dir_time_stamp

    def _FileTimeStamp(self, file):
        self._file_time_stamp += 1
        return self._file_time_stamp


class SourceBlogReaderTest(RigTestCase):

    def setUp(self):
        self._tempdir = self.MakeTempDir()
        self._cachedir = self.MakeTempDir()
        self.path1 = os.path.join(self.getTestDataPath(), "album", "blog1")
        self.path2 = os.path.join(self.getTestDataPath(), "album", "blog2")
        source1 = SourceBlogReader(self.Log(), None, None, self.path1)
        source2 = SourceBlogReader(self.Log(), None, None, self.path2)
        self.sis = SiteSettings(public_name="Test Album",
                                source_list=[ source1, source2 ],
                                dest_dir=self._tempdir,
                                cache_dir=self._cachedir,
                                theme=DEFAULT_THEME,
                                base_url="http://www.example.com")
        self.sos = SourceSettings(rig_base="http://example.com/photos/")
        self.m1 = MockSourceBlogReader(self.Log(), self.sis, self.sos, self.path1)
        self.m2 = MockSourceBlogReader(self.Log(), self.sis, self.sos, self.path2)

    def tearDown(self):
        self.m1 = None
        self.m2 = None
        self.RemoveDir(self._tempdir)
        self.RemoveDir(self._cachedir)

    def testParse(self):
        p1 = self.m1.Parse(self._tempdir)
        p2 = self.m2.Parse(self._tempdir)

        self.assertListEquals(
            [ SourceDir(datetime.fromtimestamp(1),
                        RelDir(self.path1, "2007-10-07_Folder 1"),
                        [ "T12896_tiny_jpeg.jpg", "index.izu" ],
                        self.sos ),
              SourceFile(datetime.fromtimestamp(1),
                         RelFile(self.path1, os.path.join("file_items", "2007-09-09 Izu File Item.izu")),
                         self.sos),
              SourceFile(datetime.fromtimestamp(2),
                         RelFile(self.path1, os.path.join("file_items", "2008-01-12 Some Html File.html")),
                         self.sos),
              SourceFile(datetime.fromtimestamp(3),
                         RelFile(self.path1, os.path.join("file_items", "2008-01-17 U Haz Been eZcluded.izu")),
                         self.sos),
              SourceFile(datetime.fromtimestamp(4),
                         RelFile(self.path1, os.path.join("file_items", "sub_dir", "2007-10-01 Empty Post.izu")),
                         self.sos),
              SourceFile(datetime.fromtimestamp(5),
                         RelFile(self.path1, os.path.join("file_items", "sub_dir", "2007-10-02 No Tags.izu")),
                         self.sos),
              SourceFile(datetime.fromtimestamp(6),
                         RelFile(self.path1, os.path.join("file_items", "sub_dir", "2008-01-02 Sub File Item.izu")),
                         self.sos),
            ],
            p1)

        self.assertListEquals(
            [ SourceDir(datetime.fromtimestamp(1),
                        RelDir(self.path2, "2006-05_Movies"),
                        [ "index.html" ],
                        self.sos ),
              SourceDir(datetime.fromtimestamp(2),
                        RelDir(self.path2, "2006-08-05 20.00.38  Progress"),
                        [ "index.html" ],
                        self.sos ),
              SourceDir(datetime.fromtimestamp(3),
                        RelDir(self.path2, "2007-10-07 11.00_Folder 2"),
                        [ "T12896_tiny1.jpg", "T12896_tiny2.jpg", "index.izu"],
                        self.sos ),
            ],
            p2)


    def testSourceSettings(self):
        # default reader does not have any custom source settings
        p = self.m1.Parse(self._tempdir)
        for item in p:
            self.assertEquals(self.sos, item.source_settings)

        # Now add a custom source settings to the reader. It gets
        # propagated to all items.
        sourceset = SourceSettings(rig_base="http://other/base/")
        m = MockSourceBlogReader(self.Log(), self.sis, sourceset, self.path1)
        p = m.Parse(self._tempdir)
        for item in p:
            self.assertNotEquals(None, item.source_settings)
            self.assertSame(sourceset, item.source_settings)
            self.assertEquals("http://other/base/", item.source_settings.rig_base)


#------------------------
class MockSourceDirReader(SourceDirReader):
    def __init__(self, log, settings, source_settings, path):
        super(MockSourceDirReader, self).__init__(log, settings, source_settings, path)
        self.update_needed_requests = []
        self._dir_time_stamp = 0

    def _UpdateNeeded(self, source_dir, dest_dir, all_files):
        self.update_needed_requests.append( ( source_dir, dest_dir, all_files ) )
        return True

    def _DirTimeStamp(self, dir):
        self._dir_time_stamp += 1
        return self._dir_time_stamp


class SourceDirReaderTest(RigTestCase):

    def setUp(self):
        self._tempdir = self.MakeTempDir()
        self._cachedir = self.MakeTempDir()
        self.path1 = os.path.join(self.getTestDataPath(), "album", "blog1")
        self.path2 = os.path.join(self.getTestDataPath(), "album", "blog2")
        source1 = SourceDirReader(self.Log(), None, None, self.path1)
        source2 = SourceDirReader(self.Log(), None, None, self.path2)
        self.sis = SiteSettings(public_name="Test Album",
                                source_list=[ source1, source2 ],
                                dest_dir=self._tempdir,
                                cache_dir=self._cachedir,
                                theme=DEFAULT_THEME,
                                base_url="http://www.example.com")
        self.sos = SourceSettings(rig_base="http://example.com/photos/")
        self.m1 = MockSourceDirReader(self.Log(), self.sis, self.sos, self.path1)
        self.m2 = MockSourceDirReader(self.Log(), self.sis, self.sos, self.path2)

    def tearDown(self):
        self.m = None
        self.RemoveDir(self._tempdir)
        self.RemoveDir(self._cachedir)

    def testParse(self):
        p1 = self.m1.Parse(self._tempdir)
        p2 = self.m2.Parse(self._tempdir)

        self.assertListEquals(
            [ ( RelDir(self.path1, "2007-10-07_Folder 1"),
                RelDir(self._tempdir, "2007-10-07_Folder 1"),
                [ "T12896_tiny_jpeg.jpg", "index.izu" ] ),
             ],
            self.m1.update_needed_requests)

        self.assertListEquals(
            [ ( RelDir(self.path2, "2006-05_Movies"),
                RelDir(self._tempdir, "2006-05_Movies"),
                [ "index.html" ] ),
              ( RelDir(self.path2, "2006-08-05 20.00.38  Progress"),
                RelDir(self._tempdir, "2006-08-05 20.00.38  Progress"),
                [ "index.html" ] ),
              ( RelDir(self.path2, "2007-10-07 11.00_Folder 2"),
                RelDir(self._tempdir, "2007-10-07 11.00_Folder 2"),
                [ "T12896_tiny1.jpg", "T12896_tiny2.jpg", "index.izu"] ),
             ],
            self.m2.update_needed_requests)

        self.assertListEquals(
            [ SourceDir(datetime.fromtimestamp(1),
                        RelDir(self.path1, "2007-10-07_Folder 1"),
                        [ "T12896_tiny_jpeg.jpg", "index.izu" ],
                        self.sos ) ],
            p1)

        self.assertListEquals(
            [ SourceDir(datetime.fromtimestamp(1),
                        RelDir(self.path2, "2006-05_Movies"),
                        [ "index.html" ],
                        self.sos ),
              SourceDir(datetime.fromtimestamp(2),
                        RelDir(self.path2, "2006-08-05 20.00.38  Progress"),
                        [ "index.html" ],
                        self.sos ),
              SourceDir(datetime.fromtimestamp(3),
                        RelDir(self.path2, "2007-10-07 11.00_Folder 2"),
                        [ "T12896_tiny1.jpg", "T12896_tiny2.jpg", "index.izu"],
                        self.sos ) ],
            p2)

    def testSourceSettings(self):
        # default reader has a default source settings
        p = self.m2.Parse(self._tempdir)
        for item in p:
            self.assertEquals(self.sos, item.source_settings)

        # Now add a custom source settings to the reader. It gets
        # propagated to all items.
        sourceset = SourceSettings(rig_base="http://other/base/")
        m = MockSourceDirReader(self.Log(), self.sis, sourceset, self.path2)
        p = m.Parse(self._tempdir)
        for item in p:
            self.assertSame(sourceset, item.source_settings)
            self.assertEquals("http://other/base/", item.source_settings.rig_base)


#------------------------
class MockSourceFileReader(SourceFileReader):
    def __init__(self, log, settings, source_settings, path):
        super(MockSourceFileReader, self).__init__(log, settings, source_settings, path)
        self.update_needed_requests = []
        self._file_time_stamp = 0

    def _UpdateNeeded(self, source_file, dest_dir):
        self.update_needed_requests.append( ( source_file, dest_dir ) )
        return True

    def _FileTimeStamp(self, file):
        self._file_time_stamp += 1
        return self._file_time_stamp


class SourceFileReaderTest(RigTestCase):

    def setUp(self):
        self._tempdir = self.MakeTempDir()
        self._cachedir = self.MakeTempDir()
        self.path1 = os.path.join(self.getTestDataPath(), "album", "blog1")
        source1 = SourceFileReader(self.Log(),
                                   site_settings=None,
                                   source_settings=None,
                                   path=self.path1)
        self.sis = SiteSettings(public_name="Test Album",
                                source_list=[ source1 ],
                                dest_dir=self._tempdir,
                                cache_dir=self._cachedir,
                                theme=DEFAULT_THEME,
                                base_url="http://www.example.com")
        self.sos = SourceSettings(rig_base="http://example.com/photos/")
        self.m1 = MockSourceFileReader(self.Log(), self.sis, self.sos, self.path1)

    def tearDown(self):
        self.m1 = None
        self.RemoveDir(self._tempdir)
        self.RemoveDir(self._cachedir)

    def testParse(self):
        p1 = self.m1.Parse(self._tempdir)

        self.assertListEquals(
            [ ( RelFile(self.path1, os.path.join("file_items", "2007-09-09 Izu File Item.izu")),
                RelDir (self._tempdir, "file_items") ),
              ( RelFile(self.path1, os.path.join("file_items", "2008-01-12 Some Html File.html")),
                RelDir (self._tempdir, "file_items") ),
              ( RelFile(self.path1, os.path.join("file_items", "2008-01-17 U Haz Been eZcluded.izu")),
                RelDir (self._tempdir, "file_items") ),
              ( RelFile(self.path1, os.path.join("file_items", "sub_dir", "2007-10-01 Empty Post.izu")),
                RelDir (self._tempdir, os.path.join("file_items", "sub_dir")) ),
              ( RelFile(self.path1, os.path.join("file_items", "sub_dir", "2007-10-02 No Tags.izu")),
                RelDir (self._tempdir, os.path.join("file_items", "sub_dir")) ),
              ( RelFile(self.path1, os.path.join("file_items", "sub_dir", "2008-01-02 Sub File Item.izu")),
                RelDir (self._tempdir, os.path.join("file_items", "sub_dir")) ),
             ],
            self.m1.update_needed_requests)

        self.assertListEquals(
            [ SourceFile(datetime.fromtimestamp(1),
                         RelFile(self.path1, os.path.join("file_items", "2007-09-09 Izu File Item.izu")),
                         self.sos),
              SourceFile(datetime.fromtimestamp(2),
                         RelFile(self.path1, os.path.join("file_items", "2008-01-12 Some Html File.html")),
                         self.sos),
              SourceFile(datetime.fromtimestamp(3),
                         RelFile(self.path1, os.path.join("file_items", "2008-01-17 U Haz Been eZcluded.izu")),
                         self.sos),
              SourceFile(datetime.fromtimestamp(4),
                         RelFile(self.path1, os.path.join("file_items", "sub_dir", "2007-10-01 Empty Post.izu")),
                         self.sos),
              SourceFile(datetime.fromtimestamp(5),
                         RelFile(self.path1, os.path.join("file_items", "sub_dir", "2007-10-02 No Tags.izu")),
                         self.sos),
              SourceFile(datetime.fromtimestamp(6),
                         RelFile(self.path1, os.path.join("file_items", "sub_dir", "2008-01-02 Sub File Item.izu")),
                         self.sos),
            ],
            p1)

    def testSourceSettings(self):
        # default reader has a default source settings
        p1 = self.m1.Parse(self._tempdir)
        for item in p1:
            self.assertEquals(self.sos, item.source_settings)

        # Now add a custom source settings to the reader. It gets
        # propagated to all items.
        sourceset = SourceSettings(rig_base="http://other/base/")
        m = MockSourceFileReader(self.Log(), self.sis, sourceset, self.path1)
        p = m.Parse(self._tempdir)
        for item in p:
            self.assertSame(sourceset, item.source_settings)
            self.assertEquals("http://other/base/", item.source_settings.rig_base)



#------------------------
# Local Variables:
# mode: python
# tab-width: 4
# py-continuation-offset: 4
# py-indent-offset: 4
# sentence-end-double-space: nil
# fill-column: 79
# End:
