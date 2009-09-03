#!/usr/bin/python
#-----------------------------------------------------------------------------|
"""
Rig3 main module.

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
import sys
import getopt
from rig import stats
from rig.log import Log
from rig.site import CreateSite
from rig.sites_settings import SitesSettings

#------------------------
class Rig3(object):
    _USAGE = """
Rig3 [-h] [-v]

Options:
    -h, --help:    This help
    -n, --dry-run: Dry-run, do nothing, print what would be done
    -v, --verbose: Verbose logging
    -q, --quiet:   Quiet logging
    -c, --config:  Configuration file (default: %(_configPaths)s)
    -f, --force:   Force generation even if cache is hot and unmodified
"""

    def __init__(self):
        self._log = None
        self._sites_settings = None
        self._verbose = Log.LEVEL_NORMAL
        self._dry_run = False
        self._force = False
        self._configPaths = [ "/etc/rig3.rc",
                              os.path.expanduser(os.path.join("~", ".rig3rc")) ]

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
                                          "hHvqc:nf",
                                          ["help", "verbose", "quiet", "config=",
                                           "dry-run", "dry_run", "dryrun",
                                           "force"])
            for opt, value in options:
                if opt in ["-h",  "-H", "--help"]:
                    self._UsageAndExit()
                elif opt in ["-v", "--verbose"]:
                    self._verbose = Log.LEVEL_VERY_VERBOSE
                elif opt in ["-q", "--quiet"]:
                    self._verbose = Log.LEVEL_MOSLTY_SILENT
                elif opt in ["-c", "--config"]:
                    self._configPaths = [ value ]
                elif opt in ["-n", "--dry-run", "--dry_run", "--dryrun"]:
                    self._dry_run = True
                elif opt in ["-f", "--force"]:
                    self._force = True
        except getopt.error, msg:
            self._UsageAndExit(msg)

    def Run(self):
        """
        Runs rig3.
        """
        self._log = Log(verbose_level=self._verbose, use_stderr=self._verbose)
        self._sites_settings = SitesSettings(self._log).Load(self._configPaths)
        self.ProcessSites()

    def ProcessSites(self):
        st = stats.Start("0-Total Time")

        s = self._sites_settings
        for site_id in s.Sites():
            site = CreateSite(self._log,
                              self._dry_run,
                              self._force,
                              s.GetSiteSettings(site_id))
            site.Process()
            site.Dispose()

        st.Stop(len(s.Sites()))
        stats.Display(self._log)

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
