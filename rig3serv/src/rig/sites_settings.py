#!/usr/bin/python
#-----------------------------------------------------------------------------|
"""
Rig3 module: Settings for top-level sites definitions.

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

import re
import ConfigParser
from rig.settings_base import SettingsBase
from rig.source_item import SourceSettings
from rig.source_reader import SourceDirReader, SourceFileReader, SourceBlogReader
from rig.site_base import DEFAULT_THEME
from rig.hashable import Hashable

_CAT_FILTER_SEP = re.compile("[, \t\f]")

DEFAULT_ITEMS_PER_PAGE = 20  # Default for settings.num_item_index and settings.num_item_atom


#------------------------
class IncludeExclude(Hashable):
    ALL = "*"
    NOTAG = "$"
    EXCLUDE = "!"

    def __init__(self, include=None, exclude=None):
        super(IncludeExclude, self).__init__()
        self._include = include
        self._exclude = exclude

    def Matches(self, cats):
        """
        For the given list of categories that apply to a post, check if they
        match against the current include/exclude list: if one is excluded,
        the whole thing is rejected. They must all be included for it to match.

        Returns true if it matches.
        """
        # First apply exclusions... the first match makes the test fail
        exc = self._exclude
        if exc == IncludeExclude.ALL:
            return False  # everything is excluded
        elif exc:
            if not cats and IncludeExclude.NOTAG in exc:
                return False  # exclude posts with no tags
            for cat in cats:
                if cat in exc:
                    return False  # some word is excluded

        # Then process inclusions... one of them must be there.
        inc = self._include
        if not inc or inc == IncludeExclude.ALL:
            return True  # default is to match everything
        if not cats and IncludeExclude.NOTAG in inc:
            return True  # include posts with no tags
        for cat in cats:
            if cat in inc:
                return True  # some word is included
        return False  # no inclusion worked

    def Filter(self, all_cats):
        """
        For a given list of all possible categories, start with those that
        can be included, then removes what needs to be excluded.

        Returns a list(str) of all what matches. The list can be empty but
        not none.
        """
        exc = self._exclude
        if exc == IncludeExclude.ALL:
            return [] # everything is excluded

        inc = self._include
        if not inc or inc == IncludeExclude.ALL or IncludeExclude.NOTAG in inc:
            # default is to accept everything
            result = list(all_cats)
        else:
            # apply inclusions
            result = [c for c in all_cats if c in inc]

        if exc:
            result = [c for c in result if not c in exc]

        return result

    def __contains__(self, cat):
        return cat in self.Filter([ cat ])

    def Set(self, name, words):
        """
        Processes a "filter" variable from the settings and builds the
        corresponding include/exclude list in the site's defaults.

        Exclusions are matched using a "OR". Inclusions are matched using a "OR" too.
        The "all" exclusion trumps everything else.
        The "all" inclusion trumps all other inclusions.
        """
        _ALL = IncludeExclude.ALL
        _NOTAG = IncludeExclude.NOTAG
        _EXCLUDE = IncludeExclude.EXCLUDE
        default_exclude = self._exclude
        default_include = self._include
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
                    self._exclude = exc
                    self._include = None
                    return
                else:
                    cat_exclude[exc] = True
            elif cat_include != _ALL:
                if word == _ALL:
                    cat_include = word
                else:
                    cat_include[word] = True

        # reset defaults
        if not cat_include:
            if default_include == _ALL:
                cat_include = _ALL
            else:
                cat_include = None
        if not cat_exclude:
            if not cat_include and default_exclude == _ALL:
                cat_exclude = _ALL
            else:
                cat_exclude = None

        self._exclude = cat_exclude
        self._include = cat_include

    def __repr__(self):
        return "<%s: Inc=%s, Exc=%s>" % (self.__class__.__name__, self._include, self._exclude)

    def RigHash(self, md=None):
        md = self.UpdateHash(md, self._include)
        md = self.UpdateHash(md, self._exclude)
        return md


#------------------------
class SiteSettings(object):
    """
    Settings for one site with defaults:
    - public_name (str): Site name, as published on the generated page. Free text.
    - source_list (list SourceBase): List of SourceBase readers
    - dest_dir (str): Path of where to generate content. Can be relative or absolute.
    - cache_dir (str): Path the temp content cache. Can be relative or absolute.
    - theme (str): Name of the theme to use, must match a directory in templates.
    - template_dir (str): Path of the templates directory. Can be relative or absolute.
    - base_url (str): URL where the site will be published, in case templates wants to use that.
    - rig_album_url(string): Declares how to generate a link to a given RIG album.
        rig_album_url=%(rig_base)s?album=%(album)s
    - rig_img_url(string): Declares how to generate a text link to a given RIG image _page_.
    - rig_img_size(int): 512, the default size of a [rigimg] tag in Izumi
        rig_img_url=%(rig_base)s?album=%(album)s&img=%(img)s
    - rig_thumb_url(string): Declares how to generate an IMG reference to a give RIG image.
        rig_thumb_url=%(rig_base)s?th=&album=%(album)s&img=%(img)s&sz=%(size)s&q=75
    - header_img_url (str): Full URL for the header image. If not present, the default one from
      the theme will be used.
    - header_img_height (int): The height of the header_img. Default is 185.
    - cat_filter(IncludeExclude): An inclusion-exclusion list.
    - img_gen_script (string): An optional script to execute to generate images
    - num_item_page (int): Number of items per HTML page. Default is 20. Must be > 0.
    - num_item_atom (int): Number of items in ATOM feed. Default is 20. -1 for all.
    - html_header (string): Path to HTML header. Default is "html_header.html"
    - toc_categories(IncludeExclude): An inclusion-exclusion list of categories for
                   which to insert a TOC to their pages.
                   Default is none of them.
    - reverse_categories(IncludeExclude): An inclusion-exclusion list of categories
                   to display in reverse date order (i.e. incremental).
                   Default is to display in decrementing date.
    - blog_file_pattern (string): Regex for files valid as blog entries.
    - blog_dir_pattern (string): Regex for directories valid as blog entries.
    - blog_dir_valid_files (string): Regex for accepted files inside a blog directory entry.
    - mangled_name_len (int): Max length of blog entries. Titles which are longer
        than this length are mangled with a hash to make them unique. Set to 0
        to deactivate.
    - use_curr_month_in_index (boolean): True if index should use current month
    - date_ymd_pattern: The compiled regex to find date & title in an album name.
                   See SiteDefault._DATE_YMD for the default and the required
                   syntax (especially the named regex groups).
    - img_pattern: The compiled regex to find images and their rating.
                   See SiteDefault._IMG_PATTERN for the default and the required
                   syntax (especially the named regex groups).
    - dup_on_realpath(bool): When true, use real path of source entries to de-dup
                   *regardless* of the various source settings.
    - enable_sharing(bool): When true, add links to share posts to Facebook, twitter, etc.
    - index_exclude(str): An inclusion-exclusion list of categories to exclude from
                    the generic "all recents items" page.
    - encoding(str): Encoding of Izu/HTML text files. Default is Latin-1 (ISO-8859-1).
                     Can be overridden per source.
    """
    def __init__(self,
                 public_name="",
                 source_list=[],
                 dest_dir=None,
                 cache_dir=None,
                 theme=DEFAULT_THEME,
                 template_dir=None,
                 base_url=None,
                 rig_album_url="%(rig_base)s?album=%(album)s",
                 rig_img_url="%(rig_base)s?album=%(album)s&img=%(img)s",
                 rig_thumb_url="%(rig_base)s?th=&album=%(album)s&img=%(img)s&sz=%(size)s&q=75",
                 rig_img_size=512,
                 header_img_url="",
                 header_img_height=185,
                 tracking_code="",
                 cat_filter=IncludeExclude(IncludeExclude.ALL, None),
                 img_gen_script="",
                 num_item_page=DEFAULT_ITEMS_PER_PAGE,
                 num_item_atom=DEFAULT_ITEMS_PER_PAGE,
                 html_header="html_header.html",
                 toc_categories=IncludeExclude(None, IncludeExclude.ALL),
                 reverse_categories=IncludeExclude(None, IncludeExclude.ALL),
                 blog_file_pattern=None,
                 blog_dir_pattern=None,
                 blog_dir_valid_files=None,
                 mangled_name_len=50,
                 use_curr_month_in_index=True,
                 date_ymd_pattern=None,
                 img_pattern=None,
                 dup_on_realpath=False,
                 youtube_html="""<object width="%(sx)s" height="%(sy)s">
<param name="movie" value="http://www.youtube-nocookie.com/v/%(id)s&hl=en&fs=1&rel=0&color1=0x234900&color2=0x4e9e00%(url_extra)s"></param>
<param name="allowFullScreen" value="true"></param>
<param name="allowscriptaccess" value="always"></param>
<embed src="http://www.youtube-nocookie.com/v/%(id)s&hl=en&fs=1&rel=0&color1=0x234900&color2=0x4e9e00" type="application/x-shockwave-flash" allowscriptaccess="always" allowfullscreen="true" width="%(sx)s" height="%(sy)s"></embed>
</object>""",
                 youtube_sx="640",
                 youtube_sy="385",
                 enable_sharing=False,
                 index_exclude=IncludeExclude(IncludeExclude.ALL, None),
                 encoding="iso-8859-1"
                 ):
        # Note: this is *always* called using the default values defined in the
        # constructor. If you need to change a setting loaded from an RC file,
        # use SetFinished() instead.
        self.public_name = public_name
        self.source_list = source_list or []
        self.dest_dir = dest_dir
        self.cache_dir = cache_dir
        self.theme = theme
        self.template_dir = template_dir
        self.base_url = base_url
        self.rig_album_url = rig_album_url
        self.rig_img_url = rig_img_url
        self.rig_thumb_url = rig_thumb_url
        self.rig_img_size = int(rig_img_size)
        self.header_img_url = header_img_url
        self.header_img_height = int(header_img_height)
        self.tracking_code = tracking_code
        self.cat_filter = cat_filter
        self.img_gen_script = img_gen_script
        self.num_item_page = int(num_item_page)
        self.num_item_atom = int(num_item_atom)
        self.html_header = html_header
        self.reverse_categories = reverse_categories
        self.toc_categories = toc_categories
        self.blog_file_pattern = blog_file_pattern
        self.blog_dir_pattern = blog_dir_pattern
        self.blog_dir_valid_files = blog_dir_valid_files
        self.mangled_name_len = mangled_name_len
        self.use_curr_month_in_index = self.ParseBool(use_curr_month_in_index)
        self.date_ymd_pattern = None
        if date_ymd_pattern:
            self.date_ymd_pattern = re.compile(date_ymd_pattern)
        self.img_pattern = None
        if img_pattern:
            self.img_pattern = re.compile(img_pattern)
        self.dup_on_realpath = self.ParseBool(dup_on_realpath)
        self.youtube_html = youtube_html
        self.youtube_sx = youtube_sx
        self.youtube_sy = youtube_sy
        self.enable_sharing = self.ParseBool(enable_sharing)
        self.index_exclude = index_exclude;
        self.encoding = encoding

    def AsDict(self):
        """
        Returns a copy of the settings' dictionary.
        It's safe for caller to modify this dictionary.
        """
        return dict(self.__dict__)

    def FromDict(self, keywords):
        """
        Set all known settings to the values defined in the keywords dictionary.
        """
        for k in self.__dict__.iterkeys():
            if k in keywords:
                self.__dict__[k] = keywords[k]

    def Set(self, key, new_value):
        """
        Sets a value in this SiteSettings.
        This correctly matches the new value to the expected internal type.

        - key (str): the name of the value to set
        - new_value (any): the value to set.
        """
        value = self.__dict__[key]
        if isinstance(value, IncludeExclude):
            value.Set(key, new_value)
        elif isinstance(value, bool):
            # Note: must test bool before int because a bool is also an int!
            value = self.ParseBool(new_value)
        elif isinstance(value, int):
            value = int(new_value)
        elif isinstance(value, (str, unicode, type(None))):
            value = str(new_value)
        elif isinstance(value, list):
            value = list(new_value)
        else:
            raise TypeError("Invalid type for setting %s: expected %s, got %s" %
                            (key, type(value), type(new_value) ))
        self.__dict__[key] = value

    def SetFinished(self):
        """
        Called once all settings have been set using Set(). This gives us
        a last chance to edit/correct/check some settings.
        """
        # We automatically add a / to the base_url if it needs to.
        # A rare case where this might be unwanted is in case the URL has cgi params.
        if self.base_url and \
                not self.base_url.endswith("/") and \
                not "?" in self.base_url:
            self.base_url += "/"

    def ParseBool(self, value):
        """
        Parses a value and interprets it as a boolean.
        If value is a bool type, returns the value itself.
        If value is a string, returns true if the string.lower is "1" or "true".
        """
        if isinstance(value, bool):
            return value
        if isinstance(value, (str, unicode)):
            return value.lower() in [ "1", "true" ]
        return False

    def __repr__(self):
        try:
            return "[%s: %s]" % (self.__class__.__name__, self.__dict__)
        except:
            return super(SiteSettings, self).__repr__()


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
        self._log.Debug("Site Settings: %s", vars)
        self._ProcessDefaults(s, vars)
        self._ProcessSources(s, vars)
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
            if k in vars:
                settings.Set(k, vars[k])
        settings.SetFinished()

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
                       "file": SourceFileReader, "files": SourceFileReader,
                       "blog": SourceBlogReader,
                      }
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
                    if type in type_class:
                        settings.source_list.append(
                            type_class[type](self._log,
                                             site_settings=settings,
                                             source_settings=curr_source_settings,
                                             path=path))
                    elif type in source_settings_keys:
                        curr_source_settings.__dict__[type] = path
                    else:
                        self._log.Error("Unknown source type '%s' in '%s'",
                                        type,
                                        m.group(0))
        self._log.Info("[%s] Sources: %s",
                       settings.public_name,
                       ",".join([repr(s) for s in settings.source_list]))


#------------------------
# Local Variables:
# mode: python
# tab-width: 4
# py-continuation-offset: 4
# py-indent-offset: 4
# sentence-end-double-space: nil
# fill-column: 79
# End:
