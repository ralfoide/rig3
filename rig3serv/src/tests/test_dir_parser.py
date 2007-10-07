#!/usr/bin/python
#-----------------------------------------------------------------------------|
"""
Unit tests for DirParser

Part of Rig3.
License GPL.
"""
__author__ = "ralfoide@gmail.com"

import os

from tests.rig_test_case import RigTestCase
from rig.dir_parser import DirParser

#------------------------
class MockDirParser(DirParser):
    def __init__(self, log, mock_dirs):
        self._mock_dirs = mock_dirs
        super(MockDirParser, self).__init__(log)

    def _new(self):
        return MockDirParser(self._log, self._mock_dirs)

    def _listdir(self, dir):
        return self._mock_dirs.get(dir, [])

    def _isdir(self, dir):
        return dir in self._mock_dirs

#------------------------
class DirParserTest(RigTestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def testEmptyDir(self):
        m = MockDirParser(self.Log(), mock_dirs={})
        p = m.Parse("base", "dest")
        self.assertEquals(p, m)
        self.assertListEquals([], m.Files())
        self.assertListEquals([], m.SubDirs())

    def testFiles(self):
        mock_dirs={ "base": [ "file1", "file2", "file3" ] }
        m = MockDirParser(self.Log(), mock_dirs)
        m.Parse( "base", "dest")
        self.assertEquals("base", m.AbsSourceDir())
        self.assertEquals("dest", m.AbsDestDir())
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
        self.assertListEquals([ "file1", "entry1" ], m.Files())
        self.assertListEquals([], m.SubDirs())

    def testDir1Level(self):
        mock_dirs={ "base": [ "dir1" ],
                   os.path.join("base", "dir1"): [ "file1" ] }
        m = MockDirParser(self.Log(), mock_dirs)
        dir1 = MockDirParser(self.Log(), mock_dirs)

        m.Parse("base", "dest")
        dir1.Parse(os.path.join("base", "dir1"), os.path.join("dest", "dir1"))

        self.assertListEquals([], m.Files())
        self.assertListEquals([ dir1 ], m.SubDirs())
        self.assertListEquals([ "file1" ], dir1.Files())
        self.assertListEquals([], dir1.SubDirs())

    def testDir2Levels(self):
        mock_dirs={ "base": [ "dir1a", "dir1b", "file0" ],
                   os.path.join("base", "dir1a"): [ "file1", "file2", "dir2a" ],
                   os.path.join("base", "dir1b"): [ "file3", "file4", "dir2b" ],
                   os.path.join("base", "dir1a", "dir2a"): [ "file5", "file6", "dir3a" ],
                   os.path.join("base", "dir1b", "dir2b"): [ "file7", "file8", "dir3b" ],
                   os.path.join("base", "dir1a", "dir2a", "dir3a"): [],
                   os.path.join("base", "dir1b", "dir2b", "dir3b"): [] }
        m = MockDirParser(self.Log(), mock_dirs)
        dir1a = MockDirParser(self.Log(), mock_dirs)
        dir1b = MockDirParser(self.Log(), mock_dirs)
        dir2a = MockDirParser(self.Log(), mock_dirs)
        dir2b = MockDirParser(self.Log(), mock_dirs)

        m.Parse("base", "dest")
        dir1a.Parse(os.path.join("base", "dir1a"), os.path.join("dest", "dir1a"))
        dir1b.Parse(os.path.join("base", "dir1b"), os.path.join("dest", "dir1b"))
        dir2a.Parse(os.path.join("base", "dir1a", "dir2a"), os.path.join("dest", "dir1a", "dir2a"))
        dir2b.Parse(os.path.join("base", "dir1b", "dir2b"), os.path.join("dest", "dir1b", "dir2b"))

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

#------------------------
# Local Variables:
# mode: python
# tab-width: 4
# py-continuation-offset: 4
# py-indent-offset: 4
# sentence-end-double-space: nil
# fill-column: 79
# End:
