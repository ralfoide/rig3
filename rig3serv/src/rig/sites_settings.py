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
from rig.site import DEFAULT_THEME

#------------------------
class SiteSettings(object):
    """
    Settings for one site with defaults.
    """
    def __init__(self,
                 public_name="",
                 source_dir=None,
                 dest_dir=None,
                 theme=DEFAULT_THEME,
                 base_url="http://html.base.url/",
                 rig_url="http://rig.base.url/photos/"):
        self.public_name = public_name
        self.source_dir = source_dir
        self.dest_dir = dest_dir
        self.theme = theme
        self.base_url = base_url
        self.rig_url = rig_url

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

    def GetSiteSettings(self, site_name):
        """
        Returns a SiteSetting for the given site.
        """
        s = SiteSettings()
        for k in s.__dict__.iterkeys():
            try:
                s.__dict__[k] = self._parser.get(site_name, k)
            except ConfigParser.NoOptionError:
                pass  # preserve defaults from SiteSettings.__init__
        return s

#------------------------
# Local Variables:
# mode: python
# tab-width: 4
# py-continuation-offset: 4
# py-indent-offset: 4
# sentence-end-double-space: nil
# fill-column: 79
# End:
