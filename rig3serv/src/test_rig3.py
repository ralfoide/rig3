#!/usr/bin/python
#-----------------------------------------------------------------------------|
"""
Unit tests for rig3

Creates a test suite with all the tests under the "tests/" directory
and then invokes unittest.TestProgram with it. This means all the command
line options of unittest.TestProgram are still available.
"""


import os
import sys
import glob
import unittest
from tests.rig_test_case import RigTestCase

#------------
class CustomTestProgram(unittest.TestProgram):
    """
    Overrides unittest.TestProgram to use our own test list if none is
    specified on the command line.
    """
    def __init__(self, tests):
        self._tests = tests
        unittest.TestProgram.__init__(self)

    def runTests(self):
        RigTestCase.setVerbose(self.verbosity == 2)
        if self.test is None or self.test.countTestCases() == 0:
            self.test = self._tests
        unittest.TestProgram.runTests(self)
        

#------------
def get_tests():
    """
    Create a test suite with all the tests to run.
    """
    localdir = os.path.join(os.path.dirname(__file__), "tests")
    start = len(localdir.split(os.path.sep)) - 1
    modules = []
    for root, dirs, files in os.walk(localdir):
        if "CVS"  in dirs:
            dirs.remove("CVS")
        if ".svn" in dirs:
            dirs.remove(".svn")
        if "data" in dirs:
            dirs.remove("data")
        if not "__init__.py" in files:
            print >>sys.stderr, ("WARNING: '%s' ignored because not a package. "
                                 "Did you forget to create a __init__.py?") % root
        base = root.split(os.path.sep)
        for file in files:
            if file != "__init__.py" and file.endswith(".py"):
                file = file[:-3]  # remove .py
                m = list(base)
                m.append(file)
                m = m[start:]
                modules.append(".".join(m))

    print >>sys.stderr, "Rig Tests:", ", ".join([m.split(".")[-1] for m in modules])

    loader = unittest.TestLoader()
    tests = loader.loadTestsFromNames(modules)
    return tests
    

#------------------------
if __name__ == "__main__":
    print >>sys.stderr, "UT Main", sys.argv
    tests = get_tests()
    p = CustomTestProgram(tests)


#------------------------
# Local Variables:
# mode: python
# tab-width: 4
# py-continuation-offset: 4
# py-indent-offset: 4
# sentence-end-double-space: nil
# fill-column: 79
# End:
