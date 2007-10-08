#!/usr/bin/python
#-----------------------------------------------------------------------------|
"""
Rig3 module: Settings for top-level sites definitions.

Each site has the following definitions (all are strings):
- internal_name: A compact identifier, ideally short and without spaces
- public_name: The public name for the site.
- source_dir: The absolute path where sources are located
- dest_dir: The absolute path where files are generated
- theme: The identifier for the generated files' theme.

Part of Rig3.
License GPL.
"""
__author__ = "ralfoide@gmail.com"

import sys
import ConfigParser
from rig.settings_base import SettingsBase

#------------------------
class SitesSettings(SettingsBase):
    """
    Loader for Sites Settings.
    """
    def __init__(self, log):
        super(SitesSettings, self).__init__(log)

    def Load(self, config_paths):
        """
        Loads sites .rc files from the list of config_paths.
        Return self, for chaining.
        """
        return super(SitesSettings, self).Load(config_paths)

    def Sites(self):
        """
        Returns the list of internal site names available.
        """
        try:
            sites = self._parser.get("serve", "sites")
            result = [s.strip() for s in sites.split(",")]
            return result
        except ConfigParser.NoSectionError:
            return []

    def PublicName(self, site):
        return self._parser.get(site, "public_name")

    def SourceDir(self, site):
        return self._parser.get(site, "source_dir")

    def DestDir(self, site):
        return self._parser.get(site, "dest_dir")

    def Theme(self, site):
        return self._parser.get(site, "theme")

#------------------------
# Local Variables:
# mode: python
# tab-width: 4
# py-continuation-offset: 4
# py-indent-offset: 4
# sentence-end-double-space: nil
# fill-column: 79
# End:
