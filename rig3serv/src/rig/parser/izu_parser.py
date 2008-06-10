#!/usr/bin/python
# -*- coding: iso-8859-1 -*-
#-----------------------------------------------------------------------------|
"""
Rig3 module: Parses Izumi files to HTML

Part of Rig3.
License GPL.
"""
__author__ = "ralfoide@gmail.com"

import re
import os
import sys
import fnmatch
import urllib
from datetime import datetime
from StringIO import StringIO

from rig.parser.utf8_accents import UTF8_ACCENTS_TO_HTML

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
    def __init__(self, _file, filename):
        self._file = _file
        self._filename = filename
        self._tags = {}
        self._sections = {}
        self._section_needs_paragraph = {}
        self._curr_section = None
        self._curr_formatter = None

    def Filename(self):
        return self._filename

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
            if v and isinstance(v, str):
                self._sections[k] = '<span class="izu">%s</span>' % v
        return self._tags, self._sections


#------------------------
class IzuParser(object):
    """
    Izumi parser.
    This class is stateless.
    """
    def __init__(self, log, settings):
        self._log = log
        self._settings = settings
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
        
        If source is a string, it is considered a path to be opened as read-only text.
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
            if isinstance(filestream, str):
                f = file(filestream, "rU", 1)  # 1=line buffered, universal
                self._filename = filestream
            else:
                f = filestream
                self._filename = "<unknown stream>"
            
            state = _State(f, self._filename)
            self._ParseStream(state)
            result = state.Close()
            self._filename = None
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
        """
        # First take care of the case of a block that opens and closes on the same line
        while line:
            m = re.match(r"(?P<start>(?:^|.*?[^\[]))\[!(?P<name>--|html:)(?P<body>.*?)--\](?P<end>.*)$", line)
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
            m = re.match("(?P<body>.*?)--\](?P<line>.*)$", line)
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
            m = re.match("(?P<start>.*?(?:^|[^\[]))\[!(?P<name>--|html:)(?P<body>.*)$", line)
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

    def _EscapeComment(self, state, line):
        """
        Process an escaped line in an [!-- ... --] comment block.
        We simply drop the line.
        """
        pass

    def _EscapeRawHtml(self, state, line):
        """
        Process an escaped line in an [!html: ... --] block.
        We simply appending the line as-is, unescaped, to the current section
        without using the current section formatter.
        """
        curr_section = state.CurrSection()
        state.InitSection(curr_section, "")
        state.Append(curr_section, line)

                               
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
            m = re.match("(?P<start>(?:^|.*[^\[]))\[izu:(?P<tag>[^:\]]+):(?P<value>[^\]]*)\](?P<end>.*)$", line)
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
                    self._log.Error("Invalid tag %s:%s in %s", tag, value, self._filename)
            else:
                break
        return line

    def _ParseIzuSection(self, state, line):
        """
        Handles [s:section_name], allowing multiple per line.
        """
        # section. Supports multile [s:section_name] per line.
        m = re.match(r"(?P<start>(?:^|.*[^\[]))\[s:(?P<name>[^\]:]+)\](?P<end>.*)$", line)
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
                self._log.Error("Invalid section name in %s", self._filename)
        return False, line  # don't loop


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
        if state.EndsWith(curr_section, "<br>"):
            has_br = True
            while line.startswith("<br>"):
                line = line[4:]
        has_p = False
        if state.EndsWith(curr_section, "<p>"):
            has_p = True
            while line.startswith("<p>"):
                line = line[3:]
        if not line:
            return

        if (state.SectionNeedsParagraph(curr_section) and
            not has_br and not has_p and
            not line.startswith("<p>") and
            not line.startswith("<table") and
            not line.startswith("<ul>") and
            not line.startswith("<pre") and
            not line.startswith("<blockquote")):
            state.SetSectionNeedsParagraph(curr_section, False)
            state.Append(curr_section, "\n<p>")

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
        line = re.sub(r"\[(\[+)", r"\1", line)
        line = re.sub(r"_(_+)", r"\1", line)
        line = re.sub(r"'('+)", r"\1", line)
        line = re.sub(r"=(=+)", r"\1", line)
        return line

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

        # Anecdote: I rewrote these regexp from scratch and they turn to be
        # *exactly* identical to what I wrote for Izumi 3 years ago :-)
        # Makes you put "patents obviousness" in perspective...

        # Bold: __word__
        line = re.sub(r"(^|[^_])__([^_].*?)__($|[^_])", r"\1<b>\2</b>\3", line)

        # Italics: ''word''
        line = re.sub(r"(^|[^'])''([^'].*?)''($|[^'])", r"\1<i>\2</i>\3", line)

        # Code: ==word==
        line = re.sub(r"(^|[^=])==([^=].*?)==($|[^=])", r"\1<code>\2</code>\3", line)
       
        return line

    def _FormatSimpleTags(self, state, line):
        """
        Format simple tags. Currently only [br] and [p].
        Returns the formatted line.
        """
        # [br] generates an HTML <br> in-place
        line = re.sub(r'(^|[^\[])\[br\]', r'\1<br>', line)
        
        # A single forward-slash at the end of a line generates a <br> too
        line = re.sub(r'(^|[^/])/$', r'\1<br>', line)
       
        # [p] generates an HTML <p/> in-place
        line = re.sub(r'(^|[^\[])\[p\]', r'\1<p/>', line)

        return line

    def _FormatLinks(self, state, line):
        """
        Formats straight URLs and tags for URLs & images
        Returns the formatted line.
        """
        # -- format external links --
        
        # named image link: [title|http://blah/blah.gif,jpeg,jpg,png,svg], without [[
        line = re.sub(r'(^|[^\[])\[([^\|\[\]]+)\|(https?://[^\]"<>]+\.(?:gif|jpe?g|png|svg))\]',
                      r'\1<img alt="\2" title="\2" src="\3">', line)

        # unnamed image link: [http://blah/blah.gif,jpeg,jpg,png,svg], without [[
        line = re.sub(r'(^|[^\[])\[(https?://[^\]"<>]+\.(?:gif|jpe?g|png|svg))\]',
                      r'\1<img src="\2">', line)

        # named link: [name|http://blah/blah], accept ftp:// and #name, without [[
        line = re.sub(r'(^|[^\[])\[([^\|\[\]]+)\|((?:https?://|ftp://|#)[^"<>]+?)\]',
                      r'\1<a href="\3">\2</a>', line)

        # unnamed link: [http://blah/blah], accepts ftp:// and #name, without [[
        line = re.sub(r'(^|[^\[])\[((?:https?://|ftp://|#)[^"<>]+?)\]',
                      r'\1<a href="\2">\2</a>', line)

        # rig link: [name|riglink:image_glob]
        line = re.sub(r'(^|[^\[])\[([^\|\[\]]+)\|riglink:([^"<>]+?)\]',
            lambda m: self._ReplRigLink(state, m.group(1), m.group(2), m.group(3)), line)

        # rig image: [name|rigimg:size:image_glob]
        line = self._ParseRigImage(state, line, accept_rest=True)

        # unformated link: http://blah or ftp:// (link cannot contain quotes)
        # and must not be surrounded by quotes
        # and must not be surrounded by brackets
        # and must not be surrounded by < >        -- RM 20041120 fixed
        # and must not be prefixed by [] or |
        # (all these exceptions to prevent processing twice links in the form <a href="http...">http...</a>
        line = re.sub(r'(^|[^\[]\]|[^"\[\]\|>])((?:https?://|ftp://)[^ "<]+)($|[^"\]])',
                      r'\1<a href="\2">\2</a>\3', line)
        return line

    def _ParseRigImage(self, state, line, accept_rest):
        """
        Parses the line for a [name|rigimg:size:image_glob] tag.
        
        If accept_rest is True, a sub-replacement is done so the tag can be anywhere
        in the line. If accept_rest is False, a pure match is done so the tag must
        start at the beginning of the line and anything after the tag is ignored.
        """
        # griups:        1 first    .  2 title               3 islink.  4 size     5 img glob .    6 caption
        r = re.compile(r'(^|[^\[])\[(?:([^\|\[\]]+)\|)?rigimg(link)?:(?:([^:]*?):)?([^"<>|]+?)(?:\|([^"<>]+?))?\]')
        if accept_rest:
            line = r.sub(lambda m: self._ReplRigImage(state, m.group(1), m.group(2), m.group(3), m.group(4), m.group(5), m.group(6)), line)
        else:
            m = r.match(line)
            if m:
                line = self._ReplRigImage(state, m.group(1), m.group(2), m.group(3), m.group(4), m.group(5), m.group(6))
        return line

    def _ReplRigLink(self, state, first, title, image_glob):
        """
        Returns the replacement string for a [name|riglink:...] tag.
        
        The image_glob parameter must be a leaf name (no paths) and will be
        located in the current Izu's file directory if possible.
        """
        result = ""
        filename = state.Filename()
        if filename and image_glob:
            choices = self._GlobGlob(os.path.dirname(filename), image_glob)
            if choices:
                result = '[[[if rig_base]]<a title="%(name)s" href="[[[raw rig_img_url %% { "rig_base": rig_base, "album": curr_album, "img": "%(img)s" } ]]">%(name)s</a>[[[end]]'
                result %= { "name": title, 
                            "img": urllib.quote(choices[0], "/") }
        return first + result

    def _ReplRigImage(self, state, first, title, is_link, size, image_glob, caption):
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
            choices = self._GlobGlob(os.path.dirname(filename), image_glob)
            if choices:
                result = '[[[if rig_base]]'
                if is_link:
                    result += '<a '
                    if title:
                        result += 'title="%(name)s" '
                    result += 'href="[[[raw rig_img_url %% { "rig_base": rig_base, "album": curr_album, "img": "%(img)s" } ]]">'
                result += '<img '
                if title:
                    result += 'title="%(name)s" '
                result += 'src="[[[raw rig_thumb_url %% { "rig_base": rig_base, "album": curr_album, "img": "%(img)s", "size": %(size)s } ]]">'
                if is_link:
                    result += '</a>'
                if caption:
                    result += "<br><tt>%(caption)s</tt>"
                result += '[[[end]]'
                result %= { "name": title,
                            "img": urllib.quote(choices[0], "/"),
                            "size": size and ('"%s"' % size) or "rig_img_size",
                            "caption": caption }
        return first + result

    def _FormatLists(self, state, line):
        """
        Formats straight URLs and tags for URLs & images
        Returns the formatted line.
        """
        # simple one-level list: "* blah"
        line = re.sub(r'^\* (.*)$',
                      r'<li>\1</li>', line)        
        return line

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
                self._log.Error("Invalid tag 'izu:%s:%s' in %s", tag, value, self._filename)


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
        Similar to a glob.glob but works by listing the given directory
        and applying the pattern *only* to the basename (aka leaf name).
        
        This is used by _ReplRigLink.
        """
        result = []
        for d in os.listdir(dir):
            leaf = os.path.basename(d)
            if fnmatch.fnmatch(leaf, pattern):
                result.append(leaf)
        return result


#------------------------
# Local Variables:
# mode: python
# tab-width: 4
# py-continuation-offset: 4
# py-indent-offset: 4
# sentence-end-double-space: nil
# fill-column: 79
# End:
