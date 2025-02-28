#!/usr/bin/python
# -*- coding: iso-8859-1 -*-
#-----------------------------------------------------------------------------|
"""
Unit tests for IzuParser

===> IMPORTANT: This file MUST be opened using iso-8859-1 encoding, not UTF-8. <===

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

import os
from datetime import datetime

from tests.rig_test_case import RigTestCase
from rig.parser.izu_parser import IzuParser
from rig.parser.dir_parser import RelFile

_j_ = os.path.join  # shortcut

#------------------------
class MockIzuParser(IzuParser):
    def __init__(self, log, glob, rig_base, img_gen_script):
        self._popen_args = None
        self._popen_kw = None
        self._popen_ret = None
        self._popen_out = None

        self._glob = glob or {}

        super(MockIzuParser, self).__init__(log, rig_base, img_gen_script)

    def _GlobGlob(self, dir, pattern):
        return self._glob.get(pattern, None)

    def SetPopenValues(self, retcode, stdout):
        self._popen_ret = retcode
        self._popen_out = stdout

    def GetPopenArgs(self):
        """
        Returns the positional arguments given to Popen (as a tuple)
        and the dictionary of keyword arguments.

        _popen_args is a tuple of all positional args (i.e. non keywords).
        The only positional args given to popen by the caller is the list
        of arguments strings for the process.
        In other words:
          _popen_args = tuple( list [ strings: process-args ], )

        _popen_kw is a dict { string: string }
        """
        return self._popen_args, self._popen_kw

    def _SubprocessPopen(self, *popenargs, **kwargs):
        self._popen_args = popenargs
        self._popen_kw = kwargs
        return self

    def communicate(self, input=None):
        """ Simulates subprocess.Popen.communicate """
        return [ self._popen_out, "MOCK-stderr" ]

    def wait(self):
        """ Simulates subprocess.Popen.wait """
        return self._popen_ret

#------------------------
class IzuParserTest(RigTestCase):

    def setUp(self):
        self.m = MockIzuParser(self.Log(),
                               glob=None,
                               rig_base=None,
                               img_gen_script=None)

    def tearDown(self):
        self.m = None

    def _Render(self, text, section="en"):
        tags, sections = self.m.RenderStringToHtml(text) #@UnusedVariable
        return sections.get("en", None)

    def _Tags(self, text):
        tags, sections = self.m.RenderStringToHtml(text) #@UnusedVariable
        return tags

    def testEscapes(self):
        self.assertEquals(
            '<span class="izu">\n___3___ __2__</span>',
            self._Render("____3____ ___2___"))

        self.assertEquals(
            "<span class=\"izu\">\n'''3''' ''2''</span>",
            self._Render("''''3'''' '''2'''"))

        self.assertEquals(
            '<span class="izu">\n[[[3[[[] [[2[[]</span>',
            self._Render("[[[[3[[[[] [[[2[[[]"))

    def testNoEscapeInURLs(self):
        # ___ (2+) can be present in an URL and should not espaced to be replaced
        # by n-1 underscores, as it's not a valid pattern.
        self.assertEquals(
            '<span class="izu">\n<a href="http://my___url.com">some label</a></span>',
            self._Render("[some label|http://my___url.com]"))

    def testHtmlEscapes(self):
        self.assertEquals(
            '<span class="izu">\nfoo&lt;bar&gt;zoo&amp;luu</span>',
            self._Render("foo<bar>zoo&luu"))

    def testLines(self):
        self.assertEquals(
            '<span class="izu">\n[izu-tag]\nLine 1\nLine 2\n<p/>\nLine 3</span>',
            self._Render("[izu-tag]\nLine 1\nLine 2\n\nLine 3"))

    def testLineContinuation(self):
        # By default, a tag such as bold cannot be split on several lines
        self.assertEquals('<span class="izu">\n_foo\nbar_</span>',
            self._Render("__foo\nbar__"))
        # Lines can be concatenated by using a backslash at the end, which allows
        # single-line tags to work on several lines.
        self.assertEquals('<span class="izu">\n<b>foobar</b></span>',
            self._Render("__foo\\\nbar__"))

    def testBr(self):
        # [br] generates a <br> and can be used inside a formatting tag such as __bold__
        self.assertEquals(
            '<span class="izu">\nthere is a <b>break<br/>in the line</b>\nbut not here.</span>',
            self._Render("there is a __break[br]in the line__\nbut not here."))

        # / at the end of the lines generates a <br> but it cannot be used inside a formatting tag
        self.assertEquals(
            '<span class="izu">\nthere is a _break<br/>\nin the line_\nbut not here.</span>',
            self._Render("there is a __break/\nin the line__\nbut not here."))

        # A double-slash // does not generate a <br>
        self.assertEquals(
            '<span class="izu">\nthere is no //\na break.</span>',
            self._Render("there is no //\na break."))

        # / not at the end of the line is used as-is
        self.assertEquals(
            '<span class="izu">\nthere is no /a break.</span>',
            self._Render("there is no /a break."))

    def testP(self):
        self.assertEquals(
            '<span class="izu">\nthere is a <b>break<p/>in the line</b>\nbut not here.</span>',
            self._Render("there is a __break[p]in the line__\nbut not here."))

    def testC(self):
        # C preserves whatever is before [c] and centers the rest of the line
        self.assertEquals(
            '<span class="izu">\nsome <center>line.</center></span>',
            self._Render("some [c]line."))

        # it's ok to center the full line.
        self.assertEquals(
            '<span class="izu">\n<center>some line.</center></span>',
            self._Render("[c]some line."))

        # it's ok to center an empty line.
        self.assertEquals(
            '<span class="izu">\n<center></center></span>',
            self._Render("[c]"))

        # only the first occurrence is used, others are removed (note how the
        # spacing is not normalized).
        self.assertEquals(
            '<span class="izu">\nyou can <center>only center once  in a while.</center></span>',
            self._Render("you can [c]only center once [c] in a while."))

    def testHtmlTags(self):
        # a typical use case
        self.assertEquals(
            '<span class="izu">\nsome <li>line</li>.</span>',
            self._Render("some [html:li]line[html:/li]."))

        # tags don't have to be balanced
        self.assertEquals(
            '<span class="izu">\nsome <li>line.</span>',
            self._Render("some [html:li]line."))

        # tags don't have to be valid HTML tags
        self.assertEquals(
            '<span class="izu">\nsome <whatever>line.</span>',
            self._Render("some [html:whatever]line."))

        # start of line, space are preserved
        self.assertEquals(
            '<span class="izu">\n<look> at me now.</span>',
            self._Render("[html:look] at me now."))

        # end of line
        self.assertEquals(
            '<span class="izu">\nI am so <lonely></span>',
            self._Render("I am so [html:lonely]"))

        # empty line
        self.assertEquals(
            '<span class="izu">\n<ul></span>',
            self._Render("[html:ul]"))

    def testYoutube(self):
        # Youtube tag with just an id, no size
        self.assertEquals(
            '<span class="izu">\n[[raw youtube_html % { "id": "ab_CdefgGh", "sx": youtube_sx, "sy": youtube_sy, "url_extra": "" } ]].</span>',
            self._Render("[youtube:ab_CdefgGh]."))

        # Youtube tag with an id and a pixel size
        self.assertEquals(
            '<span class="izu">\n[[raw youtube_html % { "id": "ab_CdefgGh", "sx": 640, "sy": 385, "url_extra": "" } ]].</span>',
            self._Render("[youtube:ab_CdefgGh:640x385]."))

        # Youtube tag with an id, a pixel size, and time
        self.assertEquals(
            '<span class="izu">\n[[raw youtube_html % { "id": "ab_CdefgGh", "sx": 640, "sy": 385, "url_extra": "&t=123" } ]].</span>',
            self._Render("[youtube:ab_CdefgGh:t=123:640x385]."))

    def testTable(self):
        self.assertEquals(
            '<span class="izu">\n<table border="0"  width="100%"><tr valign="top"><td  width="50px">my column 1</td><td  width="48px">my column 2</td></tr><tr valign="top"><td  width="40%">second row</td></tr></table></span>',
            self._Render("[table:begin:100%:50px]my column 1[col:48px]my column 2[row:40%]second row[table:end]"))

        self.assertEquals(
            '<span class="izu">\n<table border="0"  width="100%"><tr valign="top"><td >my column 1</td><td >my column 2</td></tr><tr valign="top"><td >second row</td></tr></table></span>',
            self._Render("[table:begin:100%]my column 1[col]my column 2[row]second row[table:end]"))

        self.assertEquals(
            '<span class="izu">\n<table border="0" ><tr valign="top"><td >my column 1</td><td >my column 2</td></tr><tr valign="top"><td >second row</td></tr></table></span>',
            self._Render("[table:begin]my column 1[col]my column 2[row]second row[table:end]"))

    def testIzuImage(self):
        self.assertEquals(
            '<span class="izu">\n<a href="http://en.wikipedia.org/wiki/Apple_iic"><img src="http://upload.wikimedia.org/wikipedia/commons/thumb/1/1b/Apple_iicb.jpg/150px-Apple_iicb.jpg"  title="Apple IIc (Wikipedia)" /></a></span>',
            self._Render("[izu:image:http://upload.wikimedia.org/wikipedia/commons/thumb/1/1b/Apple_iicb.jpg/150px-Apple_iicb.jpg|http://en.wikipedia.org/wiki/Apple_iic:Apple IIc (Wikipedia)]"))

    def testBold(self):
        self.assertEquals(
            '<span class="izu">\n<b>this</b> is <b>in bold</b> but not <b>this</b></span>',
            self._Render("__this__ is __in bold__ but not __this__"))

    def testItalics(self):
        self.assertEquals(
            '<span class="izu">\n<i>this</i> is <i>in italics</i> but not <i>this</i></span>',
            self._Render("''this'' is ''in italics'' but not ''this''"))

    def testCode(self):
        self.assertEquals(
            '<span class="izu">\n<code>this</code> is <code>in italics</code> but not <code>this</code></span>',
            self._Render("==this== is ==in italics== but not ==this=="))

    def testParagraph(self):
        self.assertEquals(
            '<span class="izu">\nLine 1,\nline 2\n<p/>\nLine 3\n<p/>\n<b>Line 4</b>\nLine 5 </span>',
            self._Render("Line 1,\nline 2\n\nLine 3\n\n\n\n\n__Line 4__\nLine 5 "))

        self.assertEquals(
            '<span class="izu">\nLine 1\n<b>line 2</b>\n<i>Line 3</i>\nLine 4\n<a href="http://link.com">Line 5</a></span>',
            self._Render("Line 1\n__line 2__\n''Line 3''\nLine 4\n[Line 5|http://link.com]\n"))

        self.assertEquals(
            '<span class="izu">\nLine 1\nLine 4<a href="http://link.com">Line 5</a></span>',
            self._Render("Line 1\nLine 4[Line 5|http://link.com]\n"))

    def testComments(self):
        # An inline comment generates a section break, so the section formatter
        # will insert a whitespace.
        self.assertEquals(
            '<span class="izu">\nfoo\nbar</span>',
            self._Render("foo[!-- blah blah --]bar"))

        self.assertEquals(
            '<span class="izu">\nfoo[!-- blah blah --]bar</span>',
            self._Render("foo[[!-- blah blah --]bar"))

        self.assertEquals(
            '<span class="izu">\nfoo</span>',
            self._Render("foo[!-- blah blah"))

        # A multi-line comment is a like a line-break, it generates a whitespace
        self.assertEquals(
            '<span class="izu">\nfoo\nbar</span>',
            self._Render("foo[!-- blah blah\nbleh bleh --]bar"))

        # Empty lines in a comment are ignored and do not generate <p> tags
        self.assertEquals(
            '<span class="izu">\nfoo\nbar</span>',
            self._Render("foo[!-- blah blah\n\n\n\nbleh bleh --]bar"))

        # You can have multiple comments on a single line
        self.assertEquals(
            '<span class="izu">\nfoo\ntoto\nbar</span>',
            self._Render("foo[!--blah1--]toto[!--blah2--]bar"))

    def testRawHtmlBlock(self):
        # The raw html block can pass anything in
        self.assertEquals(
            '<span class="izu">\nfoo<img whatever>\nand &lt;img&gt;bar</span>',
            self._Render("foo[!html:<img whatever>--]and <img>bar"))

        # You can have multiple raw html blocks on a single line
        self.assertEquals(
            '<span class="izu">\nfoo<blah1>\ntoto<blah2>\nbar</span>',
            self._Render("foo[!html:<blah1>--]toto[!html:<blah2>--]bar"))

        # Comments and HTML don't nest. Whichever comes first wins.
        self.assertEquals(
            '<span class="izu">\nfoo\nand &lt;img&gt;bar</span>',
            self._Render("foo[!--[!html:<img whatever>--]and <img>bar"))

        # A block can start on a line and end on another. Inner new lines are
        # not discarded.
        self.assertEquals(
            '<span class="izu">\nfirst line\nfoo<blah1>\n<blah2>\n\ntoto</blah2>\nbar\nend</span>',
            self._Render("first line\nfoo[!html:<blah1>\n<blah2>\n\ntoto</blah2>--]bar\nend"))

    def testSection(self):
        tags, sections = self.m.RenderStringToHtml("default section is en") #@UnusedVariable
        self.assertEquals('<span class="izu">\ndefault section is en</span>',
                          sections.get("en", None))
        self.assertEquals(None, sections.get("fr", None))

        tags, sections = self.m.RenderStringToHtml("line 1[s:en]line 2") #@UnusedVariable
        self.assertEquals('<span class="izu">\nline 1\nline 2</span>', sections.get("en", None))
        self.assertEquals(None, sections.get("fr", None))

        tags, sections = self.m.RenderStringToHtml("line 1\n[s:en]line 2") #@UnusedVariable
        self.assertEquals('<span class="izu">\nline 1\nline 2</span>', sections.get("en", None))
        self.assertEquals(None, sections.get("fr", None))

        tags, sections = self.m.RenderStringToHtml("section 1\n[s:fr]section 2") #@UnusedVariable
        self.assertEquals('<span class="izu">\nsection 1</span>', sections.get("en", None))
        self.assertEquals('<span class="izu">\nsection 2</span>', sections.get("fr", None))

        tags, sections = self.m.RenderStringToHtml("[s:en]section 1\n[s:fr]section 2") #@UnusedVariable
        self.assertEquals('<span class="izu">\nsection 1</span>', sections.get("en", None))
        self.assertEquals('<span class="izu">\nsection 2</span>', sections.get("fr", None))

        tags, sections = self.m.RenderStringToHtml("[s:fr]section 1\n[s:en]section 2") #@UnusedVariable
        self.assertEquals('<span class="izu">\nsection 1</span>', sections.get("fr", None))
        self.assertEquals('<span class="izu">\nsection 2</span>', sections.get("en", None))

        # Empty sections generate *really* nothing, not even the wrapping div (since
        # there's nothing to wrap)
        tags, sections = self.m.RenderStringToHtml("\n\n\n\n[s:en]\n\n\n\n\n[s:fr]\n\n\n\n") #@UnusedVariable
        self.assertEquals('', sections.get("en", None))
        self.assertEquals('', sections.get("fr", None))

        # A section before EOF generates nothing
        tags, sections = self.m.RenderStringToHtml("[s:fr]section 1[s:en]") #@UnusedVariable
        self.assertEquals('<span class="izu">\nsection 1</span>', sections.get("fr", None))
        self.assertEquals('', sections.get("en", None))

        tags, sections = self.m.RenderStringToHtml("[s:fr]section 1\n[s:en]") #@UnusedVariable
        self.assertEquals('<span class="izu">\nsection 1</span>', sections.get("fr", None))
        self.assertEquals('', sections.get("en", None))

        # Sole section tags do not count as a white line that would generate a <p>
        tags, sections = self.m.RenderStringToHtml("\n[s:en]\nline 1\n\n[s:fr]\nline 2\n\n") #@UnusedVariable
        self.assertEquals('<span class="izu">\nline 1</span>', sections.get("en", None))
        self.assertEquals('<span class="izu">\nline 2</span>', sections.get("fr", None))

    def testIzuTags(self):
        tags, sections = self.m.RenderStringToHtml("[izu:author:ralf]") #@UnusedVariable
        self.assertDictEquals({ "author": "ralf" }, tags)

        tags, sections = self.m.RenderStringToHtml("[izu:date:2006-05-28 17:18:05]") #@UnusedVariable
        self.assertDictEquals({ "date":  datetime(2006, 5, 28, 17, 18, 5) }, tags)

        tags, sections = self.m.RenderStringToHtml("[izu:date:2006:05:28 17:18:22]") #@UnusedVariable
        self.assertDictEquals({ "date":  datetime(2006, 5, 28, 17, 18, 22) }, tags)

        tags, sections = self.m.RenderStringToHtml("[izu:cat:videos,photos]") #@UnusedVariable
        self.assertDictEquals({ "cat":  { "videos": True, "photos": True } }, tags)

        tags, sections = self.m.RenderStringToHtml("[izu:title:some random title with : colon]") #@UnusedVariable
        self.assertDictEquals({ "title":  "some random title with : colon" }, tags)

        tags, sections = self.m.RenderStringToHtml("[izu:date:0000-00-00 00:00:00]") #@UnusedVariable
        self.assertDictEquals({}, tags)

    def testParseFirstLine(self):
        source = "<!-- [izu:author:ralf] [izu:date:2006-05-28 17:18:05] [izu:cat:foo,BAR Test] [izu:title:Video May/Mai 2006, Part 1] -->\nline 2\nline 3\n"
        tags = self.m.ParseFirstLine(source)
        self.assertDictEquals({ "title":  "Video May/Mai 2006, Part 1",
                                "author": "ralf",
                                "date":  datetime(2006, 5, 28, 17, 18, 5),
                                "cat": { "foo": True, "bar": True, "test": True } },
                               tags)

    def testConvertAccents(self):
        self.assertEquals(
              "&ccedil;a, o&ugrave; est le pr&eacute; pr&egrave;s du pr&ecirc;t?",
              self.m._ConvertAccents("�a, o� est le pr� pr�s du pr�t?"))

    def testAutoLink(self):
        self.assertEquals(
            '<span class="izu">\n<a href="http://www.example.code">http://www.example.code</a></span>',
            self._Render("http://www.example.code"))

        # Ampersand in CGI parameters is incorrectly encoded as &amp;
        self.assertEquals(
            '<span class="izu">\n<a href="http://www.example.code?a=1&amp;b=1">http://www.example.code?a=1&amp;b=1</a></span>',
            self._Render("http://www.example.code?a=1&b=1"))

        self.assertEquals(
            '<span class="izu">\n<a href="http://www.example.code">http://www.example.code</a></span>',
            self._Render("[http://www.example.code]"))

        self.assertEquals(
            '<span class="izu">\n<a href="http://www.example.code">this is the link\'s description</a></span>',
            self._Render("[this is the link's description|http://www.example.code]"))

        self.assertEquals(
            '<span class="izu">\n<a href="/my/blog/somepage.html?a=42#anchor">a relative URL</a></span>',
            self._Render("[a relative URL|/my/blog/somepage.html?a=42#anchor]"))

    def testAutoLinkImages(self):
        self.assertEquals(
            '<span class="izu">\n<img src="http://www.example.code/image.gif"></span>',
            self._Render("[http://www.example.code/image.gif]"))

        self.assertEquals(
            '<span class="izu">\n<img alt="My Image" title="My Image" src="http://www.example.code/image.gif"></span>',
            self._Render("[My Image|http://www.example.code/image.gif]"))

    def testRigLink(self):
        self.m = MockIzuParser(self.Log(),
                   glob={ "A01234*.jpg": "A01234 My Image.jpg",
                          os.path.join("pic*", "all*", "A01234*.jpg"):
                            os.path.join("pictures", "all my pix", "A01234 Some Image.jpg")
                        },
                   rig_base=None,
                   img_gen_script=None)

        self.assertEquals(
            '<span class="izu">\n[[if rig_base]]<a title="This is &amp; comment" '
            'href="[[raw rig_img_url % '
            '{ "rig_base": rig_base, "album": curr_album, "img": "A01234%20My%20Image.jpg" } ]]">'
            'This is &amp; comment</a>[[end]]</span>',
            self._Render("[This is & comment|riglink:A01234*.jpg]"))

        self.assertEquals(
            '<span class="izu">\n[[if rig_base]]<a title="This is &amp; comment" '
            'href="[[raw rig_img_url % '
            '{ "rig_base": rig_base, "album": curr_album + (curr_album and "/" or "") + "pictures/all%20my%20pix", "img": "A01234%20Some%20Image.jpg" } ]]">'
            'This is &amp; comment</a>[[end]]</span>',
            self._Render("[This is & comment|riglink:" + os.path.join("pic*", "all*", "A01234*.jpg") + "]"))

    def testRigImage(self):
        self.m = MockIzuParser(self.Log(),
                   glob={ "A01234*.jpg": "A01234 My Image.jpg",
                          "*dir/flag*.gif" : "mydir/flag1.gif",
                          "*dir\\flag*.gif" : "mydir\\flag1.gif",
                          os.path.join("pic*", "all*", "A01234*.jpg"):
                            os.path.join("pictures", "all my pix", "A01234 Some Image.jpg")
                        },
                   rig_base=None,
                   img_gen_script=None)

        # full tag with name, size and glob
        self.assertEquals(
            '<span class="izu">\n[[if rig_base]]<img title="This is &amp; comment" '
            'src="[[raw rig_thumb_url % '
            '{ "rig_base": rig_base, "album": curr_album, "img": "A01234%20My%20Image.jpg", "size": "256" } ]]">'
            '[[end]]</span>',
            self._Render("[This is & comment|rigimg:256:A01234*.jpg]"))

        # full tag with name, size and sub-dir-based glob
        self.assertEquals(
            '<span class="izu">\n[[if rig_base]]<img title="This is &amp; comment" '
            'src="[[raw rig_thumb_url % '
            '{ "rig_base": rig_base, "album": curr_album + (curr_album and "/" or "") + "pictures/all%20my%20pix", "img": "A01234%20Some%20Image.jpg", "size": "256" } ]]">'
            '[[end]]</span>',
            self._Render("[This is & comment|rigimg:256:" + os.path.join("pic*", "all*", "A01234*.jpg") + "]"))

        # tag with name and glob, no size
        self.assertEquals(
            '<span class="izu">\n[[if rig_base]]<img title="This is &amp; comment" '
            'src="[[raw rig_thumb_url % '
            '{ "rig_base": rig_base, "album": curr_album, "img": "A01234%20My%20Image.jpg", "size": rig_img_size } ]]">'
            '[[end]]</span>',
            self._Render("[This is & comment|rigimg:A01234*.jpg]"))

        # size field present but empty
        self.assertEquals(
            '<span class="izu">\n[[if rig_base]]<img title="This is &amp; comment" '
            'src="[[raw rig_thumb_url % '
            '{ "rig_base": rig_base, "album": curr_album, "img": "A01234%20My%20Image.jpg", "size": rig_img_size } ]]">'
            '[[end]]</span>',
            self._Render("[This is & comment|rigimg::A01234*.jpg]"))

        # full tag with size and glob but no name
        self.assertEquals(
            '<span class="izu">\n[[if rig_base]]<img '
            'src="[[raw rig_thumb_url % '
            '{ "rig_base": rig_base, "album": curr_album, "img": "A01234%20My%20Image.jpg", "size": "256" } ]]">'
            '[[end]]</span>',
            self._Render("[rigimg:256:A01234*.jpg]"))

        # full tag with name, size, glob and caption
        self.assertEquals(
            '<span class="izu">\n[[if rig_base]]<img title="This is &amp; comment" '
            'src="[[raw rig_thumb_url % '
            '{ "rig_base": rig_base, "album": curr_album, "img": "A01234%20My%20Image.jpg", "size": "256" } ]]">'
            '<br/><tt>This is a caption!</tt>'
            '[[end]]</span>',
            self._Render("[This is & comment|rigimg:256:A01234*.jpg|This is a caption!]"))

        # tag with name and glob, no size and caption
        self.assertEquals(
            '<span class="izu">\n[[if rig_base]]<img title="This is &amp; comment" '
            'src="[[raw rig_thumb_url % '
            '{ "rig_base": rig_base, "album": curr_album, "img": "A01234%20My%20Image.jpg", "size": rig_img_size } ]]">'
            '<br/><tt>This is a caption!</tt>'
            '[[end]]</span>',
            self._Render("[This is & comment|rigimg:A01234*.jpg|This is a caption!]"))

        # size field present but empty and caption
        self.assertEquals(
            '<span class="izu">\n[[if rig_base]]<img title="This is &amp; comment" '
            'src="[[raw rig_thumb_url % '
            '{ "rig_base": rig_base, "album": curr_album, "img": "A01234%20My%20Image.jpg", "size": rig_img_size } ]]">'
            '<br/><tt>This is a caption!</tt>'
            '[[end]]</span>',
            self._Render("[This is & comment|rigimg::A01234*.jpg|This is a caption!]"))

        # full tag with size and glob but no name and caption
        self.assertEquals(
            '<span class="izu">\n[[if rig_base]]<img '
            'src="[[raw rig_thumb_url % '
            '{ "rig_base": rig_base, "album": curr_album, "img": "A01234%20My%20Image.jpg", "size": "256" } ]]">'
            '<br/><tt>This is a caption!</tt>'
            '[[end]]</span>',
            self._Render("[rigimg:256:A01234*.jpg|This is a caption!]"))

        # Edge case. This used to be display an invalid size. Also features both
        # windows and unix path separators.
        self.assertEquals(
            '<span class="izu">\n'
            'Here: '
            '[[if rig_base]]<img title="caption" '
            'src="[[raw rig_thumb_url % '
            '{ "rig_base": rig_base, "album": curr_album + (curr_album and "/" or "") + "mydir", "img": "flag1.gif", "size": rig_img_size } ]]">'
            '[[end]]'
            ' '
            '[[if rig_base]]<img title="caption" '
            'src="[[raw rig_thumb_url % '
            '{ "rig_base": rig_base, "album": curr_album + (curr_album and "/" or "") + "mydir", "img": "flag1.gif", "size": rig_img_size } ]]">'
            '[[end]]'
            '</span>',
            self._Render("Here: [caption|rigimg:*dir/flag*.gif] [caption|rigimg:*dir" + os.path.sep + "flag*.gif]"))

    def testSectionImage(self):
        self.m = MockIzuParser(self.Log(),
                               glob={ "A01234*.jpg": "A01234 My Image.jpg" },
                               rig_base=None,
                               img_gen_script=None)
        tags, sections = self.m.RenderStringToHtml("[s:images]") #@UnusedVariable
        self.assertEquals(None, sections.get("en", None))
        self.assertEquals(None, sections.get("fr", None))
        self.assertEquals([], sections.get("images", None))

        # Ignore invalid tags
        tags, sections = self.m.RenderStringToHtml("[s:images]line 1\nline 2\n[not a rigimg tag]") #@UnusedVariable
        self.assertEquals(None, sections.get("en", None))
        self.assertEquals(None, sections.get("fr", None))
        self.assertEquals([], sections.get("images", None))

        # full tag with name, size and glob
        tags, sections = self.m.RenderStringToHtml("[s:images][This is & comment|rigimg:256:A01234*.jpg] ignore the rest") #@UnusedVariable
        self.assertListEquals(
            [ '[[if rig_base]]<img title="This is &amp; comment" '
              'src="[[raw rig_thumb_url % '
              '{ "rig_base": rig_base, "album": curr_album, "img": "A01234%20My%20Image.jpg", "size": "256" } ]]">'
              '[[end]]' ],
            sections.get("images", None))

    def testCatHandler(self):
        self.assertEquals(None,
            self._Tags("[izu:blah:]").get("cat"))

        self.assertDictEquals({},
            self._Tags("[izu:cat:]").get("cat"))

        self.assertDictEquals(
            { "foo": True, "bar": True, "foobar": True, "foob": True, "babar": True, "foobar2": True },
            self._Tags("[izu:cat:foo,bar,Foo Bar FooBar,,foob  babar\t\ffoobar2]").get("cat"))

    def testExternalGenRigUrl_errors(self):
        self.assertEquals(None, self.m._ExternalGenRigUrl(
                  rel_file=None, abs_dir=0, filename=1, title=2, is_link=False, size=4, caption=5))

        m = MockIzuParser(self.Log(),
                          glob=None,
                          rig_base="/pix/for/rig",
                          img_gen_script="/path/to/my/script")

        # error code is not 0, so nothing is done
        m.SetPopenValues(42, "blah")
        self.assertEquals(
              None,
              m._ExternalGenRigUrl(
                  rel_file=None, abs_dir="@test@", filename=1, title=2, is_link=False, size=4, caption=5))

        # output from script is empty so nothinf is done
        m.SetPopenValues(0, "")
        self.assertEquals(
              None,
              m._ExternalGenRigUrl(
                   rel_file=None, abs_dir="@test@", filename=1, title=2, is_link=False, size=4, caption=5))

    def testExternalGenRigUrl_url(self):
        m = MockIzuParser(self.Log(),
                          glob=None,
                          rig_base="/pix/for/rig",
                          img_gen_script="/path/to/my/script")
        m.SetPopenValues(0, "some-url")

        # auto generate an <img> for a url (i.e. something without "<img")
        self.assertEquals('<img title="title2" src="some-url"><br/><tt>caption5</tt>',
             m._ExternalGenRigUrl(rel_file=RelFile("some", _j_("path", "file1")),
                                  abs_dir="some/path", filename="file1", title="title2",
                                  is_link=False, size="size4", caption="caption5"))

        # we don't auto-generate <a> for an URL since the only URL is for an
        # image, not a page.
        self.assertEquals('<img title="title2" src="some-url"><br/><tt>caption5</tt>',
             m._ExternalGenRigUrl(rel_file=RelFile("some", _j_("path", "file1")),
                                  abs_dir="some/path", filename="file1", title="title2",
                                  is_link=True, size="size4", caption="caption5"))

        self.assertEquals('<img title="title2" src="some-url">',
             m._ExternalGenRigUrl(rel_file=RelFile("some", _j_("path", "file1")),
                                  abs_dir="some/path", filename="file1", title="title2",
                                  is_link=False, size="size4", caption=None))

        self.assertEquals('<img src="some-url">',
             m._ExternalGenRigUrl(rel_file=RelFile("some", _j_("path", "file1")),
                                  abs_dir="some/path", filename="file1", title=None,
                                  is_link=False, size="size4", caption=None))

    def testExternalGenRigUrl_env(self):
        m = MockIzuParser(self.Log(),
                          glob=None,
                          rig_base="/pix/for/rig",
                          img_gen_script="/path/to/my/script")
        m.SetPopenValues(0, '<a href="foo"><img src"toto"><blah></a>')

        self.assertEquals('<a href="foo"><img src"toto"><blah></a><br/><tt>caption5</tt>',
             m._ExternalGenRigUrl(rel_file=RelFile("some", _j_("path", "file1")),
                                  abs_dir="some/path", filename="file1", title="title2",
                                  is_link=False, size="size4", caption="caption5"))

        args, kw = m.GetPopenArgs()

        self.assertListEquals( ( [ "/path/to/my/script",
                                   "some/path",
                                   _j_("path", "file1"),
                                   "file1",
                                   "0", "size4", "title2", "caption5",
                                   "/pix/for/rig"
                                 ],
                               ),
                               args)
        self.assertDictEquals( { "ABS_DIR": "some/path",
                                 "IMG_NAME": "file1",
                                 "REL_FILE": _j_("path", "file1"),
                                 "IS_LINK": "0",
                                 "OPT_SIZE": "size4",
                                 "OPT_TITLE": "title2",
                                 "OPT_CAPTION": "caption5",
                                 "RIG_BASE": "/pix/for/rig",
                               },
                               kw["env"])

    def testExternalGenRigUrl_img(self):
        m = MockIzuParser(self.Log(),
                          glob=None,
                          rig_base="/pix/for/rig",
                          img_gen_script="/path/to/my/script")
        m.SetPopenValues(0, '<img src"toto"><blah>')

        self.assertEquals('<img src"toto"><blah><br/><tt>caption5</tt>',
             m._ExternalGenRigUrl(rel_file=RelFile("some", _j_("path", "file1")),
                                  abs_dir="some/path", filename="file1", title="title2",
                                  is_link=False, size="size4", caption="caption5"))

        self.assertEquals('<img src"toto"><blah><br/><tt>caption5</tt>',
             m._ExternalGenRigUrl(rel_file=RelFile("some", _j_("path", "file1")),
                                  abs_dir="some/path", filename="file1", title="title2",
                                  is_link=True, size="size4", caption="caption5"))

        self.assertEquals('<img src"toto"><blah>',
             m._ExternalGenRigUrl(rel_file=RelFile("some", _j_("path", "file1")),
                                  abs_dir="some/path", filename="file1", title=None,
                                  is_link=False, size="size4", caption=None))

    def testExternalGenRigUrl_a(self):
        m = MockIzuParser(self.Log(),
                          glob=None,
                          rig_base="/pix/for/rig",
                          img_gen_script="/path/to/my/script")
        m.SetPopenValues(0, '<a href="foo"><img src"toto"><blah></a>')

        self.assertEquals('<a href="foo"><img src"toto"><blah></a><br/><tt>caption5</tt>',
             m._ExternalGenRigUrl(rel_file=RelFile("some", _j_("path", "file1")),
                                  abs_dir="some/path", filename="file1", title="title2",
                                  is_link=False, size="size4", caption="caption5"))

        self.assertEquals('<a href="foo"><img src"toto"><blah></a><br/><tt>caption5</tt>',
             m._ExternalGenRigUrl(rel_file=RelFile("some", _j_("path", "file1")),
                                  abs_dir="some/path", filename="file1", title="title2",
                                  is_link=True, size="size4", caption="caption5"))

        self.assertEquals('<a href="foo"><img src"toto"><blah></a>',
             m._ExternalGenRigUrl(rel_file=RelFile("some", _j_("path", "file1")),
                                  abs_dir="some/path", filename="file1", title=None,
                                  is_link=False, size="size4", caption=None))

    def testExternalGenRigUrl_tt(self):
        m = MockIzuParser(self.Log(),
                          glob=None,
                          rig_base="/pix/for/rig",
                          img_gen_script="/path/to/my/script")
        m.SetPopenValues(0, '<a href="foo"><img src"toto"><blah></a><tt>boo</tt>')

        self.assertEquals('<a href="foo"><img src"toto"><blah></a><tt>boo</tt>',
             m._ExternalGenRigUrl(rel_file=RelFile("some", _j_("path", "file1")),
                                  abs_dir="some/path", filename="file1", title="title2",
                                  is_link=False, size="size4", caption="caption5"))

        m.SetPopenValues(0, '<img src"toto"><blah><tt>boo</tt>')

        self.assertEquals('<img src"toto"><blah><tt>boo</tt>',
             m._ExternalGenRigUrl(rel_file=RelFile("some", _j_("path", "file1")),
                                  abs_dir="some/path", filename="file1", title="title2",
                                  is_link=True, size="size4", caption="caption5"))



#------------------------
# Local Variables:
# mode: python
# tab-width: 4
# py-continuation-offset: 4
# py-indent-offset: 4
# sentence-end-double-space: nil
# fill-column: 79
# End:
