#!/usr/bin/python
# -*- coding: iso-8859-1 -*-
#-----------------------------------------------------------------------------|
"""
Unit tests for IzuParser

Part of Rig3.
License GPL.
"""
__author__ = "ralfoide@gmail.com"

from datetime import datetime

from tests.rig_test_case import RigTestCase
from rig.parser.izu_parser import IzuParser

#------------------------
class MockIzuParser(IzuParser):
    def __init__(self, log, glob=None):
        self._glob = glob or {}
        super(MockIzuParser, self).__init__(log)

    def _GlobGlob(self, dir, pattern):
        return self._glob.get(pattern, [])
        

#------------------------
class IzuParserTest(RigTestCase):

    def setUp(self):
        self.m = MockIzuParser(self.Log())

    def tearDown(self):
        self.m = None

    def _Render(self, text, section="en"):
        tags, sections = self.m.RenderStringToHtml(text)
        return sections.get("en", None)

    def _Tags(self, text):
        tags, sections = self.m.RenderStringToHtml(text)
        return tags

    def testEscapes(self):
        self.assertEquals(
            '<div class="izu">\n___3___ __2__</div>',
            self._Render("____3____ ___2___"))

        self.assertEquals(
            "<div class=\"izu\">\n'''3''' ''2''</div>",
            self._Render("''''3'''' '''2'''"))

        self.assertEquals(
            '<div class="izu">\n[[[3[[[] [[2[[]</div>',
            self._Render("[[[[3[[[[] [[[2[[[]"))

    def testHtmlEscapes(self):
        self.assertEquals(
            '<div class="izu">\nfoo&lt;bar&gt;zoo&amp;luu</div>',
            self._Render("foo<bar>zoo&luu"))

    def testLines(self):
        self.assertEquals(
            '<div class="izu">\n[izu-tag]\nLine 1\nLine 2\n<p>\nLine 3</div>',
            self._Render("[izu-tag]\nLine 1\nLine 2\n\nLine 3"))

    def testLineContinuation(self):
        # By default, a tag such as bold cannot be split on several lines
        self.assertEquals('<div class="izu">\n_foo\nbar_</div>',
            self._Render("__foo\nbar__"))
        # Lines can be concatenated by using a backslash at the end, which allows
        # single-line tags to work on several lines.
        self.assertEquals('<div class="izu">\n<b>foobar</b></div>',
            self._Render("__foo\\\nbar__"))

    def testBr(self):
        # [br] generates a <br> and can be used inside a formatting tag such as __bold__
        self.assertEquals(
            '<div class="izu">\nthere is a <b>break<br>in the line</b>\nbut not here.</div>',
            self._Render("there is a __break[br]in the line__\nbut not here."))

        # / at the end of the lines generates a <br> but it cannot be used inside a formatting tag
        self.assertEquals(
            '<div class="izu">\nthere is a _break<br>\nin the line_\nbut not here.</div>',
            self._Render("there is a __break/\nin the line__\nbut not here."))

        # A double-slash // does not generate a <br> 
        self.assertEquals(
            '<div class="izu">\nthere is no //\na break.</div>',
            self._Render("there is no //\na break."))

        # / not at the end of the line is used as-is 
        self.assertEquals(
            '<div class="izu">\nthere is no /a break.</div>',
            self._Render("there is no /a break."))

    def testP(self):
        self.assertEquals(
            '<div class="izu">\nthere is a <b>break<p/>in the line</b>\nbut not here.</div>',
            self._Render("there is a __break[p]in the line__\nbut not here."))

    def testBold(self):
        self.assertEquals(
            '<div class="izu">\n<b>this</b> is <b>in bold</b> but not <b>this</b></div>',
            self._Render("__this__ is __in bold__ but not __this__"))

    def testItalics(self):
        self.assertEquals(
            '<div class="izu">\n<i>this</i> is <i>in italics</i> but not <i>this</i></div>',
            self._Render("''this'' is ''in italics'' but not ''this''"))

    def testCode(self):
        self.assertEquals(
            '<div class="izu">\n<code>this</code> is <code>in italics</code> but not <code>this</code></div>',
            self._Render("==this== is ==in italics== but not ==this=="))

    def testParagraph(self):
        self.assertEquals(
            '<div class="izu">\nLine 1,\nline 2\n<p>\nLine 3\n<p>\n<b>Line 4</b>\nLine 5 </div>',
            self._Render("Line 1,\nline 2\n\nLine 3\n\n\n\n\n__Line 4__\nLine 5 "))

        self.assertEquals(
            '<div class="izu">\nLine 1\n<b>line 2</b>\n<i>Line 3</i>\nLine 4\n<a href="http://link.com">Line 5</a></div>',
            self._Render("Line 1\n__line 2__\n''Line 3''\nLine 4\n[Line 5|http://link.com]\n"))

        self.assertEquals(
            '<div class="izu">\nLine 1\nLine 4<a href="http://link.com">Line 5</a></div>',
            self._Render("Line 1\nLine 4[Line 5|http://link.com]\n"))

    def testComments(self):
        # An inline comment generates a section break, so the section formatter
        # will insert a whitespace.
        self.assertEquals(
            '<div class="izu">\nfoo\nbar</div>',
            self._Render("foo[!-- blah blah --]bar"))

        self.assertEquals(
            '<div class="izu">\nfoo[!-- blah blah --]bar</div>',
            self._Render("foo[[!-- blah blah --]bar"))

        self.assertEquals(
            '<div class="izu">\nfoo</div>',
            self._Render("foo[!-- blah blah"))

        # A multi-line comment is a like a line-break, it generates a whitespace
        self.assertEquals(
            '<div class="izu">\nfoo\nbar</div>',
            self._Render("foo[!-- blah blah\nbleh bleh --]bar"))

        # Empty lines in a comment are ignored and do not generate <p> tags
        self.assertEquals(
            '<div class="izu">\nfoo\nbar</div>',
            self._Render("foo[!-- blah blah\n\n\n\nbleh bleh --]bar"))

        # You can have multiple comments on a single line
        self.assertEquals(
            '<div class="izu">\nfoo\ntoto\nbar</div>',
            self._Render("foo[!--blah1--]toto[!--blah2--]bar"))

    def testRawHtmlBlock(self):
        # The raw html block can pass anything in
        self.assertEquals(
            '<div class="izu">\nfoo<img whatever>\nand &lt;img&gt;bar</div>',
            self._Render("foo[!html:<img whatever>--]and <img>bar"))

        # You can have multiple raw html blocks on a single line
        self.assertEquals(
            '<div class="izu">\nfoo<blah1>\ntoto<blah2>\nbar</div>',
            self._Render("foo[!html:<blah1>--]toto[!html:<blah2>--]bar"))

        # Comments and HTML don't nest. Whichever comes first wins.
        self.assertEquals(
            '<div class="izu">\nfoo\nand &lt;img&gt;bar</div>',
            self._Render("foo[!--[!html:<img whatever>--]and <img>bar"))

        # A block can start on a line and end on another. Inner new lines are
        # discarded. TODO: this should be fixed, they should be passed as-is.
        self.assertEquals(
            '<div class="izu">\nfirst line\nfoo<blah1><blah2>toto</blah2>\nbar\nend</div>',
            self._Render("first line\nfoo[!html:<blah1>\n<blah2>toto</blah2>--]bar\nend"))

    def testSection(self):
        tags, sections = self.m.RenderStringToHtml("default section is en")
        self.assertEquals('<div class="izu">\ndefault section is en</div>',
                          sections.get("en", None))
        self.assertEquals(None, sections.get("fr", None))

        tags, sections = self.m.RenderStringToHtml("line 1[s:en]line 2")
        self.assertEquals('<div class="izu">\nline 1\nline 2</div>', sections.get("en", None))
        self.assertEquals(None, sections.get("fr", None))

        tags, sections = self.m.RenderStringToHtml("line 1\n[s:en]line 2")
        self.assertEquals('<div class="izu">\nline 1\nline 2</div>', sections.get("en", None))
        self.assertEquals(None, sections.get("fr", None))

        tags, sections = self.m.RenderStringToHtml("section 1\n[s:fr]section 2")
        self.assertEquals('<div class="izu">\nsection 1</div>', sections.get("en", None))
        self.assertEquals('<div class="izu">\nsection 2</div>', sections.get("fr", None))

        tags, sections = self.m.RenderStringToHtml("[s:en]section 1\n[s:fr]section 2")
        self.assertEquals('<div class="izu">\nsection 1</div>', sections.get("en", None))
        self.assertEquals('<div class="izu">\nsection 2</div>', sections.get("fr", None))

        tags, sections = self.m.RenderStringToHtml("[s:fr]section 1\n[s:en]section 2")
        self.assertEquals('<div class="izu">\nsection 1</div>', sections.get("fr", None))
        self.assertEquals('<div class="izu">\nsection 2</div>', sections.get("en", None))

        # A section before EOF generates nothing
        tags, sections = self.m.RenderStringToHtml("[s:fr]section 1[s:en]")
        self.assertEquals('<div class="izu">\nsection 1</div>', sections.get("fr", None))
        self.assertEquals('<div class="izu"></div>', sections.get("en", None))

        tags, sections = self.m.RenderStringToHtml("[s:fr]section 1\n[s:en]")
        self.assertEquals('<div class="izu">\nsection 1</div>', sections.get("fr", None))
        self.assertEquals('<div class="izu"></div>', sections.get("en", None))

        # Sole section tags do not count as a white line that would generate a <p>
        tags, sections = self.m.RenderStringToHtml("\n[s:en]\nline 1\n\n[s:fr]\nline 2\n\n")
        self.assertEquals('<div class="izu">\nline 1</div>', sections.get("en", None))
        self.assertEquals('<div class="izu">\nline 2</div>', sections.get("fr", None))

        # Empty sections generate nothing
        tags, sections = self.m.RenderStringToHtml("\n\n\n\n[s:en]\n\n\n\n\n[s:fr]\n\n\n\n")
        self.assertEquals('<div class="izu"></div>', sections.get("en", None))
        self.assertEquals('<div class="izu"></div>', sections.get("fr", None))
    
    def testIzuTags(self):
        tags, sections = self.m.RenderStringToHtml("[izu:author:ralf]")
        self.assertDictEquals({ "author": "ralf" }, tags)

        tags, sections = self.m.RenderStringToHtml("[izu:date:2006-05-28 17:18:05]")
        self.assertDictEquals({ "date":  datetime(2006, 5, 28, 17, 18, 5) }, tags)

        tags, sections = self.m.RenderStringToHtml("[izu:date:2006:05:28 17:18:22]")
        self.assertDictEquals({ "date":  datetime(2006, 5, 28, 17, 18, 22) }, tags)

        tags, sections = self.m.RenderStringToHtml("[izu:cat:videos,photos]")
        self.assertDictEquals({ "cat":  { "videos": True, "photos": True } }, tags)

        tags, sections = self.m.RenderStringToHtml("[izu:title:some random title with : colon]")
        self.assertDictEquals({ "title":  "some random title with : colon" }, tags)

        tags, sections = self.m.RenderStringToHtml("[izu:date:0000-00-00 00:00:00]")
        self.assertDictEquals({}, tags)

    def testParseFirstLine(self):
        source = "<!-- [izu:author:ralf] [izu:date:2006-05-28 17:18:05] [izu:cat:foo,BAR Test] [izu:title:Video May/Mai 2006, Part 1] -->\nline 2\nline 3\n"
        tags = self.m.ParseFirstLine(source)
        self.assertDictEquals({ "title":  "Video May/Mai 2006, Part 1",
                                "author": "ralf",
                                "date":  datetime(2006, 5, 28, 17, 18, 5),
                                "cat": { "foo": True, "bar": True, "test": True } },
                               tags)

    def testAutoLink(self):
        self.assertEquals(
            '<div class="izu">\n<a href="http://www.example.code">http://www.example.code</a></div>',
            self._Render("http://www.example.code"))

        self.assertEquals(
            '<div class="izu">\n<a href="http://www.example.code">http://www.example.code</a></div>',
            self._Render("[http://www.example.code]"))

        self.assertEquals(
            '<div class="izu">\n<a href="http://www.example.code">this is the link\'s description</a></div>',
            self._Render("[this is the link's description|http://www.example.code]"))

    def testAutoLinkImages(self):
        self.assertEquals(
            '<div class="izu">\n<img src="http://www.example.code/image.gif"></div>',
            self._Render("[http://www.example.code/image.gif]"))

        self.assertEquals(
            '<div class="izu">\n<img alt="My Image" title="My Image" src="http://www.example.code/image.gif"></div>',
            self._Render("[My Image|http://www.example.code/image.gif]"))

    def testConvertAccents(self):
        self.assertEquals(
              "&ccedil;a, o&ugrave; est le pr&eacute; pr&egrave;s du pr&ecirc;t?",
              self.m._ConvertAccents("ça, où est le pré près du prêt?"))

    def testRigLink(self):
        self.m = MockIzuParser(self.Log(),
                               glob={ "A01234*.jpg": [ "A01234 My Image.jpg" ] })
        self.assertEquals(
            '<div class="izu">\n[[if rig_base]]<a title="This is &amp; comment" '
            'href="[[raw rig_img_url % '
            '{ "rig_base": rig_base, "album": curr_album, "img": "A01234%20My%20Image.jpg" } ]]">'
            'This is &amp; comment</a>[[end]]</div>',
            self._Render("[This is & comment|riglink:A01234*.jpg]"))

    def testRigImage(self):
        self.m = MockIzuParser(self.Log(),
                               glob={ "A01234*.jpg": [ "A01234 My Image.jpg" ] })
        
        # full tag with name, size and glob
        self.assertEquals(
            '<div class="izu">\n[[if rig_base]]<img title="This is &amp; comment" '
            'src="[[raw rig_thumb_url % '
            '{ "rig_base": rig_base, "album": curr_album, "img": "A01234%20My%20Image.jpg", "size": "256" } ]]">'
            '[[end]]</div>',
            self._Render("[This is & comment|rigimg:256:A01234*.jpg]"))
        
        # tag with name and glob, no size
        self.assertEquals(
            '<div class="izu">\n[[if rig_base]]<img title="This is &amp; comment" '
            'src="[[raw rig_thumb_url % '
            '{ "rig_base": rig_base, "album": curr_album, "img": "A01234%20My%20Image.jpg", "size": rig_img_size } ]]">'
            '[[end]]</div>',
            self._Render("[This is & comment|rigimg:A01234*.jpg]"))
        
        # size field present but empty
        self.assertEquals(
            '<div class="izu">\n[[if rig_base]]<img title="This is &amp; comment" '
            'src="[[raw rig_thumb_url % '
            '{ "rig_base": rig_base, "album": curr_album, "img": "A01234%20My%20Image.jpg", "size": rig_img_size } ]]">'
            '[[end]]</div>',
            self._Render("[This is & comment|rigimg::A01234*.jpg]"))

        # full tag with size and glob but no name
        self.assertEquals(
            '<div class="izu">\n[[if rig_base]]<img '
            'src="[[raw rig_thumb_url % '
            '{ "rig_base": rig_base, "album": curr_album, "img": "A01234%20My%20Image.jpg", "size": "256" } ]]">'
            '[[end]]</div>',
            self._Render("[rigimg:256:A01234*.jpg]"))

        # full tag with name, size, glob and caption
        self.assertEquals(
            '<div class="izu">\n[[if rig_base]]<img title="This is &amp; comment" '
            'src="[[raw rig_thumb_url % '
            '{ "rig_base": rig_base, "album": curr_album, "img": "A01234%20My%20Image.jpg", "size": "256" } ]]">'
            '<br><tt>This is a caption!</tt>'
            '[[end]]</div>',
            self._Render("[This is & comment|rigimg:256:A01234*.jpg|This is a caption!]"))

        # tag with name and glob, no size and caption
        self.assertEquals(
            '<div class="izu">\n[[if rig_base]]<img title="This is &amp; comment" '
            'src="[[raw rig_thumb_url % '
            '{ "rig_base": rig_base, "album": curr_album, "img": "A01234%20My%20Image.jpg", "size": rig_img_size } ]]">'
            '<br><tt>This is a caption!</tt>'
            '[[end]]</div>',
            self._Render("[This is & comment|rigimg:A01234*.jpg|This is a caption!]"))
        
        # size field present but empty and caption
        self.assertEquals(
            '<div class="izu">\n[[if rig_base]]<img title="This is &amp; comment" '
            'src="[[raw rig_thumb_url % '
            '{ "rig_base": rig_base, "album": curr_album, "img": "A01234%20My%20Image.jpg", "size": rig_img_size } ]]">'
            '<br><tt>This is a caption!</tt>'
            '[[end]]</div>',
            self._Render("[This is & comment|rigimg::A01234*.jpg|This is a caption!]"))

        # full tag with size and glob but no name and caption
        self.assertEquals(
            '<div class="izu">\n[[if rig_base]]<img '
            'src="[[raw rig_thumb_url % '
            '{ "rig_base": rig_base, "album": curr_album, "img": "A01234%20My%20Image.jpg", "size": "256" } ]]">'
            '<br><tt>This is a caption!</tt>'
            '[[end]]</div>',
            self._Render("[rigimg:256:A01234*.jpg|This is a caption!]"))

    def testCatHandler(self):
        self.assertEquals(None,
            self._Tags("[izu:blah:]").get("cat"))

        self.assertDictEquals({},
            self._Tags("[izu:cat:]").get("cat"))

        self.assertDictEquals(
            { "foo": True, "bar": True, "foobar": True, "foob": True, "babar": True, "foobar2": True },
            self._Tags("[izu:cat:foo,bar,Foo Bar FooBar,,foob  babar\t\ffoobar2]").get("cat"))

#------------------------
# Local Variables:
# mode: python
# tab-width: 4
# py-continuation-offset: 4
# py-indent-offset: 4
# sentence-end-double-space: nil
# fill-column: 79
# End:
