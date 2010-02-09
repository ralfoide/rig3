#!/usr/bin/python
# -*- coding: iso-8859-1 -*-
#-----------------------------------------------------------------------------|
"""
Rig3 module: Parses Izumi files to HTML

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
import os
import sys
import fnmatch
import urllib
import subprocess
from datetime import datetime
from StringIO import StringIO

from rig.parser.utf8_accents import UTF8_ACCENTS_TO_HTML
from rig.parser.dir_parser import RelPath

_DATE_YMD = re.compile(r"^(?P<year>\d{4})[:/-]?(?P<month>\d{2})[:/-]?(?P<day>\d{2})"
                       r"(?:[ ,:/-]?(?P<hour>\d{2})[:/.-]?(?P<min>\d{2})(?:[:/.-]?(?P<sec>\d{2}))?)?")

_WS_LINE = re.compile(r"^[ \t\r\n\f]*$")

_IZU_CAT_SEP = re.compile("[, \t\f]")

_ACCENTS_TO_HTML = {
    "á": "&aacute;",
    "à": "&agrave;",
    "â": "&acirc;",
    "ä": "&auml;",
    "ã": "&atilde;",

    "ç": "&ccedil;",

    "é": "&eacute;",
    "è": "&egrave;",
    "ê": "&ecirc;",
    "ë": "&euml;",

    "í": "&iacute;",
    "ì": "&igrave;",
    "î": "&icirc;",
    "ï": "&iuml;",

    "ñ": "&mtilde;",

    "ó": "&oacute;",
    "ò": "&ograve;",
    "ô": "&ocirc;",
    "ö": "&ouml;",
    "õ": "&otilde;",

    "ú": "&uacute;",
    "ù": "&ugrave;",
    "û": "&ucirc;",
    "ü": "&uuml;",

    "°": "&deg;",
}

#------------------------
class _State(object):
    def __init__(self, _file, filename, rel_file):
        self._file = _file
        self._filename = filename
        self._rel_file= rel_file
        self._tags = {}
        self._sections = {}
        self._section_needs_paragraph = {}
        self._curr_section = None
        self._curr_formatter = None

    def Filename(self):
        return self._filename

    def RelFile(self):
        return self._rel_file

    def Tags(self):
        return self._tags

    def CurrSection(self):
        return self._curr_section

    def SetCurrSection(self, curr_section, curr_formatter):
        self._curr_section = curr_section
        self._curr_formatter = curr_formatter

    def SectionNeedsParagraph(self, curr_section):
        return self._section_needs_paragraph.get(curr_section, False)

    def SetSectionNeedsParagraph(self, curr_section, needs_paragraph):
        self._section_needs_paragraph[curr_section] = needs_paragraph

    def CurrFormatter(self):
        return self._curr_formatter

    def Section(self, section):
        return self._sections.get(section, None)

    def InitSection(self, section, default):
        self._sections[section] = self._sections.get(section, default)

    def Append(self, section, content):
        try:
            # lists support append()
            self._sections[section].append(content)
        except AttributeError:
            # strings support +=
            self._sections[section] += content

    def EndsWith(self, section, word):
        return self._sections[section].endswith(word)

    def EndOfFile(self):
        return self._file is None

    def ReadLine(self):
        """
        Reads a line from the input stream. Strips the end-of-line terminator
        if present.

        If the end of the file has been reached, returns None.
        """
        line = None
        if self._file:
            line = self._file.readline()
            if not line:
                self._file = None
                line = None
            else:
                line = line.strip("\r\n")
        return line

    def Close(self):
        """
        Ends usage of the State and returns a tuple that will be returned by
        RenderFiletoHtml.

        Returns tuple(dict: tags, dict: sections)
        """
        # Wrap existing non-empty HTML sessions in the appropriate div
        for k, v in self._sections.iteritems():
            if v and isinstance(v, (str, unicode)):
                self._sections[k] = '<span class="izu">%s</span>' % v
        return self._tags, self._sections


#------------------------
class IzuParser(object):
    """
    Izumi parser.
    This class is stateless.
    """
    def __init__(self, log, rig_base, img_gen_script):
        self._log = log
        self._img_gen_script = img_gen_script
        self._rig_base = rig_base

        # custom section handlers. Unlisted sections use the "default" formatter
        self._escape_block = { "--": self._EscapeComment,
                               "html:": self._EscapeRawHtml }
        self._formatters = { "images": self._ImagesSection,
                             "html":   self._HtmlSection }
        self._tag_handlers = { "cat":  self._CatHandler,
                               "date": self._DateHandler }

    def RenderFileToHtml(self, filestream):
        """
        Parses the file 'filename' and returns an HTML snippet for it.
        Renders a <div> section, not a full single HTML file.

        If source is a string or a RelPath/RelFile, it is considered a path to
        be opened as read-only text.

        Otherwise, it must be a file-like object. Use StringIO if you need to parse
        a string buffer.

        Returns a tuple:
        - dict of izumi header tags (can be an empty list, but not None)
            - most are just srtings. The "cat" (categories) tag is a list of strings.
        - dict of sections.
            - most are HTML content.
            - the "images" section must be a list of RIG urls.
        """
        f = None
        result = None
        try:
            rel_file = None
            if isinstance(filestream, (str, unicode)):
                f = file(filestream, "rU", 1)  # 1=line buffered, universal
                filename = filestream
            elif isinstance(filestream, RelPath):
                filename = filestream.abs_path
                rel_file = filestream
                f = file(filename, "rU", 1)  # 1=line buffered, universal
            else:
                f = filestream
                filename = "<unknown stream>"

            state = _State(f, filename, rel_file)
            self._ParseStream(state)
            result = state.Close()
        except IOError:
            if f and f != filestream:
                f.close()
            self._log.Exception("Read-error for %s" % filestream)
        return result

    def RenderStringToHtml(self, source):
        """
        Renders an Izu source to HTML.
        This is an utility wrapper that actually calls RenderFileToHtml.
        """
        f = StringIO(source)
        return self.RenderFileToHtml(f)

    def ParseFirstLine(self, source):
        """
        Parses the *first* line of a string -- the string is actual content,
        not a filename. It returns any Izu tags found on the line.

        This is mostly an utility method to parse izu tags embedded in the
        first line of an HTML file.
        """
        a = source.find("\n")
        if a != -1:
            source = source[:a]
        a = source.find("\r")
        if a != -1:
            source = source[:a]
        tags, sections = self.RenderStringToHtml(source)
        return tags

    def _ParseStream(self, state):
        is_block = None
        state.SetCurrSection("en",
                             self._formatters.get("en", self._DefaultSection))

        while not state.EndOfFile():
            line = state.ReadLine()
            if line is None:
                break
            # A backslash at the end of a line means the line must be merged
            # with the next one. This is useful to split tags on several lines.
            while line.endswith("\\"):
                line = line[:-1]
                temp = state.ReadLine()
                if not temp is None:
                    line += temp

            is_block, line = self._ParseEscapeBlock(is_block, state, line)
            if not is_block:
                self._ParseLine(state, line)
        # end of file reached

    def _ParseEscapeBlock(self, is_block, state, line):
        """
        Parses one line of the input stream and detect blocks based on 3
        rules:
        - blocks completely held in the same line.
        - opened blocks ending on this line.
        - new blocks opened on this line.

        Input/Output:
        - is_block (string): Non-empty if there's currently a block opened,
          in which case the string is the key value for the _escape_block
          map. The map points to the method to be called to handle the line
          inside the escaped block.
        """
        # First take care of the case of a block that opens and closes on the same line
        while line:
            m = self._RE_PEB_BLOCK_SAME_LINE.match(line)
            if not m:
                break
            start = m.group("start")
            line  = m.group("end")
            name  = m.group("name")
            body  = m.group("body")
            if start:
                self._ParseLine(state, start)
            if body:
                self._escape_block[name](state, body)

        # Now handle the case of a block that gets closed and another one opened
        # on the line...
        if is_block:
            m = self._RE_PEB_BLOCK_CLOSE.match(line)
            if m:
                # A block is being closed.
                body  = m.group("body")
                if body:
                    self._escape_block[is_block](state, body)
                is_block = None
                line = m.group("line") or ""
            else:
                # We're still in a block and it's not being closed, process line.
                self._escape_block[is_block](state, line)

        if not is_block:
            m = self._RE_PEB_BLOCK_OPEN.match(line)
            if m:
                # A block has been opened, just use the start of the line
                start  = m.group("start")
                name  = m.group("name")
                body  = m.group("body")

                is_block = name
                line = ""

                if start:
                    self._ParseLine(state, start)
                if body:
                    self._escape_block[name](state, body)

        return is_block, line

    _RE_PEB_BLOCK_SAME_LINE = re.compile(r"(?P<start>(?:^|.*?[^\[]))\[!(?P<name>--|html:)(?P<body>.*?)--\](?P<end>.*)$")
    _RE_PEB_BLOCK_CLOSE     = re.compile(r"(?P<body>.*?)--\](?P<line>.*)$")
    _RE_PEB_BLOCK_OPEN      = re.compile(r"(?P<start>.*?(?:^|[^\[]))\[!(?P<name>--|html:)(?P<body>.*)$")

    def _EscapeComment(self, state, line):
        """
        Process an escaped line in an [!-- ... --] comment block.
        We simply drop the line.
        """
        pass

    def _EscapeRawHtml(self, state, line):
        """
        Process an escaped line in an [!html: ... --] block.

        We simply append the line as-is, non-escaped, to the current section
        without using the current section formatter.

        The line splitter (in _ParseStream) removed the line separator so
        we need to re-inject one. This is necessary for some HTML tags such
        as <pre> which are line-sensitive.
        """
        curr_section = state.CurrSection()
        state.InitSection(curr_section, "")
        state.Append(curr_section, line + "\n")


    # --- structural parsers

    def _ParseLine(self, state, line):
        """
        Parses a line, or part of a line:
        - first process all tags and strips them out
        - then splits into sections, formatting whatever is before the current section
        - finally formats whatever is left
        """
        while line is not None:
            line = self._ParseIzuTags(state, line)
            loop, line = self._ParseIzuSection(state, line)
            if loop:
                continue
            # Process according to current formatter
            state.CurrFormatter()(state, line)
            return

    def _ParseIzuTags(self, state, line):
        """
        Handles [izu:tag:value]
        """
        while line:
            m = self._RE_PARSE_IZU_TAG.match(line)
            if m:
                start = m.group("start") or ""
                end   = m.group("end") or ""
                line = start + end

                tag  = m.group("tag")
                value  = m.group("value")
                if tag:
                    self._tag_handlers.get(tag, self._DefaultTagHandler)(state, tag, value)
                else:
                    # log an error and ignore
                    self._log.Error("Invalid tag %s:%s in %s", tag, value, state.Filename())
            else:
                break
        return line

    _RE_PARSE_IZU_TAG = re.compile(r"(?P<start>(?:^|.*[^\[]))\[izu:(?P<tag>[^:\]]+):(?P<value>[^\]]*)\](?P<end>.*)$")

    def _ParseIzuSection(self, state, line):
        """
        Handles [s:section_name], allowing multiple per line.
        """
        # section. Supports multile [s:section_name] per line.
        m = self._RE_PARSE_IZU_SECTION.match(line)
        if m:
            start = m.group("start")
            line  = m.group("end")
            name  = m.group("name")

            if start:
                state.CurrFormatter()(state, start)

            if name:
                state.SetCurrSection(name,
                                     self._formatters.get(name, self._DefaultSection))
                return True, line  # loop on line
            else:
                # log an error and ignore
                self._log.Error("Invalid section name in %s", state.Filename())
        return False, line  # don't loop

    _RE_PARSE_IZU_SECTION = re.compile(r"(?P<start>(?:^|.*[^\[]))\[s:(?P<name>[^\]:]+)\](?P<end>.*)$")


    # --- section formatters
        # finally append the line to the section

    def _DefaultSection(self, state, line):
        """
        Default formatter for Izu section.
        """
        curr_section = state.CurrSection()
        state.InitSection(curr_section, "")

        # --- formatting tags
        line = self._FormatBoldItalicHtmlEmpty(line)
        line = self._FormatSimpleTags(state, line)
        line = self._FormatHtmlTags(state, line)
        line = self._FormatCenter(state, line)
        line = self._FormatLinks(state, line)
        line = self._FormatLists(state, line)

        # --- cleanup
        line = self._RemoveEscapes(line)
        line = self._ConvertAccents(line)

        # --- append to buffer
        # empty lines or line solely made of whitespace are to be treated as
        # paragraphs (<p>) and merged togethers *iif* we'll have content later
        # that is inline and we *already* had content.
        if _WS_LINE.match(line):
            state.SetSectionNeedsParagraph(curr_section, state.Section(curr_section))
            return

        # don't append <br> to <br> or <p> to <p>
        has_br = False
        if state.EndsWith(curr_section, "<br>") or state.EndsWith(curr_section, "<br/>"):
            has_br = True
            while line.startswith("<br>") or line.startswith("<br/>"):
                line = line[4:]
        has_p = False
        if state.EndsWith(curr_section, "<p>") or state.EndsWith(curr_section, "<p/>"):
            has_p = True
            while line.startswith("<p>") or line.startswith("<p/>"):
                line = line[3:]
        if not line:
            return

        if (state.SectionNeedsParagraph(curr_section) and
                not has_br and not has_p and
                not line.startswith("<p>") and
                not line.startswith("<p/>") and
                not line.startswith("<table") and
                not line.startswith("<ul>") and
                not line.startswith("<pre") and
                not line.startswith("<blockquote")):
            state.SetSectionNeedsParagraph(curr_section, False)
            state.Append(curr_section, "\n<p/>")

        if (not line.startswith("</") and
                not line.startswith("\n") and
                not state.Section(curr_section).endswith("\n")):
            state.Append(curr_section, "\n")

        # finally append the line to the section
        state.Append(curr_section, line)

    def _RemoveEscapes(self, line):
        """
        Remove escapes at the very end: double-[ which were used
        to escape normal [ tags and same for double-underscore, double-quotes
        """
        line = self._RE_RMV_ESC_DOUBLE_CHAR.sub(r"\2", line)
        return line

    _RE_RMV_ESC_DOUBLE_CHAR = re.compile(r"([_'=\[])(\1+)")

    def _ConvertAccents(self, line):
        """
        Converts accents to HTML encoding entities.
        Returns the formatted line.
        """
        for k, v in _ACCENTS_TO_HTML.iteritems():
            if k in line:
                line = line.replace(k, v)

        try:
            us = line.decode("utf-8")
            for k, v in UTF8_ACCENTS_TO_HTML.iteritems():
                if k in us:
                    us = us.replace(k, v)
            line = us
        except Exception:
            pass

        return line

    def _FormatBoldItalicHtmlEmpty(self, line):
        """
        Strips html, formats bold, italics, code, empty paragraphs.
        Returns the formatted line.
        """
        # disable HTML as early as possible: only & < >
        line = line.replace("&", "&amp;")
        line = line.replace(">", "&gt;")
        line = line.replace("<", "&lt;")

        # Bold: __word__
        line = self._RE_TAG_BOLD.sub(r"<b>\1</b>", line)

        # Italics: ''word''
        line = self._RE_TAG_ITALIC.sub(r"<i>\1</i>", line)

        # Code: ==word==
        line = self._RE_TAG_CODE.sub(r"<code>\1</code>", line)

        return line

    _RE_TAG_BOLD   = re.compile(r"(?<!_)__([^_].*?)__(?!_)")
    _RE_TAG_ITALIC = re.compile(r"(?<!')''([^'].*?)''(?!')")
    _RE_TAG_CODE   = re.compile(r"(?<!=)==([^=].*?)==(?!=)")

    def _FormatSimpleTags(self, state, line):
        """
        Formats simple tags. Currently only [br] and [p].
        An alternative line break is to use / as the last character of the line.
        Returns the formatted line.
        """
        # [br] generates an HTML <br> in-place
        # A single forward-slash at the end of a line generates a <br> too
        line = self._RE_TAG_BR.sub("<br/>", line)

        # [p] generates an HTML <p/> in-place
        line = self._RE_TAG_P.sub(r"<p/>", line)

        return line

    _RE_TAG_BR = re.compile(r"(?<!\[)\[br\]|(?<!/)/$")
    _RE_TAG_P  = re.compile(r"(?<!\[)\[p\]")

    def _FormatHtmlTags(self, state, line):
        """
        Formats simple escaped HTML tags, either of the form
        [html:foo] or [html:/foo] where the expression must be
        solely an a-z name.

        This replaces all the occurrences of any [html:foo] in the line.
        """
        m = True
        while m:
            m = self._RE_TAG_HTML.match(line)
            if m:
                before = m.group("before") or ""
                tag    = m.group("tag") or ""
                after  = m.group("after")  or ""
                line = "%s<%s>%s" % (before, tag, after)

        return line

    _RE_TAG_HTML = re.compile(r"(?P<before>.*?)(?<!\[)\[html:(?P<tag>/?[a-z]+)\](?P<after>.*)")

    def _FormatCenter(self, state, line):
        """
        Formats a [c] that centers the whole line, that is it wraps the
        text between [c] and the end of the line in a <center></center> tag.

        Since [c] formats all the _remainder_ of the line as a center block,
        only the first occurrence of [c] is used and any following one is removed.
        """
        m = self._RE_TAG_C_LINE.match(line)
        if m:
            # Replace the first occurrence of [c], centering the rest of the line
            before = m.group("before") or ""
            after  = m.group("after")  or ""

            # Any occurrence found after the first one is removed
            after = self._RE_TAG_C_ONLY.sub(r"", after)

            line = "%s<center>%s</center>" % (before, after)

        return line

    _RE_TAG_C_LINE = re.compile(r"(?P<before>.*?)(?<!\[)\[c\](?P<after>.*)")
    _RE_TAG_C_ONLY = re.compile(r"(?<!\[)\[c\]")

    def _FormatLinks(self, state, line):
        """
        Formats straight URLs and tags for URLs & images
        Returns the formatted line.
        """
        # -- format external links --

        # named image link: [title|http://blah/blah.gif,jpeg,jpg,png,svg], without [[
        line = self._RE_LINK_NAMED_IMG.sub(r'<img alt="\1" title="\1" src="\2">', line)

        # unnamed image link: [http://blah/blah.gif,jpeg,jpg,png,svg], without [[
        line = self._RE_LINK_UNNAMED_IMG.sub(r'<img src="\1">', line)

        # named link: [name|http://blah/blah], accept ftp:// and #name, without [[
        line = self._RE_LINK_NAMED_URL.sub(r'<a href="\2">\1</a>', line)

        # unnamed link: [http://blah/blah], accepts ftp:// and #name, without [[
        line = self._RE_LINK_UNNAMED_URL.sub(r'<a href="\1">\1</a>', line)

        # rig link: [name|riglink:image_glob]
        line = self._RE_RIGLINK.sub(
            lambda m: self._ReplRigLink(state, m.group(1), m.group(2)), line)

        # rig image: [name|rigimg:size:image_glob]
        line = self._ParseRigImage(state, line, accept_rest=True)

        # unformatted link: http://blah or ftp:// (link cannot contain quotes)
        # and must not be surrounded by quotes
        # and must not be surrounded by brackets
        # and must not be surrounded by < >        -- RM 20041120 fixed
        # and must not be prefixed by [] or |
        # (all these exceptions to prevent processing twice links in the form <a href="http...">http...</a>
        line = self._RE_LINK_UNFORMATTED.sub(r'\1<a href="\2">\2</a>\3', line)
        return line

    _RE_LINK_NAMED_IMG   = re.compile(r'(?<!\[)\[([^\|\[\]]+)\|((?:https?://|/)[^\] "<>]+\.(?:gif|jpe?g|png|svg))\]')
    _RE_LINK_UNNAMED_IMG = re.compile(r'(?<!\[)\[((?:https?://|/)[^\]" <>]+\.(?:gif|jpe?g|png|svg))\]')
    _RE_LINK_NAMED_URL   = re.compile(r'(?<!\[)\[([^\|\[\]]+)\|((?:https?://|ftp://|#|/)[^ "<>]+?)\]')
    _RE_LINK_UNNAMED_URL = re.compile(r'(?<!\[)\[((?:https?://|ftp://|#)[^ "<>]+?)\]')
    _RE_LINK_UNFORMATTED = re.compile(r'(^|[^\[]\]|[^"\[\]\|>])((?:https?://|ftp://)[^ "<>]+)($|[^"\]])')
    _RE_RIGLINK = re.compile(r'(?<!\[)\[([^\|\[\]]+)\|riglink:([^ "<>]+?)\]')

    def _ParseRigImage(self, state, line, accept_rest):
        """
        Parses the line for a [name|rigimg:size:image_glob] tag.

        If accept_rest is True, a sub-replacement is done so the tag can be anywhere
        in the line. If accept_rest is False, a pure match is done so the tag must
        start at the beginning of the line and anything after the tag is ignored.
        """
        if accept_rest:
            line = self._RE_RIGIMGLINK.sub(
                       lambda m: self._ReplRigImage(state, m.group(1), m.group(2), m.group(3), m.group(4), m.group(5)),
                       line)
        else:
            m = self._RE_RIGIMGLINK.match(line)
            if m:
                line = self._ReplRigImage(state, m.group(1), m.group(2), m.group(3), m.group(4), m.group(5))
        return line

    # groups:                     . first  .  1 title               2 islink.  3 size     4 img glob .    5 caption
    _RE_RIGIMGLINK = re.compile(r'(?<!\[)\[(?:([^\|\[\]]+)\|)?rigimg(link)?:(?:([^:\]]*?):)?([^"<>|]+?)(?:\|([^"<>\]]+?))?\]')

    def _ReplRigLink(self, state, title, image_glob):
        """
        Returns the replacement string for a [name|riglink:...] tag.

        The image_glob parameter must be a leaf name (no paths) and will be
        located in the current Izu's file directory or subdirectories. if possible.
        """
        result = ""
        filename = state.Filename()
        if filename and image_glob:
            choice = self._GlobGlob(os.path.dirname(filename), image_glob)
            if choice:
                subdir = os.path.dirname(choice)
                filename = os.path.basename(choice)
                album = "curr_album"
                if subdir:
                    if os.path.sep != "/":
                        subdir = subdir.replace(os.path.sep, "/")
                    album += ' + (curr_album and "/" or "") + "%s"' % urllib.quote(subdir, "/")
                result = '[[[if rig_base]]<a title="%(name)s" href="[[[raw rig_img_url %% { "rig_base": rig_base, "album": %(album)s, "img": "%(img)s" } ]]">%(name)s</a>[[[end]]'
                result %= { "name":  title,
                            "album": album,
                            "img":   urllib.quote(filename, "/") }
        return result

    def _ReplRigImage(self, state, title, is_link, size, image_glob, caption):
        """
        Returns the replacement string for a [name|rigimg:size:image_glob|caption]
        Title and size are optional and can be empty or None.

        If the glob pattern returns more than one name, only the first one is used.

        The image_glob parameter must be a leaf name (no paths) and will be
        located in the current Izu's file directory if possible.
        """
        result = ""
        filename = state.Filename()
        if filename and image_glob:
            abs_dir = os.path.dirname(filename)
            choice = self._GlobGlob(abs_dir, image_glob)
            if choice:
                rel_file = state.RelFile()
                if rel_file:
                    rel_file = rel_file.dirname().join(choice)
                subdir = os.path.dirname(choice)
                filename = os.path.basename(choice)
                result = self._ExternalGenRigUrl(rel_file, abs_dir, choice, title, is_link, size, caption)
                if not result:
                    result = self._InternalGenRigUrl(subdir, filename, title, is_link, size, caption)
        return result

    def _ExternalGenRigUrl(self, rel_file, abs_dir, filename, title, is_link, size, caption):
        """
        """
        script = self._img_gen_script
        if not script:
            return None

        rig_base = self._rig_base

        env = { "ABS_DIR":     abs_dir,
                "REL_FILE":    rel_file and rel_file.rel_curr or "",
                "IMG_NAME":    filename,
                "IS_LINK":     is_link and "1"          or "0",
                "OPT_SIZE":    size    and str(size)    or "",
                "OPT_TITLE":   title   and str(title)   or "",
                "OPT_CAPTION": caption and str(caption) or "",
                "RIG_BASE":    rig_base                 or ""
              }

        p = self._SubprocessPopen( [ script,
                                     env["ABS_DIR"],
                                     env["REL_FILE"],
                                     env["IMG_NAME"],
                                     env["IS_LINK"],
                                     env["OPT_SIZE"],
                                     env["OPT_TITLE"],
                                     env["OPT_CAPTION"],
                                     env["RIG_BASE"],
                                   ],
                             executable=None,
                             stdin=None,
                             stdout=subprocess.PIPE,
                             stderr=None,
                             shell=False,
                             cwd=None,
                             env=env,
                             universal_newlines=True)

        output = p.communicate()[0]
        if not output:
            return None
        ret = p.wait()
        if ret != 0:
            return None

        result = output
        if output.find("<img ") == -1:
            # result must be an URL. Wrap in <img> tag.
            result = '<img '
            if title:
                result += 'title="%(title)s" '
            result += 'src="%(output)s">'

        if caption and output.find("<tt>") == -1:
            result += "<br/><tt>%(caption)s</tt>"

        result %= { "output": output,
                    "title": title,
                    "caption": caption }
        return result


    def _InternalGenRigUrl(self, subdir, filename, title, is_link, size, caption):
        """
        Returns the replacement string for a [name|rigimg:size:image_glob|caption]
        based on the rig_img_url and rig_thumb_url variables.
        """
        result = '[[[if rig_base]]'
        album = "curr_album"
        if subdir:
            if os.path.sep != "/":
                subdir = subdir.replace(os.path.sep, "/")
            album += ' + (curr_album and "/" or "") + "%s"' % urllib.quote(subdir, "/")
        if is_link:
            result += '<a '
            if title:
                result += 'title="%(name)s" '
            result += 'href="[[[raw rig_img_url %% { "rig_base": rig_base, "album": %(album)s, "img": "%(img)s" } ]]">'
        result += '<img '
        if title:
            result += 'title="%(name)s" '
        result += 'src="[[[raw rig_thumb_url %% { "rig_base": rig_base, "album": %(album)s, "img": "%(img)s", "size": %(size)s } ]]">'
        if is_link:
            result += '</a>'
        if caption:
            result += "<br/><tt>%(caption)s</tt>"
        result += '[[[end]]'
        result %= { "name":    title,
                    "album":   album,
                    "img":     urllib.quote(filename, "/"),
                    "size":    size and ('"%s"' % size) or "rig_img_size",
                    "caption": caption }
        return result

    def _FormatLists(self, state, line):
        """
        Formats straight URLs and tags for URLs & images
        Returns the formatted line.
        """
        # simple one-level list: "* blah"
        line = self._RE_LIST_1.sub(r"<li>\1</li>", line)
        return line

    _RE_LIST_1 = re.compile(r"^\* (.*)$")

    def _ImagesSection(self, state, line):
        """
        Specific formatter for images section.
        When present, the [s:images] section must contain a line-separated
        list of [name|rigimg:size:image_glob] tags. Everything else is
        ignored.
        """
        curr_section = state.CurrSection()
        state.InitSection(curr_section, [])
        if line:
            line = self._FormatBoldItalicHtmlEmpty(line)
            reference = line
            line = self._ParseRigImage(state, line.strip(), accept_rest=False)
            if line and line != reference:
                line = self._RemoveEscapes(line)
                line = self._ConvertAccents(line)
                state.Append(curr_section, line)

    def _HtmlSection(self, state, line):
        """
        Specific formatter for HTML section.
        """
        curr_section = state.CurrSection()
        state.InitSection(curr_section, "")
        state.Append(curr_section, line)

    # --- tag handlers

    def _DefaultTagHandler(self, state, tag, value):
        """
        Handles unknown izu:<tag>
        """
        state.Tags()[tag] = value.strip()

    def _DateHandler(self, state, tag, value):
        """
        Handles izu:date tags
        """
        m = _DATE_YMD.match(value.strip())
        if m:
            try:
                d = datetime(int(m.group("year" ) or 0),
                             int(m.group("month") or 0),
                             int(m.group("day"  ) or 0),
                             int(m.group("hour" ) or 0),
                             int(m.group("min"  ) or 0),
                             int(m.group("sec"  ) or 0))
                state.Tags()[tag] = d
            except ValueError:
                self._log.Error("Invalid tag 'izu:%s:%s' in %s", tag, value, state.Filename())


    def _CatHandler(self, state, tag, value):
        """
        Handle izu:cat (categories) tags.
        """
        cats = state.Tags().get(tag, {})
        for cat in _IZU_CAT_SEP.split(value.lower()):
            if cat:
                cats[cat] = True
        state.Tags()[tag] = cats


    # --- Utilites

    def _GlobGlob(self, dir, pattern):
        """
        Traverse a directory tree starting at directory "dir" and using
        the glob-like pattern.

        Pattern can be composed of several path segments, each one
        being a glob-like expression. Each segment is resolved once
        going forward, thus making sure you can only select things in
        the current or sub-directories. For each glob resolved, only
        the first choice is taken into account.

        This is used by _ReplRigLink.
        """
        if isinstance(pattern, list):
            segments = pattern
        else:
            segments = pattern.split(os.path.sep)

        while segments:
            segment = segments[0]
            segments = segments[1:]

            # ignore invalid segments, the root segment (None) or
            # attemps to go backward (..)
            if not segment or segment == "." or segment == "..":
                continue

            for d in os.listdir(dir):
                leaf = os.path.basename(d)
                if fnmatch.fnmatch(leaf, segment):

                    if not segments:
                        return leaf
                    dir2 = os.path.join(dir, leaf)
                    found = self._GlobGlob(dir2, segments)
                    if found:
                        return os.path.join(leaf, found)

        return None

    def _SubprocessPopen(self, *popenargs, **kwargs):
        """
        Returns the result from subprocess.Popen().
        This is useful for mocking in unit tests.
        """
        return subprocess.Popen(*popenargs, **kwargs)

#------------------------
# Local Variables:
# mode: python
# tab-width: 4
# py-continuation-offset: 4
# py-indent-offset: 4
# sentence-end-double-space: nil
# fill-column: 79
# End:
