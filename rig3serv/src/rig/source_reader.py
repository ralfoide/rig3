#!/usr/bin/python
#-----------------------------------------------------------------------------|
"""
Rig3 module: One-line module description

Note: SourceReaderBase derived classes defined here are created in SitesSettings._ProcessSources()

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

import codecs
import os
import re
from binascii import crc32
from datetime import datetime

from rig.source_item import SourceDir, SourceFile, SourceContent
from rig.parser.dir_parser import DirParser, RelFile, PathTimestamp
from rig.parser.izu_parser import IzuParser


#------------------------
class SourceReaderBase(object):
    """
    Base class for a source reader, i.e. an object that knows how to read
    "items" out of files or directories on disk. These items (...TODO...)

    The constructor captures the current site settings and the default source
    path. The settings are used for specific configuration, for example
    filtering patterns.
    """
    def __init__(self, log, site_settings, source_settings, path):
        self._log = log
        self._path = path
        self._site_settings = site_settings
        self._source_settings = source_settings

    def GetPath(self):
        return self._path

    def Parse(self, dest_dir):
        """
        Parses the source and returns a list of SourceItem.
        The source directory is always the internal path given to the
        constructor of the source reader.

        Parameter:
        - dest_dir (string): Destination directory.

        This method is abstract and must always be implemented by derived
        classes. Derived classes should not call their super.
        """
        raise NotImplementedError("Must be derived by subclasses")

    def __eq__(self, rhs):
        """
        Two readers are equal if they have the same type, the same path
        and the same site_settings.
        """
        if isinstance(rhs, SourceReaderBase):
            return (type(self) == type(rhs) and
                    self._path == rhs._path and
                    self._site_settings == rhs._site_settings)
        else:
            return False

    def __repr__(self):
        return "<%s '%s'>" % (self.__class__.__name__, self._path)


#------------------------
class SourceBlogReader(SourceReaderBase):
    """
    Source reader for rig3 blog entries (both directory and file entries).
    """

    DIR_PATTERN = re.compile(r"^(\d{4}[-]?\d{2}(?:[-]?\d{2})?)[ _-] *(?P<name>.*) *$")
    DIR_VALID_FILES = re.compile(r"\.(?:izu|jpe?g|html)$")
    FILE_PATTERN = re.compile(r"^(\d{4}[-]?\d{2}(?:[-]?\d{2})?)[ _-] *(?P<name>.*) *\.(?P<ext>izu|html)$")
    OLD_IZU_PATTERN = re.compile(r"^(?P<cat>.+?)\.old\.izu$")

    def __init__(self, log, site_settings, source_settings, path):
        """
        Constructs a new SourceBlogReader.

        Arguments:
        - log (Log)
        - site_settings (SiteSettings)
        - path (String): The base directory to read recursively
        - source_settings(SourceSettings)
        """
        super(SourceBlogReader, self).__init__(log, site_settings, source_settings, path)
        # allow patterns to be overridden via site settings
        self._dir_pattern     = site_settings and site_settings.blog_dir_pattern     or self.DIR_PATTERN
        self._dir_valid_files = site_settings and site_settings.blog_dir_valid_files or self.DIR_VALID_FILES
        self._file_pattern    = site_settings and site_settings.blog_file_pattern    or self.FILE_PATTERN

    def Parse(self, dest_dir):
        """
        Calls the directory parser on the source vs dest directories.

        Then traverses the source tree and generates new items as needed.

        An item in a RIG site is a directory that contains either an
        index.izu and/or JPEG images.

        Parameter:
        - dest_dir (string): Destination directory.

        Returns a list of SourceItem.
        """
        tree = DirParser(self._log).Parse(os.path.realpath(self.GetPath()),
                                          os.path.realpath(dest_dir))

        dir_pattern = re.compile(self._dir_pattern)
        dir_valid_files = re.compile(self._dir_valid_files)
        file_pattern = re.compile(self._file_pattern)

        items = []
        for source_dir, dest_dir, all_files in tree.TraverseDirs():
            basename = source_dir.basename()

            if dir_pattern.match(basename):
                # This directory looks like one entry.
                # Only keep the "valid" files for directory entries.
                valid_files = [f for f in all_files if dir_valid_files.search(f)]


                # Only process directories that have at least one file of interest
                if valid_files:
                    self._log.Debug("[%s] Process '%s' to '%s'",
                                    self._site_settings and self._site_settings.public_name or "[Unnamed Site]",
                                   source_dir.rel_curr, dest_dir.rel_curr)

                    date = datetime.fromtimestamp(self._DirTimeStamp(source_dir.abs_path))
                    item = SourceDir(date, source_dir, all_files, self._source_settings)
                    items.append(item)
            else:
                # Not a directory entry, so check individual files to see if they
                # qualify as individual entries
                for f in all_files:
                    m = self.OLD_IZU_PATTERN.match(f)
                    if m:
                        rel_file = RelFile(source_dir.abs_base,
                                           os.path.join(source_dir.rel_curr, f))
                        self._ParseOldIzu(rel_file, m.group("cat"), items)

                    elif file_pattern.match(f):
                        rel_file = RelFile(source_dir.abs_base,
                                           os.path.join(source_dir.rel_curr, f))
                        date = datetime.fromtimestamp(self._FileTimeStamp(rel_file.abs_path))
                        item = SourceFile(date, rel_file, self._source_settings)
                        items.append(item)
                        self._log.Debug("[%s] Append item '%s'", item)

        return items


    _RE_OLD_IZU_HEADER = re.compile(r"^\[s:(?P<year>\d{4})(?P<month>\d{2})(?P<day>\d{2}):(?P<title>[^\]]*).*$")

    # An inter-izumi named link: [label|page/subpage#s:YYYYMMDD:title], without [[
    # title is optional and date must be 8-digits.
    _RE_INTER_IZU_LINK = re.compile(r"(?<!\[)\[(?P<label>[^\|\]]+)\|(?P<page>[^#:|\]]+)#s:(?P<date>[0-9]{8})(?::(?P<title>[^\]]+))?\]")


    def _ParseOldIzu(self, rel_file, cat, items):
        """
        """

        SEP = "----"

        if self._source_settings.encoding:
            encoding = self._source_settings.encoding
        else:
            encoding = self._site_settings.encoding

        # First line must have some izu tags
        tags = IzuParser(self._log, None, None).ParseFileFirstLine(rel_file.abs_path, encoding)

        # If we find an encoding tag, reparse the tags using that encoding
        if "encoding" in tags:
            tags = IzuParser(self._log, None, None).ParseFileFirstLine(rel_file.abs_path, encoding)

        f = codecs.open(rel_file.abs_path, mode="rU",
                        encoding=encoding,
                        errors="xmlcharrefreplace")
        # Skip to the first section
        for line in f:
            if line.strip() == SEP:
                break

        # Use the category based on the filename if there's no override in the file tags
        if not "cat" in tags:
            tags["cat"] = { cat: True }

        izumi_base_url = tags.get("izumi_base_url", None)
        if izumi_base_url and not izumi_base_url.endswith("/"):
            izumi_base_url += "/"

        content = None
        date = None
        title = None
        for line in f:
            if isinstance(line, unicode):
                # Internally we only process ISO-8859-1 and replace
                # unknown entities by their XML hexa encoding
                line = line.encode("iso-8859-1", "xmlcharrefreplace")

            if line.strip() == SEP:
                continue

            elif line.startswith("[s:"):
                # Flush content
                if content:
                    # Inject date in tags
                    tags = dict(tags)
                    tags["date"] = date
                    item = SourceContent(date, rel_file, title, content, tags, self._source_settings)
                    items.append(item)
                    self._log.Debug("[%s] Append item '%s'", item)

                content = ""
                date = None
                title = None

                m = self._RE_OLD_IZU_HEADER.match(line)
                if m:
                    date = datetime(
                                 int(m.group("year")),
                                 int(m.group("month")),
                                 int(m.group("day")))
                    title = m.group("title")

            elif date and title:
                if "#s" in line and not "|#s" in line:
                    pass
                if izumi_base_url:
                    # Convert old inter-izumi links into hard URLs (e.g. only links
                    # from one izumi page to another. This does not affect intra-izumi
                    # links inside the same category, as those will be supported by
                    # rig3 directly.)
                    line = self._RE_INTER_IZU_LINK.sub(
                               lambda m: self._ConvertInterIzuLinks(m, izumi_base_url), line)

                content += line

        if content:
            # Inject date in tags
            tags = dict(tags)
            tags["date"] = date
            # Flush content
            item = SourceContent(date, rel_file, title, content, tags, self._source_settings)
            items.append(item)
            self._log.Debug("[%s] Append item '%s'", item)

        f.close()

    def _ConvertInterIzuLinks(self, m, izumi_base_url):
        label = m.group("label")
        date  = m.group("date")
        title = m.group("title")
        page  = m.group("page")

        # Compute the same key than RBlog::BlogEntryKey from izumi.sourforge.net
        # see http://izumi.cvs.sourceforge.net/viewvc/izumi/izumi/src/RBlog.php?view=markup&pathrev=HEAD
        # at line 348.
        if title:
            key = title.lower()
            key = re.sub(r"[ \-_=+\[\]{};:'\",./<>?`~!@#$%^&*()\\|]", "_", key)
            key = re.sub(r"[^0123456789abcdefghijklmnopqrstuvwxyz_]", "", key)
            key = date + "_" + key
            if len(key) > 32:
                # shorten with a crc32
                key = "%s_%x" % (key[0:23], crc32(date + title))
        else:
            key = date

        return "[%s|%s%s?s=%s]" % (label, izumi_base_url, page, key)


    # Utilities, overridable for unit tests

    def _DirTimeStamp(self, dir):
        """
        Returns the most recent change or modification time stamp for the
        given directory.

        Throws OSError with e.errno==errno.ENOENT (2) when the directory
        does not exists.
        """
        c = os.path.getctime(dir)
        m = os.path.getmtime(dir)
        return max(c, m)

    def _FileTimeStamp(self, file):
        """
        Returns the most recent change or modification time stamp for the
        given file.

        Throws OSError with e.errno==errno.ENOENT (2) when the file
        does not exists.
        """
        c = os.path.getctime(file)
        m = os.path.getmtime(file)
        return max(c, m)



#------------------------
class SourceDirReader(SourceReaderBase):
    """
    Source reader for rig3 directory-based entries.

    Only directories are considered as items: valid directory names must match
    the specified DIR_PATTERN regexp *and* must contain one or more of the files
    specified by the VALID_FILES regexp.

    @deprecated use SourceBlogReader instead
    """

    DIR_PATTERN = re.compile(r"^(\d{4}[-]?\d{2}(?:[-]?\d{2})?)[ _-] *(?P<name>.*) *$")
    VALID_FILES = re.compile(r"\.(?:izu|jpe?g|html)$")

    def __init__(self, log, site_settings, source_settings, path):
        """
        Constructs a new SourceDirReader.

        Arguments:
        - log (Log)
        - site_settings (SiteSettings)
        - path (String): The base directory to read recursively
        - source_settings(SourceSettings)
        """
        # TODO: the patterns must be overridable via site settings
        super(SourceDirReader, self).__init__(log, site_settings, source_settings, path)

    def Parse(self, dest_dir):
        """
        Calls the directory parser on the source vs dest directories
        with the default dir/file patterns.

        Then traverses the source tree and generates new items as needed.

        An item in a RIG site is a directory that contains either an
        index.izu and/or JPEG images.

        Parameter:
        - dest_dir (string): Destination directory.

        Returns a list of SourceItem.
        """
        tree = DirParser(self._log).Parse(os.path.realpath(self.GetPath()),
                                          os.path.realpath(dest_dir),
                                          file_pattern=self.VALID_FILES,
                                          dir_pattern=self.DIR_PATTERN)

        items = []
        for source_dir, dest_dir, all_files in tree.TraverseDirs():
            if all_files:
                # Only process directories that have at least one file of interest
                self._log.Debug("[%s] Process '%s' to '%s'",
                                self._site_settings and self._site_settings.public_name or "[Unnamed Site]",
                               source_dir.rel_curr, dest_dir.rel_curr)
                if self._UpdateNeeded(source_dir, dest_dir, all_files):
                    date = datetime.fromtimestamp(self._DirTimeStamp(source_dir.abs_path))
                    item = SourceDir(date, source_dir, all_files, self._source_settings)
                    items.append(item)
        return items


    # Utilities, overridable for unit tests

    def _UpdateNeeded(self, source_dir, dest_dir, all_files):
        """
        The item needs to be updated if the source directory or any of
        its internal files are more recent than the destination directory.
        And obviously it needs to be created if the destination does not
        exist yet.

        Arguments:
        - source_dir: DirParser.RelDir (abs_base + rel_curr + abs_dir)
        - dest_dir: DirParser.RelDir (abs_base + rel_curr + abs_dir)
        """
        # TODO: This needs to be revisited. Goal is to have a per-site "last update timestamp"
        # and compare to this.
        return True

        #if not os.path.exists(dest_dir.abs_path):
        #    return True
        #source_ts = None
        #dest_ts = None
        #try:
        #    dest_ts = self._DirTimeStamp(dest_dir.abs_path)
        #except OSError:
        #    self._log.Info("[%s] Dest '%s' does not exist", self._site_settings.public_name,
        #                   dest_dir.abs_path)
        #    return True
        #try:
        #    source_ts = self._DirTimeStamp(source_dir.abs_path)
        #except OSError:
        #    self._log.Warn("[%s] Source '%s' does not exist", self._site_settings.public_name,
        #                   source_dir.abs_path)
        #    return False
        #return source_ts > dest_ts

    def _DirTimeStamp(self, dir):
        """
        Returns the most recent change or modification time stamp for the
        given directory.

        Throws OSError with e.errno==errno.ENOENT (2) when the directory
        does not exists.
        """
        c = os.path.getctime(dir)
        m = os.path.getmtime(dir)
        t = PathTimestamp(dir)
        return max(c, m, t)


#------------------------
class SourceFileReader(SourceReaderBase):
    """
    Source reader for file-based entries.

    Only files which name match the specified FILE_PATTERN regexp are considered valid.

    @deprecated use SourceBlogReader instead
    """

    FILE_PATTERN = re.compile(r"^(\d{4}[-]?\d{2}(?:[-]?\d{2})?)[ _-] *(?P<name>.*) *\.(?P<ext>izu|html)$")

    def __init__(self, log, site_settings, source_settings, path):
        """
        Constructs a new SourceDirReader.

        Arguments:
        - log (Log)
        - site_settings (SiteSettings)
        - path (String): The base directory to read recursively
        - source_settings(SourceSettings)
        """
        # TODO: the patterns must be overridable via site settings
        super(SourceFileReader, self).__init__(log, site_settings, source_settings, path)

    def Parse(self, dest_dir):
        """
        Calls the directory parser on the source vs dest directories
        with the default dir/file patterns.

        Then traverses the source tree and generates new items as needed.

        An item in a RIG site is a file if it matches the given file pattern.

        Parameter:
        - dest_dir (string): Destination directory.

        Returns a list of SourceItem.
        """
        tree = DirParser(self._log).Parse(os.path.realpath(self.GetPath()),
                                          os.path.realpath(dest_dir),
                                          file_pattern=self.FILE_PATTERN)

        items = []
        for source_dir, dest_dir, all_files in tree.TraverseDirs():
            self._log.Debug("[%s] Process '%s' to '%s'",
                            self._site_settings and self._site_settings.public_name or "[Unnamed Site]",
                           source_dir.rel_curr, dest_dir.rel_curr)
            for file in all_files:
                if self.FILE_PATTERN.search(file):
                    rel_file = RelFile(source_dir.abs_base,
                                       os.path.join(source_dir.rel_curr, file))
                    if self._UpdateNeeded(rel_file, dest_dir):
                        date = datetime.fromtimestamp(self._FileTimeStamp(rel_file.abs_path))
                        item = SourceFile(date, rel_file, self._source_settings)
                        items.append(item)
        return items

    def _UpdateNeeded(self, source_file, dest_dir):
        # TODO: This needs to be revisited. Goal is to have a per-site "last update timestamp"
        # and compare to this.
        return True

    def _FileTimeStamp(self, file):
        """
        Returns the most recent change or modification time stamp for the
        given file.

        Throws OSError with e.errno==errno.ENOENT (2) when the file
        does not exists.
        """
        c = os.path.getctime(file)
        m = os.path.getmtime(file)
        return max(c, m)


#------------------------
# Local Variables:
# mode: python
# tab-width: 4
# py-continuation-offset: 4
# py-indent-offset: 4
# sentence-end-double-space: nil
# fill-column: 79
# End:
