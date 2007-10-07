#!/usr/bin/python
#-----------------------------------------------------------------------------|
"""
Rig3 main module.

License GPL.
"""
__author__ = "ralfoide@gmail.com"

import os
import sys
import getopt
from rig.log import Log
from rig.site import Site
from rig.sites_settings import SitesSettings

#------------------------
class Rig3(object):
    _USAGE = """
Rig3 [-h] [-v]

Options:
    -h, --help:    This help
    -v, --verbose: Verbose logging (default: %(_verbose)s)
    -c, --config:  Configuration file (default: %(_configPaths)s) 
"""
    
    def __init__(self):
        self._log = None
        self._sites_settings = None
        self._verbose = False
        self._configPaths = [ "/etc/rig3.rc", os.path.expanduser("~/.rig3rc") ]

    def _UsageAndExit(self, msg=None):
        """
        Prints usage string and exit program.
        """
        if msg:
            print msg
        print self._USAGE % self.__dict__
        sys.exit(2)

    def ParseArgs(self, argv):
        """
        Parses command line arguments.
        """
        try:
            options, args = getopt.getopt(argv[1:],
                                          "hHvc:",
                                          ["help", "verbose", "config="])
            for opt, value in options:
                if opt in ["-h",  "-H", "--help"]:
                    self._UsageAndExit()
                elif opt in ["-v", "--verbose"]:
                    self._verbose = True
                elif opt in ["-c", "--config"]:
                    self._configPaths = [ value ]
        except getopt.error, msg:
            self._UsageAndExit(msg)

    def Run(self):
        """
        Runs rig3.
        """
        self._log = Log(use_stderr=self._verbose)
        self._sites_settings = SitesSettings(self._configPaths)
        self.ProcessSites()

    def ProcessSites(self):
        s = self._sites_settings
        for site_id in s.Sites():
            site = Site(s.PublicName(site_id),
                        s.SourceDir(site_id),
                        s.DestDir(site_id),
                        s.Theme(site_id))
            site.Process()

    def Close(self):
        """
        Close whatever is needed before leaving.
        """
        self._log.Close()

#------------------------
def main():
    r = Rig3()
    r.ParseArgs(sys.argv)
    r.Run()
    r.Close()

if __name__ == "__main__":
    main()

#------------------------
# Local Variables:
# mode: python
# tab-width: 4
# py-continuation-offset: 4
# py-indent-offset: 4
# sentence-end-double-space: nil
# fill-column: 79
# End:
