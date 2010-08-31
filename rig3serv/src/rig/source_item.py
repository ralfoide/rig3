#!/usr/bin/python
#-----------------------------------------------------------------------------|
"""
Rig3 module: One-line module description

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

from rig.hashable import Hashable


#------------------------
class SourceSettings(Hashable):
    """
    Settings attached to a specific source.

    Current settings that can be overridden per source:
    - rig_base(str): Base URL for rig1 for generating rig1 image links.
    - encoding(str): Text encoding of Izu/HTML files for the source.
                     When set, overrides the global settings' encoding
                     which is Latin-1 (ISO-8859-1) by default.
    """
    def __init__(self, rig_base=None, encoding=None):
        super(SourceSettings, self).__init__()
        self.rig_base = rig_base
        self.encoding = encoding

    def AsDict(self):
        """
        Returns a copy of the settings' dictionary.
        It's safe for caller to modify this dictionary.
        """
        return dict(self.__dict__)

    def KnownKeys(self):
        """
        List the variables declared by this SourceSettings
        """
        keys = self.__dict__.keys()
        keys.sort()
        return keys

    def __eq__(self, rhs):
        return (isinstance(rhs, SourceSettings) and self.__dict__ == rhs.__dict__)

    def RigHash(self, md=None):
        return self.UpdateHash(md, self.__dict__)

    def __repr__(self):
        try:
            return "[%s: %s]" % (self.__class__.__name__, self.__dict__)
        except:
            return super(SourceSettings, self).__repr__()


#------------------------
class SourceItem(Hashable):
    """
    Abstract base class to represents an item:
    - list of categories (list of string)
    - date (datetime)
    - source_settings (not optional)

    The class is conceptually abstract, meaning it has no data.
    In real usage, clients will process derived classes (e.g. SourceDir)
    which have members with actual data to process.
    """
    def __init__(self, date, source_settings, categories=None):
        super(SourceItem, self).__init__()
        self.date = date
        self.source_settings = source_settings
        self.categories = categories or []

    def __eq__(self, rhs):
        return (isinstance(rhs, SourceItem) and
                self.date == rhs.date and
                self.source_settings == rhs.source_settings and
                self.categories == rhs.categories)

    def __ne__(self, rhs):
        return not self.__eq__(rhs)

    def RigHash(self, md=None):
        """
        Computes a hash that depends on the real path of the item *and*
        its source settings.
        """
        md = self.UpdateHash(md, self.date)
        md = self.UpdateHash(md, self.source_settings)
        md = self.UpdateHash(md, self.categories)
        return md

    def ContentHash(self, md=None):
        """
        Computes a hash that depends on the real path of the item but not
        its source settings.
        """
        return md

    def PrettyRepr(self):
        """
        Returns a "pretty representation" of the item as a string,
        suitable for Log.Info.
        """
        return self.__class__.__name__

#------------------------
class SourceDir(SourceItem):
    """
    Represents a directory item from a SourceDirReader.

    Such a directory generally contains an index.izu or index.html
    and a bunch of image files.

    Parameters:
    - date (datetime): Date of the directory (i.e. most recent item)
    - rel_dir (RelDir): absolute+relative source directory
    - all_files (list [string]): All interesting files in this directory
    """
    def __init__(self, date, rel_dir, all_files, source_settings):
        super(SourceDir, self).__init__(date, source_settings)
        self.rel_dir = rel_dir
        self.all_files = all_files

    def __eq__(self, rhs):
        if not super(SourceDir, self).__eq__(rhs):
            return False
        return (isinstance(rhs, SourceDir) and
                self.rel_dir == rhs.rel_dir and
                self.all_files == rhs.all_files)

    def RigHash(self, md=None):
        """
        Computes a hash that depends on the real path of the directory
        and its inner file list (like ContentHash) but *also* depends on
        the items date, source settings and categories.
        """
        md = super(SourceDir, self).RigHash(md)
        md = self.ContentHash(md)
        return md

    def ContentHash(self, md=None):
        """
        Computes a hash that only depends on the real path of the directory
        and its inner file list.
        """
        md = super(SourceDir, self).ContentHash(md)
        md = self.UpdateHash(md, self.rel_dir.realpath())
        for f in self.all_files:
            md = self.UpdateHash(md, f)
        return md

    def __repr__(self):
        return "<%s (%s) %s, %s, %s, %s>" % (self.__class__.__name__,
                                             self.date,
                                             self.rel_dir,
                                             self.all_files,
                                             self.categories,
                                             self.source_settings)

    def PrettyRepr(self):
        """
        Returns a "pretty representation" of the item as a string,
        suitable for Log.Info, namely the directory relative path.
        """
        return self.rel_dir.rel_curr


#------------------------
class SourceFile(SourceItem):
    """
    Represents a file item from a SourceFileReader.

    Parameters:
    - date (datetime): Date of the file
    - rel_file (RelFile): absolute+relative source file
    - source_settings (not optional)
    """
    def __init__(self, date, rel_file, source_settings):
        super(SourceFile, self).__init__(date, source_settings)
        self.rel_file = rel_file

    def __eq__(self, rhs):
        if not super(SourceFile, self).__eq__(rhs):
            return False
        return (isinstance(rhs, SourceFile) and
                self.rel_file == rhs.rel_file)

    def RigHash(self, md=None):
        """
        Computes a hash that depends on the real path of the file (like
        ContentHash) but *also* depends on the items date, source settings
        and categories.
        """
        md = super(SourceFile, self).RigHash(md)
        md = self.ContentHash(md)
        return md

    def ContentHash(self, md=None):
        """
        Computes a hash that only depends on the real path of the file.
        """
        md = super(SourceFile, self).ContentHash(md)
        md = self.UpdateHash(md, self.rel_file.realpath())
        return md

    def __repr__(self):
        return "<%s (%s) %s, %s, %s>" % (self.__class__.__name__,
                                         self.date,
                                         self.rel_file,
                                         self.categories,
                                         self.source_settings)

    def PrettyRepr(self):
        """
        Returns a "pretty representation" of the item as a string,
        suitable for Log.Info, namely the file relative path.
        """
        return self.rel_file.rel_curr


#------------------------
class SourceContent(SourceItem):
    """
    Represents a file item from a SourceFileReader.

    Parameters:
    - date (datetime): Date of the file
    - rel_file (RelFile): absolute+relative source file
    - source_settings (not optional)
    """
    def __init__(self, date, rel_file, title, content, tags, source_settings):
        super(SourceContent, self).__init__(date, source_settings)
        self.rel_file = rel_file
        self.tags = tags
        self.title = title
        self.content = content

    def __eq__(self, rhs):
        if not super(SourceContent, self).__eq__(rhs):
            return False
        return (isinstance(rhs, SourceContent) and
                    self.tags == rhs.tags  and
                    self.title == rhs.title and
                    self.content == rhs.content and
                    self.rel_file == rhs.rel_file)

    def RigHash(self, md=None):
        """
        Computes a hash that depends on the content (like ContentHash)
        but *also* depends on the source settings and categories.
        """
        md = super(SourceContent, self).RigHash(md)
        md = self.ContentHash(md)
        return md

    def ContentHash(self, md=None):
        """
        Computes a hash that only depends on the content.
        """
        md = super(SourceContent, self).ContentHash(md)
        md = self.UpdateHash(md, self.tags)
        md = self.UpdateHash(md, self.title)
        md = self.UpdateHash(md, self.content)
        md = self.UpdateHash(md, self.rel_file.realpath())
        return md

    def __repr__(self):
        return "<%s (%s) %s, %s, %s>" % (self.__class__.__name__,
                                         self.date,
                                         self.title,
                                         self.tags,
                                         self.source_settings)

    def PrettyRepr(self):
        """
        Returns a "pretty representation" of the item as a string,
        suitable for Log.Info.
        """
        return "%s:%s" % (self.date, self.title)



#------------------------
# Local Variables:
# mode: python
# tab-width: 4
# py-continuation-offset: 4
# py-indent-offset: 4
# sentence-end-double-space: nil
# fill-column: 79
# End:
