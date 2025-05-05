#!/usr/bin/python
#-----------------------------------------------------------------------------|
"""
Unit tests for DirParser

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
from StringIO import StringIO

from tests.rig_test_case import RigTestCase
from rig.parser.dir_parser import DirParser, RelPath, RelDir, _EXCLUDE


#------------------------
class RelPathTest(RigTestCase):

    def setUp(self):
        self.m = RelPath(os.path.join("base", "dir"),
                         os.path.join("sub", "dir", "blah"))

    def testStr(self):
        s = str(self.m)
        self.rigAssertIsInstance(str, s)
        self.assertEquals(-1, s.find("RelPath"))
        self.assertNotEquals(-1, s.find(os.path.join("sub", "dir", "blah")))

    def testRepr(self):
        s = repr(self.m)
        self.rigAssertIsInstance(str, s)
        self.assertNotEquals(-1, s.find("RelPath"))
        self.assertNotEquals(-1, s.find(os.path.join("sub", "dir", "blah")))

    def testBasename(self):
        self.assertEquals("blah", self.m.basename())

    def testDirname(self):
        p = self.m.dirname()
        self.assertEquals(
              RelPath(os.path.join("base", "dir"),
                      os.path.join("sub", "dir")),
              p)

    def testJoin(self):
        p = self.m.join("foo", "bar")
        self.assertEquals(
              RelPath(os.path.join("base", "dir"),
                      os.path.join("sub", "dir", "blah", "foo", "bar")),
              p)

    def testEqAndHash(self):
        m2 = RelPath(os.path.join("base", "dir"),
                     os.path.join("sub", "dir", "blah"))

        self.assertNotSame(self.m, m2)
        self.assertEquals(self.m, m2)
        self.assertEquals(hash(self.m), hash(m2))

        m3 = m2.join("foo")

        self.assertNotSame(self.m, m3)
        self.assertNotEquals(self.m, m3)
        self.assertNotEquals(hash(self.m), hash(m3))


#------------------------
class MockDirParser(DirParser):
    def __init__(self, log, mock_dirs, abs_source_dir=None, abs_dest_dir=None):
        self._mock_dirs = mock_dirs
        super(MockDirParser, self).__init__(log, abs_source_dir, abs_dest_dir)

    def _new(self):
        return MockDirParser(self._log, self._mock_dirs, self._abs_source_dir, self._abs_dest_dir)

    def _listdir(self, dir):
        return self._mock_dirs.get(dir, [])

    def _isdir(self, dir):
        return dir in self._mock_dirs


class MockSubDir(MockDirParser):
    def __init__(self, log, mock_dirs, abs_source_dir, abs_dest_dir):
        super(MockSubDir, self).__init__(log, mock_dirs)
        self._abs_source_dir = abs_source_dir
        self._abs_dest_dir = abs_dest_dir

    def ParseMockDir(self, rel_curr_dir):
        self._ParseRec(rel_curr_dir)
        return self  # for chaining

    def _new(self):
        return MockSubDir(self._log, self._mock_dirs, self._abs_source_dir, self._abs_dest_dir)

#------------------------
class DirParserTest(RigTestCase):

    def testEmptyDir(self):
        m = MockDirParser(self.Log(), mock_dirs={})
        p = m.Parse("base", "dest")
        self.assertSame(p, m)
        self.assertListEquals([], m.Files())
        self.assertListEquals([], m.SubDirs())

    def testFiles(self):
        mock_dirs={ "base": [ "file1", "file2", "file3" ] }
        m = MockDirParser(self.Log(), mock_dirs)
        m.Parse( "base", "dest")
        self.assertEquals(RelDir("base", ""), m.AbsSourceDir())
        self.assertEquals(RelDir("dest", ""), m.AbsDestDir())
        self.assertListEquals([ "file1", "file2", "file3" ],
                              m.Files())
        self.assertListEquals([], m.SubDirs())

    def testFilesWithFilter(self):
        mock_dirs = { "base": [ "file1", "file2", "file3",
                               "entry1", "entry2", "entry3" ] }
        m = MockDirParser(self.Log(), mock_dirs)
        # File pattern that matches nothing
        m.Parse( "base", "dest", file_pattern="^A.*")
        self.assertListEquals([], m.Files())
        self.assertListEquals([], m.SubDirs())

        # Filter on file pattern
        m.Parse( "base", "dest", file_pattern="^f.*")
        self.assertListEquals([ "file1", "file2", "file3" ], m.Files())
        self.assertListEquals([], m.SubDirs())

        # Reusing the same object removes the old content
        m.Parse( "base", "dest", file_pattern="^e.*")
        self.assertListEquals([ "entry1", "entry2", "entry3" ], m.Files())
        self.assertListEquals([], m.SubDirs())

        # Patterns are matched using re.search so "e.*" will match "file" as well as "entry".
        m.Parse( "base", "dest", file_pattern="e.*1")
        self.assertListEquals([ "entry1", "file1" ], m.Files())
        self.assertListEquals([], m.SubDirs())

    def testDir1Level(self):
        mock_dirs={ "base": [ "dir1" ],
                   os.path.join("base", "dir1"): [ "file1" ] }
        m = MockDirParser(self.Log(), mock_dirs)

        m.Parse("base", "dest")
        dir1 = MockSubDir(self.Log(), mock_dirs, "base", "dest").ParseMockDir("dir1")

        self.assertListEquals([], m.Files())
        self.assertListEquals([ dir1 ], m.SubDirs())
        self.assertListEquals([ "file1" ], dir1.Files())
        self.assertListEquals([], dir1.SubDirs())

    def testDir2Levels(self):
        mock_dirs={ "base": [ "dir1a", "dir1b", "file0" ],
                   os.path.join("base", "dir1a"): [ "file2", "file1", "dir2a" ],
                   os.path.join("base", "dir1b"): [ "file3", "file4", "dir2b" ],
                   os.path.join("base", "dir1a", "dir2a"): [ "file6", "file5", "dir3a" ],
                   os.path.join("base", "dir1b", "dir2b"): [ "file7", "file8", "dir3b" ],
                   os.path.join("base", "dir1a", "dir2a", "dir3a"): [],
                   os.path.join("base", "dir1b", "dir2b", "dir3b"): [] }
        m = MockDirParser(self.Log(), mock_dirs)

        m.Parse("base", "dest")
        dir1a = MockSubDir(self.Log(), mock_dirs, "base", "dest").ParseMockDir("dir1a")
        dir1b = MockSubDir(self.Log(), mock_dirs, "base", "dest").ParseMockDir("dir1b")
        dir2a = MockSubDir(self.Log(), mock_dirs, "base", "dest").ParseMockDir(os.path.join("dir1a", "dir2a"))
        dir2b = MockSubDir(self.Log(), mock_dirs, "base", "dest").ParseMockDir(os.path.join("dir1b", "dir2b"))

        self.assertListEquals([ "file0" ], m.Files())
        self.assertListEquals([ dir1a, dir1b ], m.SubDirs())

        self.assertListEquals([ "file1", "file2" ], dir1a.Files())
        self.assertListEquals([ dir2a ], dir1a.SubDirs())
        self.assertListEquals([ "file3", "file4" ], dir1b.Files())
        self.assertListEquals([ dir2b ], dir1b.SubDirs())

        self.assertListEquals([ "file5", "file6" ], dir2a.Files())
        self.assertListEquals([], dir2a.SubDirs())
        self.assertListEquals([ "file7", "file8" ], dir2b.Files())
        self.assertListEquals([], dir2b.SubDirs())

    def testTraverseDirs(self):
        mock_dirs={ "base": [ "dir1b", "dir1a", "file0" ],
                   os.path.join("base", "dir1a"): [ "file2", "file1", "dir2a" ],
                   os.path.join("base", "dir1b"): [ "file3", "file4", "dir2b" ],
                   os.path.join("base", "dir1a", "dir2a"): [ "file6", "file5", "dir3a" ],
                   os.path.join("base", "dir1b", "dir2b"): [ "file7", "file8", "dir3b" ],
                   os.path.join("base", "dir1a", "dir2a", "dir3a"): [],
                   os.path.join("base", "dir1b", "dir2b", "dir3b"): [] }

        m = MockDirParser(self.Log(), mock_dirs)
        m.Parse("base", "dest")

        expected = [
            (RelDir("base", ""), RelDir("dest", ""), [ "file0" ]),
            (RelDir("base",              "dir1a"),           RelDir("dest",              "dir1a"),           [ "file1", "file2" ] ),
            (RelDir("base", os.path.join("dir1a", "dir2a")), RelDir("dest", os.path.join("dir1a", "dir2a")), [ "file5", "file6" ] ),
            (RelDir("base",              "dir1b"),           RelDir("dest",              "dir1b"),           [ "file3", "file4" ] ),
            (RelDir("base", os.path.join("dir1b", "dir2b")), RelDir("dest", os.path.join("dir1b", "dir2b")), [ "file7", "file8" ] )
            ]

        actual = [i for i in m.TraverseDirs()]
        self.assertListEquals(expected, actual)

    def testRemoveExclude(self):
        m = MockDirParser(self.Log(), mock_dirs={})

        self.assertEquals(None, m._RemoveExclude("base", None))
        self.assertListEquals([], m._RemoveExclude("base", []))

        ex = StringIO(".")
        self.assertListEquals([], m._RemoveExclude("base", [], ex))
        self.assertListEquals([],
              m._RemoveExclude("base",
                   [ "abc", "blah", "foo", _EXCLUDE ], ex))

        ex = StringIO("a")
        self.assertListEquals([ "blah", "foo" ],
            m._RemoveExclude("base",
                   [ "abc", "blah", "foo", _EXCLUDE ], ex))

        ex = StringIO("[a|b]")
        self.assertListEquals([ "foo" ],
            m._RemoveExclude("base",
                   [ "abc", "blah", "foo", _EXCLUDE ], ex))

        ex = StringIO("oo")
        self.assertListEquals([ "abc", "blah", "foo" ],
            m._RemoveExclude("base",
                   [ "abc", "blah", "foo", _EXCLUDE ], ex))

        ex = StringIO("""2007-1[3-9]_1[3-9]_Months
                         2007-20_20_Months""")
        self.assertListEquals(
          [],
          m._RemoveExclude("base",
            ['2007-20_20_Months', _EXCLUDE ],
            ex))

        ex = StringIO("""2007-1[3-9]_1[3-9]_Months
                         2007-20_20_Months
                         00-
                         temp
                         2005-
                         99-
                         .DS_Store
                         .*\.sh
                         \..*""")
        self.assertListEquals(
          [ '2007-06_18_Months', '2007-04_16_Months', '2007-09_21_Months', '2007-05_17_Months',
            '2006-09_9_Months', '2006-10_10_Months', '2006-05_5_Months', '2006-03_3_Months',
            '2006-06_6_Months', '2006-07_7_Months', '2007-10_22_Months', '2007-01_13_Months',
            '2006-04_Movies', '2007-03_15_Months', '2007-07_19_Months', '2006-12_12_Months',
            '2006-02_2_Months', '2006-08_8_Months', '2006-05_Movies', '2006-01_1_Month',
            '2007-02_14_Months', '2006-11_11_Months', '2007-08_20_Months', '2006-04_4_Months' ],
          m._RemoveExclude("base",
            [ '2007-06_18_Months', '2007-04_16_Months', '2007-09_21_Months', '2007-05_17_Months',
              '2006-09_9_Months', '2006-10_10_Months', '2006-05_5_Months', '2007-19_19_Months',
              '00-Best - Meilleures', '.DS_Store', '2006-03_3_Months', '2006-06_6_Months',
              '2006-07_7_Months', '.rsync-filter', '2007-10_22_Months', '2007-01_13_Months',
              '2006-04_Movies', '2005-12', '2005-10_Before', 'temp', '2007-15_15_Months',
              '2007-20_20_Months', '2007-03_15_Months', '2007-18_18_Months', '2007-13_13_Months',
              '99-Calendar', '2007-07_19_Months', '2006-12_12_Months', '2007-17_17_Months',
              '2007-16_16_Months', '2006-02_2_Months', '2006-08_8_Months', '2006-05_Movies',
              '2006-01_1_Month', '2007-02_14_Months', '2006-11_11_Months', '2007-08_20_Months',
              '2006-04_4_Months', _EXCLUDE ],
            ex))





#------------------------
# Local Variables:
# mode: python
# tab-width: 4
# py-continuation-offset: 4
# py-indent-offset: 4
# sentence-end-double-space: nil
# fill-column: 79
# End:
