#!/usr/bin/python
#-----------------------------------------------------------------------------|
"""
Unit tests for DirParser

Part of Rig3.
License GPL.
"""
__author__ = "ralfoide@gmail.com"

from tests.rig_test_case import RigTestCase
from rig.dir_parser import DirParser

#------------------------
class MockDirParser(DirParser):
    def __init__(self, log, mock_dirs):
        self._mock_dirs = mock_dirs
        super(MockDirParser, self).__init__(log)

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
        p = m.Parse("/base", "/tmp/dest")
        self.assertEquals(p, m)
        self.assertListEquals([], m.Files())
        self.assertListEquals([], m.SubDirs())

    def testFiles(self):
        m = MockDirParser(self.Log(),
                          mock_dirs={ "/base": [ "file1", "file2", "file3" ] })
        m.Parse( "/base", "/dest")
        self.assertEquals("/base", m.AbsSourceDir())
        self.assertEquals("/dest", m.AbsDestDir())
        self.assertListEquals([ "file1", "file2", "file3" ],
                              m.Files())
        self.assertListEquals([], m.SubDirs())

    def testFilesWithFilter(self):
        m = MockDirParser(self.Log(),
                          mock_dirs={ "/base": [ "file1", "file2", "file3",
                                                "entry1", "entry2", "entry3" ] })
        # File pattern that matches nothing
        m.Parse( "/base", "/dest", file_pattern="^A.*")
        self.assertListEquals([], m.Files())
        self.assertListEquals([], m.SubDirs())

        # Filter on file pattern
        m.Parse( "/base", "/dest", file_pattern="^f.*")
        self.assertListEquals([ "file1", "file2", "file3" ], m.Files())
        self.assertListEquals([], m.SubDirs())

        # Reusing the same object removes the old content
        m.Parse( "/base", "/dest", file_pattern="^e.*")
        self.assertListEquals([ "entry1", "entry2", "entry3" ], m.Files())
        self.assertListEquals([], m.SubDirs())

        # Patterns are matched using re.search so "e.*" will match "file" as well as "entry".
        m.Parse( "/base", "/dest", file_pattern="e.*1")
        self.assertListEquals([ "file1", "entry1" ], m.Files())
        self.assertListEquals([], m.SubDirs())

    def testDirs(self):
        m = MockDirParser(self.Log(),
                          mock_dirs={ "/base": [ "dir1" ],
                                      "/base/dir1": [ "file1" ] })
        m.Parse("/base", "/dest")
        self.assertListEquals([], m.Files())
        self.assertListEquals([], m.SubDirs())
        

#------------------------
# Local Variables:
# mode: python
# tab-width: 4
# py-continuation-offset: 4
# py-indent-offset: 4
# sentence-end-double-space: nil
# fill-column: 79
# End:
