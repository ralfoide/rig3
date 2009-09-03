#!/usr/bin/python
#-----------------------------------------------------------------------------|
"""
Unit tests for SourceItem

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

from datetime import datetime

from tests.rig_test_case import RigTestCase
from rig.source_item import SourceDir, SourceFile, SourceSettings
from rig.parser.dir_parser import RelDir, RelFile

#------------------------
class MockRelFile(RelFile):
    """
    Mocks RelFile so that realpath returns abs_path. This is necessary
    so that we can call it with dummy paths. OTOH it prevents from testing
    paths duplicates using symlinks, which we can't do on windows anyway.
    """
    def __init__(self, abs_base, rel_curr):
        super(RelFile, self).__init__(abs_base, rel_curr)

    def realpath(self):
        return self.abs_path

#------------------------
class SourceDirTest(RigTestCase):

    def testSourceDir(self):
        date = datetime.today()
        rel_dir = RelDir("/tmp", "foo")
        all_files = [ "index.txt", "image.jpg" ]
        s = SourceDir(date, rel_dir, all_files, SourceSettings())
        self.assertNotEquals(None, s)
        self.assertSame(date, s.date)
        self.assertSame(rel_dir, s.rel_dir)
        self.assertSame(all_files, s.all_files)

    def testEqAndHash(self):
        date1 = datetime.today()
        sos = SourceSettings(rig_base="/rig/base")

        s1 = SourceDir(date1, MockRelFile("/tmp", "foo.txt"), ["file1", "file2"], sos)
        s2 = SourceDir(date1, MockRelFile("/tmp", "foo.txt"), ["file1", "file2"], sos)

        # 2 equal but different objects
        self.assertNotSame(s1, s2)
        self.assertEquals(s1, s2)
        self.assertEquals(hash(s1), hash(s2))

        # with same path but a different date
        date2 = datetime.fromtimestamp(1) # e.g. 'Wed Dec 31 16:00:01 1969'
        s2 = SourceDir(date2, MockRelFile("/tmp", "foo.txt"), ["file1", "file2"], sos)
        self.assertNotEquals(s1, s2)
        self.assertNotEquals(hash(s1), hash(s2))

        # with same date but different path
        s2 = SourceDir(date1, MockRelFile("/tmp", "blah.txt"), ["file1", "file2"], sos)
        self.assertNotEquals(s1, s2)
        self.assertNotEquals(hash(s1), hash(s2))

        # with different all-files list
        s2 = SourceDir(date1, MockRelFile("/tmp", "foo.txt"), ["abc", "def", "123"], sos)
        self.assertNotEquals(s1, s2)
        self.assertNotEquals(hash(s1), hash(s2))

        # same date/path but different source settings
        sos2 = SourceSettings(rig_base="/all/your/bases")
        s2 = SourceDir(date1, MockRelFile("/tmp", "foo.txt"), ["file1", "file2"], sos2)
        self.assertNotEquals(s1, s2)
        self.assertNotEquals(hash(s1), hash(s2))

        # and different categories
        s2 = SourceDir(date1, MockRelFile("/tmp", "foo.txt"), ["file1", "file2"], sos)
        self.assertEquals(s1, s2)
        self.assertEquals(hash(s1), hash(s2))
        s2.categories = ["foo", "bar"]
        self.assertNotEquals(s1, s2)
        self.assertNotEquals(hash(s1), hash(s2))

#------------------------
class SourceFileTest(RigTestCase):

    def testSourceFile(self):
        date = datetime.today()
        rel_file = MockRelFile("/tmp", "foo.txt")
        s = SourceFile(date, rel_file, SourceSettings())
        self.assertNotEquals(None, s)
        self.assertSame(date, s.date)
        self.assertSame(rel_file, s.rel_file)

    def testEqAndHash(self):
        date1 = datetime.today()
        sos = SourceSettings(rig_base="/rig/base")

        s1 = SourceFile(date1, MockRelFile("/tmp", "foo.txt"), sos)
        s2 = SourceFile(date1, MockRelFile("/tmp", "foo.txt"), sos)

        # 2 equal but different objects
        self.assertNotSame(s1, s2)
        self.assertEquals(s1, s2)
        self.assertEquals(hash(s1), hash(s2))

        # with same path but a different date
        date2 = datetime.fromtimestamp(1) # e.g. 'Wed Dec 31 16:00:01 1969'
        s2 = SourceFile(date2, MockRelFile("/tmp", "foo.txt"), sos)
        self.assertNotEquals(s1, s2)
        self.assertNotEquals(hash(s1), hash(s2))

        # with same date but different path
        s2 = SourceFile(date1, MockRelFile("/tmp", "blah.txt"), sos)
        self.assertNotEquals(s1, s2)
        self.assertNotEquals(hash(s1), hash(s2))

        # same date/path but different source settings
        sos2 = SourceSettings(rig_base="/all/your/bases")
        s2 = SourceFile(date1, MockRelFile("/tmp", "foo.txt"), sos2)
        self.assertNotEquals(s1, s2)
        self.assertNotEquals(hash(s1), hash(s2))

        # and different categories
        s2 = SourceFile(date1, MockRelFile("/tmp", "foo.txt"), sos)
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
