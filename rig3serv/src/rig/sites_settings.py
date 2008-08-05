#!/usr/bin/python
#-----------------------------------------------------------------------------|
"""
Rig3 module: Settings for top-level sites definitions.

Part of Rig3.
License GPL.
"""
__author__ = "ralfoide@gmail.com"

import re
import ConfigParser
from rig.settings_base import SettingsBase
from rig.source_item import SourceSettings
from rig.source_reader import SourceDirReader, SourceFileReader
from rig.site_base import DEFAULT_THEME

_CAT_FILTER_SEP = re.compile("[, \t\f]")

DEFAULT_ITEMS_PER_PAGE = 20  # Default for settings.num_item_index and settings.num_item_atom


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
    - rig_base(string): An http:// URL for the base of your RIG album.
    - rig_img_size(int): 512, the default size of a [rigimg] tag in Izumi
    - rig_album_url(string): Declares how to generate a link to a given RIG album.
        rig_album_url=%(rig_base)s?album=%(album)s
    - rig_img_url(string): Declares how to generate a text link to a given RIG image _page_.
        rig_img_url=%(rig_base)s?album=%(album)s&img=%(img)s
    - rig_thumb_url(string): Declares how to generate an IMG reference to a give RIG image.
        rig_thumb_url=%(rig_base)s?th=&album=%(album)s&img=%(img)s&sz=%(size)s&q=75
    - header_img_url (str): Full URL for the header image. If not present, the default one from
      the theme will be used.
    - header_img_height (int): The height of the header_img. Default is 185.
    - cat_exclude: A dict of category words to exclude. Empty or None to exclude nothing,
                   CAT_ALL to exclude everything, CAT_NOTAG to exclude all non-tagged.
                   Note that the values in the dictionnary are irrelevant, only keys matter.
    - cat_include: A dict of category words to include. Empty or None or CAT_ALL to include all,
                   CAT_NOTAG to include all non-tagged.
                   Note that the values in the dictionnary are irrelevant, only keys matter.
    - img_gen_script (string): An optional script to execute to generate images
    - num_item_page (int): Number of items per HTML page. Default is 20. Must be > 0.
    - num_item_atom (int): Number of items in ATOM feed. Default is 20. -1 for all.
    - html_header (string): Path to HTML header. Default is "html_header.html"
    - toc_categories: A list of categories for which to insert a TOC to their pages.
                    Default is none of them.
    - reverse_categories: A list of categories to display in reverse date order (i.e. incremental).
                    Default is to display in decrementing date.
    """
    CAT_ALL = "*"
    CAT_NOTAG = "$"
    CAT_EXCLUDE = "!"

    def __init__(self,
                 public_name="",
                 source_list=None,
                 dest_dir=None,
                 theme=DEFAULT_THEME,
                 base_url=None,
                 rig_base=None,
                 rig_album_url="%(rig_base)s?album=%(album)s",
                 rig_img_url="%(rig_base)s?album=%(album)s&img=%(img)s",
                 rig_thumb_url="%(rig_base)s?th=&album=%(album)s&img=%(img)s&sz=%(size)s&q=75",
                 rig_img_size=512,
                 header_img_url="",
                 header_img_height=185,
                 tracking_code="",
                 cat_exclude=None,
                 cat_include=None,
                 img_gen_script="",
                 num_item_page=DEFAULT_ITEMS_PER_PAGE,
                 num_item_atom=DEFAULT_ITEMS_PER_PAGE,
                 html_header="html_header.html",
                 toc_categories=[],
                 reverse_categories=[]):
        self.public_name = public_name
        self.source_list = source_list or []
        self.dest_dir = dest_dir
        self.theme = theme
        self.base_url = base_url
        self.rig_base = rig_base
        self.rig_album_url = rig_album_url
        self.rig_img_url = rig_img_url
        self.rig_thumb_url = rig_thumb_url
        self.rig_img_size = int(rig_img_size)
        self.header_img_url = header_img_url
        self.header_img_height = int(header_img_height)
        self.tracking_code = tracking_code
        self.cat_exclude = cat_exclude
        self.cat_include = cat_include
        self.img_gen_script = img_gen_script
        self.num_item_page = int(num_item_page)
        self.num_item_atom = int(num_item_atom)
        self.html_header = html_header
        self.reverse_categories = reverse_categories
        self.toc_categories = toc_categories

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
        vars = self.Items(site_name)
        self._ProcessDefaults(s, vars)
        self._ProcessSources(s, vars)
        self._ProcessCatFilter(s, vars)
        self._ReformatLists(s)
        return s

    def _ProcessDefaults(self, settings, vars):
        """
        Process all variables from the vars.

        Parameters:
        - settings(SiteSettings), the settings to modify
        - vars is a dict { var_name: value }, the new values to use
        
        If a variable is defined in the SiteSettings instance,
        it's value is used. Otherwise the default is left intact.
        
        Variables not declared in SiteSettings are ignored: we do not inject
        unknown variables.
        
        """
        for k in settings.__dict__.iterkeys():
            try:
                settings.__dict__[k] = vars[k]
            except KeyError:
                pass  # preserve defaults from SiteSettings.__init__

    def _ProcessSources(self, settings, vars):
        """
        Process all "sources" variables from vars and builds the
        sources_list in the SiteSettings.

        Parameters:
        - settings(SiteSettings), the settings to modify
        - vars is a dict { var_name: value }, the new values to use.
        """
        re_def = re.compile(r"^\s*(?P<type>[a-z_]+?)\s*[:=]\s*(?P<path>[^\",]+?|\"[^\"]+?\")\s*(?:$|,(?P<rest>.*))?$")
        type_class = { "dir":  SourceDirReader,  "dirs":  SourceDirReader,
                       "file": SourceFileReader, "files": SourceFileReader }
        source_settings_keys = SourceSettings().KnownKeys()
        for k, value in vars.iteritems():
            if k.startswith("sources"):
                curr_source_settings = SourceSettings()
                old = None
                while value and old != value:
                    old = value
                    m = re_def.match(value)
                    if not m:
                        self._log.Error("Invalid source in '%s'", value)
                        break
                    value = m.group("rest")
                    type = m.group("type")
                    path = m.group("path")
                    if path.startswith('"'):
                        assert path.endswith('"')
                        path = path[1:-1]
                    if type == "all":
                        for t in ["dirs", "files"]:  # TODO: add support for "izu items"
                            settings.source_list.append(type_class[t](self._log, settings, path,
                                                                      source_settings=curr_source_settings))
                    elif type in type_class:
                        settings.source_list.append(type_class[type](self._log, settings, path,
                                                                      source_settings=curr_source_settings))
                    elif type in source_settings_keys:
                        curr_source_settings.__dict__[type] = path
                    else:
                        self._log.Error("Unknown source type '%s' in '%s'",
                                        type,
                                        m.group(0))
        self._log.Info("[%s] Sources: %s",
                       settings.public_name,
                       ",".join([repr(s) for s in settings.source_list]))

    def _ProcessCatFilter(self, s, vars):
        """
        Processes a "cat_filter" variable from the settings and builds the
        corresponding cat_exclude and cat_include lists in the site's defaults.
        """
        s.cat_include, s.cat_exclude = self._ProcessFilter(
                                   "cat_filter", vars.get("cat_filter", None))

    def _ProcessFilter(self, name, words):
        """
        Processes a "filter" variable from the settings and builds the
        corresponding cat_exclude and cat_include lists in the site's defaults.
        
        Exclusions are matched using a "OR". Inclusions are matched using a "OR" too.
        The "all" exclusion trumps everything else.
        The "all" inclusion trumps all other inclusions.
        """
        _ALL = SiteSettings.CAT_ALL
        _NOTAG = SiteSettings.CAT_NOTAG
        _EXCLUDE = SiteSettings.CAT_EXCLUDE
        cat_exclude = {}
        cat_include = {}
        if words:
            # split on whitespace or comma
            # categories are case insensitive
            words = _CAT_FILTER_SEP.split(words.lower())
        if not words:
            return (None, None)
        for word in words:
            if not word:
                continue
            if word.startswith(_EXCLUDE) and cat_exclude != _ALL:
                exc = word[1:]
                if not exc or exc == _EXCLUDE:
                    self._log.Error("Invalid '%s' word '%s'. Valid exclude "
                                    "patterns are !* (exclude all), !$ (exclude non-tagged) "
                                    "or !word (exclude 'word')", name, word)
                    continue
                if exc == _ALL:
                    # Shortcut for a site that excludes everything... we're done!
                    cat_exclude = exc
                    cat_include = None
                    return (cat_include, cat_exclude)
                else:
                    cat_exclude[exc] = True
            elif cat_include != _ALL:
                if word == _ALL:
                    cat_include = word
                else:
                    cat_include[word] = True
        if not cat_include or cat_include == _ALL:
            cat_include = None
        if not cat_exclude:
            cat_exclude = None
        return (cat_include, cat_exclude)

    def _ReformatLists(self, s):
        """
        Some variables are lists. Transform the string, which was read from
        the pref file, to an actual python list of strings.
        """
        s.toc_categories = self._SplitCatList(s.toc_categories)
        s.reverse_categories = self._SplitCatList(s.reverse_categories)

    def _SplitCatList(self, string):
        """
        Transform the input string into a list of strings.
        If the input is none or empty, returns an empty list.
        
        List word separators are whitespace and comma.
        The words are made all lower case (for category names).
        """
        a = []
        if string:
            a = [w for w in _CAT_FILTER_SEP.split(string.strip().lower()) if w]
        return a

#------------------------
# Local Variables:
# mode: python
# tab-width: 4
# py-continuation-offset: 4
# py-indent-offset: 4
# sentence-end-double-space: nil
# fill-column: 79
# End:
