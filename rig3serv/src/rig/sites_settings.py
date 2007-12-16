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
from rig.site_base import DEFAULT_THEME

#------------------------
class SiteSettings(object):
    """
    Settings for one site with defaults:
    - public_name (str): Site name, as published on the generated page. Free text.
    - source_list (list SourceBase): List of SourceBase reeaders
    - dest_dir (str): Path of where to generate content. Can be relative or absolute.
    - theme (str): Name of the theme to use, must match a directory in templates.
    - base_url (str): URL where the site will be published, in case templates wants to use that.
      Will be used as-is, so you probably want to terminate it with a / separator.
    - rig_url (str): URL of the RIG served album. Will be used as-is, i.e. typically by
      appending index.php, so you really want to terminate it with a / separator.
    - header_img_url (str): Full URL for the header image. If not present, the default one from
      the theme will be used.
    - header_img_height (int): The height of the header_img. Default is 185.
    """
    def __init__(self,
                 public_name="",
                 source_list=None,
                 dest_dir=None,
                 theme=DEFAULT_THEME,
                 base_url="http://html.base.url/",
                 rig_url="http://rig.base.url/photos/",
                 header_img_url="",
                 header_img_height=185,
                 tracking_code=""):
        self.public_name = public_name
        self.source_list = source_list or []
        self.dest_dir = dest_dir
        self.theme = theme
        self.base_url = base_url
        self.rig_url = rig_url
        self.header_img_url = header_img_url
        self.header_img_height = header_img_height
        self.tracking_code = tracking_code

    def AsDict(self):
        """
        Returns a copy of the settings' dictionnary.
        It's safe for caller to modify this dictionnary.
        """
        return dict(self.__dict__)

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
            sites = self.ConfigParser().get("serve", "sites")
            result = [s.strip() for s in sites.split(",")]
            return result
        except ConfigParser.NoSectionError:
            return []

    def GetSiteSettings(self, site_name):
        """
        Returns a SiteSetting for the given site.
        """
        s = SiteSettings()
        vars = list(self.ConfigParser().items(site_name))
        self._ProcessSources(s, vars)  # TODO missing
        self._ProcessDefaults(s, vars)
        return s

    def _ProcessDefaults(self, settings, vars):
        for k in settings.__dict__.iterkeys():
            try:
                settings.__dict__[k] = vars[k]
            except KeyError:
                pass  # preserve defaults from SiteSettings.__init__

#------------------------
# Local Variables:
# mode: python
# tab-width: 4
# py-continuation-offset: 4
# py-indent-offset: 4
# sentence-end-double-space: nil
# fill-column: 79
# End:
