#!/usr/bin/python
#-----------------------------------------------------------------------------|
"""
Unit tests for Site

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

from rig.site_base import SiteBase
from rig.site_base import DEFAULT_THEME
from rig.site.site_default import SiteDefault
from rig.sites_settings import SiteSettings
from rig.parser.dir_parser import DirParser, RelDir
from rig.source_reader import SourceDirReader
from rig.source_item import SourceFile, SourceDir, SourceSettings
from rig.parser.dir_parser import RelFile, RelDir

#------------------------
class MockSiteBase(SiteBase):
    """
    Behaves like a Site() but overrides the base template directory location
    to use testdata/templates instead.

    Also traps the last _Filltemplate parameters.
    """
    def __init__(self, test_case, log, dry_run, force, settings):
        self._test_case = test_case
        self._fill_template_params = {}
        super(MockSiteBase, self).__init__(log, dry_run, force, settings)

    def _TemplateDir(self):
        """"
        Uses testdata/templates/ instead of templates/
        """
        return os.path.join(self._test_case.getTestDataPath(), "templates")

    def GeneratePages(self, categories, items):
        pass

    def GenerateItem(self, source_item):
        return None

class MockSiteBase2(MockSiteBase):
    """
    Like MockSiteBase except GenerateItem is hacked to return its argument.
    Used to test _ProcessSourceItems.
    """
    def __init__(self, test_case, log, dry_run, force, settings):
        super(MockSiteBase2, self).__init__(test_case, log, dry_run, force, settings)

    def GenerateItem(self, source_item):
        return source_item

#------------------------
class MockSourceReader(object):
    """
    A mock source reader that returns the list of source items in its
    Parse method. Used to test _ProcessSourceItems.
    """
    def __init__(self, source_items):
        self._source_items = source_items

    def Parse(self, dest_dir):
        return self._source_items

#------------------------
class SiteBaseTest(RigTestCase):

    def setUp(self):
        self._tempdir = self.MakeTempDir()
        self._cachedir = self.MakeTempDir()
        source = SourceDirReader(self.Log(),
                                 site_settings=None,
                                 source_settings=None,
                                 path=os.path.join(self.getTestDataPath(), "album"))
        self.sis = SiteSettings(public_name="Test Album",
                                source_list=[ source ],
                                dest_dir=self._tempdir,
                                cache_dir=self._cachedir,
                                theme=DEFAULT_THEME,
                                base_url="http://www.example.com")
        self.sos = SourceSettings(rig_base="http://example.com/photos/")

    def tearDown(self):
        self.RemoveDir(self._tempdir)
        self.RemoveDir(self._cachedir)

    def testInit(self):
        """
        Test init of Site
        """
        source = SourceDirReader(self.Log(), None, None, "/tmp/source/data")
        sis = SiteSettings(public_name="Site Name",
                         source_list=[ source ],
                         dest_dir=self._tempdir,
                         theme=DEFAULT_THEME)
        m = MockSiteBase(self, self.Log(), False, True, sis)
        self.assertNotEquals(None, m)
        self.assertFalse(m._dry_run)
        self.assertTrue(m._force)
        self.assertEquals("Site Name", m._site_settings.public_name)
        self.assertEquals(
            [ SourceDirReader(self.Log(), None, None, "/tmp/source/data") ],
            m._site_settings.source_list)
        self.assertEquals(self._tempdir, m._site_settings.dest_dir)
        self.assertEquals(DEFAULT_THEME, m._site_settings.theme)

    def testPatterns(self):
        self.assertSearch(SiteBase.DIR_PATTERN, "2007-10-07_Folder 1")
        self.assertSearch(SiteBase.DIR_PATTERN, "2006-08-05 20.00.38  Progress")
        self.assertSearch(SiteBase.VALID_FILES, "index.izu")
        self.assertSearch(SiteBase.VALID_FILES, "image.jpg")
        self.assertSearch(SiteBase.VALID_FILES, "image.jpeg")
        self.assertSearch(SiteBase.VALID_FILES, "T12896_tiny_jpeg.jpg")

    def testAlbum(self):
        m = MockSiteBase(self, self.Log(), False, True, self.sis)
        m.Process()

    def testTemplateDir(self):
        m = SiteBase(self.Log(), False, True, self.sis)
        td = m._TemplateDir()
        self.assertNotEquals("", td)
        self.assertTrue(os.path.exists(td))
        self.assertTrue(os.path.isdir(td))
        # the templates dir should contain at least the "default" sub-dir
        # with at least the entry.xml and index.xml files
        self.assertTrue(os.path.exists(os.path.join(td, "default")))
        self.assertTrue(os.path.exists(os.path.join(td, "default", SiteDefault._TEMPLATE_HTML_INDEX)))
        self.assertTrue(os.path.exists(os.path.join(td, "default", SiteDefault._TEMPLATE_HTML_ENTRY)))

    def testCopyMedia(self):
        m = MockSiteBase(self, self.Log(), False, True, self.sis)
        m._CopyMedia()

        self.assertTrue(os.path.isdir (os.path.join(self._tempdir, "media")))

        style_css_path = os.path.join(self._tempdir, "media", "style.css")
        self.assertTrue(os.path.exists(style_css_path))

        # Check that the style.css has been transformed
        f = file(style_css_path, "rb")
        style_css = f.read()
        f.close()
        self.assertNotSearch("base_url", style_css)
        self.assertNotSearch("public_name", style_css)
        self.assertSearch("base url is http://www.example.com", style_css)
        self.assertSearch("public name is Test Album", style_css)

    def testProcessSourceItems_DuplicatesRemoval(self):
        today = datetime.today()
        sos2 = SourceSettings(rig_base="http://all.your.bases/are.../")

        source = MockSourceReader(
             [
             SourceFile(today, RelFile("/base", "file1"), self.sos),
             SourceFile(today, RelFile("/AYB",  "file1"), self.sos),
             SourceFile(today, RelFile("/AYB",  "file1"), self.sos),
             SourceFile(today, RelFile("/base", "file2"), self.sos),
             SourceFile(today, RelFile("/base", "file2"), sos2),
             SourceFile(today, RelFile("/base", "file2"), self.sos),
             SourceDir(today, RelDir("/base", "dir1"), [ "all", "files" ], self.sos),
             SourceDir(today, RelDir("/base", "dir2"), [ "all", "files" ], self.sos),
             SourceDir(today, RelDir("/base", "dir1"), [ "all", "my", "files" ], self.sos),
             SourceDir(today, RelDir("/base", "dir1"), [ "all", "files" ], self.sos),
             SourceDir(today, RelDir("/base", "dir2"), [ "all", "files" ], self.sos),
             ])
        m2 = MockSiteBase2(self, self.Log(), False, True, self.sis)

        in_out_items = []
        dups = {}
        m2._ProcessSourceItems(source, in_out_items, dups)

        self.assertListEquals(
             [
             SourceFile(today, RelFile("/base", "file1"), self.sos),
             SourceFile(today, RelFile("/AYB",  "file1"), self.sos),
             SourceFile(today, RelFile("/base", "file2"), self.sos),
             SourceFile(today, RelFile("/base", "file2"), sos2),
             SourceDir(today, RelDir("/base", "dir1"), [ "all", "files" ], self.sos),
             SourceDir(today, RelDir("/base", "dir2"), [ "all", "files" ], self.sos),
             SourceDir(today, RelDir("/base", "dir1"), [ "all", "my", "files" ], self.sos),
             ],
             in_out_items)


#------------------------
# Local Variables:
# mode: python
# tab-width: 4
# py-continuation-offset: 4
# py-indent-offset: 4
# sentence-end-double-space: nil
# fill-column: 79
# End:
