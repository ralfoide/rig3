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
class IzuParserTest(RigTestCase):

    def setUp(self):
        self.m = IzuParser(self.Log())

    def tearDown(self):
        self.m = None

    def _Render(self, text, section="en"):
        tags, sections = self.m.RenderStringToHtml(text)
        return sections.get("en", None)

    def testEscapes(self):
        self.assertEquals(
            '<div class="izu">___3___ __2__</div>',
            self._Render("____3____ ___2___"))

        self.assertEquals(
            "<div class=\"izu\">'''3''' ''2''</div>",
            self._Render("''''3'''' '''2'''"))

        self.assertEquals(
            '<div class="izu">[[[3[[[] [[2[[]</div>',
            self._Render("[[[[3[[[[] [[[2[[[]"))

    def testHtmlEscapes(self):
        self.assertEquals(
            '<div class="izu">foo&lt;bar&gt;zoo&luu</div>',
            self._Render("foo<bar>zoo&luu"))

    def testLines(self):
        self.assertEquals(
            '<div class="izu">[izu-tag]\nLine 1\nLine 2<p>Line 3</div>',
            self._Render("[izu-tag]\nLine 1\nLine 2\n\nLine 3"))

    def testBold(self):
        self.assertEquals(
            '<div class="izu"><b>this</b> is <b>in bold</b> but not <b>this</b></div>',
            self._Render("__this__ is __in bold__ but not __this__"))

    def testItalics(self):
        self.assertEquals(
            '<div class="izu"><i>this</i> is <i>in italics</i> but not <i>this</i></div>',
            self._Render("''this'' is ''in italics'' but not ''this''"))

    def testCode(self):
        self.assertEquals(
            '<div class="izu"><code>this</code> is <code>in italics</code> but not <code>this</code></div>',
            self._Render("==this== is ==in italics== but not ==this=="))

    def testParagraph(self):
        self.assertEquals(
            '<div class="izu">Line 1,\nline 2<p>Line 3<p><b>Line 4</b>Line 5 </div>',
            self._Render("Line 1,\nline 2\n\nLine 3\n\n\n\n\n__Line 4__\nLine 5 "))

    def testComments(self):
        self.assertEquals(
            '<div class="izu">foobar</div>',
            self._Render("foo[!-- blah blah --]bar"))

        self.assertEquals(
            '<div class="izu">foo[!-- blah blah --]bar</div>',
            self._Render("foo[[!-- blah blah --]bar"))

        self.assertEquals(
            '<div class="izu">foo</div>',
            self._Render("foo[!-- blah blah"))

        # A multi-line comment is a like a line-break, it generates a whitespace
        self.assertEquals(
            '<div class="izu">foo\nbar</div>',
            self._Render("foo[!-- blah blah\nbleh bleh --]bar"))

        # Empty lines in a comment are ignored and do not generate <p> tags
        self.assertEquals(
            '<div class="izu">foo\nbar</div>',
            self._Render("foo[!-- blah blah\n\n\n\nbleh bleh --]bar"))

    def testSection(self):
        tags, sections = self.m.RenderStringToHtml("default section is en")
        self.assertEquals('<div class="izu">default section is en</div>',
                          sections.get("en", None))
        self.assertEquals(None, sections.get("fr", None))

        tags, sections = self.m.RenderStringToHtml("line 1[s:en]line 2")
        self.assertEquals('<div class="izu">line 1\nline 2</div>', sections.get("en", None))
        self.assertEquals(None, sections.get("fr", None))

        tags, sections = self.m.RenderStringToHtml("line 1\n[s:en]line 2")
        self.assertEquals('<div class="izu">line 1\nline 2</div>', sections.get("en", None))
        self.assertEquals(None, sections.get("fr", None))

        tags, sections = self.m.RenderStringToHtml("section 1\n[s:fr]section 2")
        self.assertEquals('<div class="izu">section 1</div>', sections.get("en", None))
        self.assertEquals('<div class="izu">section 2</div>', sections.get("fr", None))

        tags, sections = self.m.RenderStringToHtml("[s:en]section 1\n[s:fr]section 2")
        self.assertEquals('<div class="izu">section 1</div>', sections.get("en", None))
        self.assertEquals('<div class="izu">section 2</div>', sections.get("fr", None))

        tags, sections = self.m.RenderStringToHtml("[s:fr]section 1\n[s:en]section 2")
        self.assertEquals('<div class="izu">section 1</div>', sections.get("fr", None))
        self.assertEquals('<div class="izu">section 2</div>', sections.get("en", None))

        # as an acceptable side effect, a section right before EOF appears as an
        # empty line so it generates a <p>
        tags, sections = self.m.RenderStringToHtml("[s:fr]section 1[s:en]")
        self.assertEquals('<div class="izu">section 1</div>', sections.get("fr", None))
        self.assertEquals('<div class="izu"><p></div>', sections.get("en", None))

        tags, sections = self.m.RenderStringToHtml("[s:fr]section 1\n[s:en]")
        self.assertEquals('<div class="izu">section 1</div>', sections.get("fr", None))
        self.assertEquals('<div class="izu"><p></div>', sections.get("en", None))
    
    def testIzuTags(self):
        tags, sections = self.m.RenderStringToHtml("[izu:author:ralf]")
        self.assertDictEquals({ "author": "ralf" }, tags)

        tags, sections = self.m.RenderStringToHtml("[izu:date:2006-05-28 17:18:05]")
        self.assertDictEquals({ "date":  datetime(2006, 5, 28, 17, 18, 5) }, tags)

        tags, sections = self.m.RenderStringToHtml("[izu:cat:videos,photos]")
        self.assertDictEquals({ "cat":  [ "videos", "photos" ] }, tags)

        tags, sections = self.m.RenderStringToHtml("[izu:title:some random title with : colon]")
        self.assertDictEquals({ "title":  "some random title with : colon" }, tags)

        tags, sections = self.m.RenderStringToHtml("[izu:date:0000-00-00 00:00:00]")
        self.assertDictEquals({}, tags)

    def testParseFirstLine(self):
        source = "<!-- [izu:author:ralf] [izu:date:2006-05-28 17:18:05] [izu:cat:] [izu:title:Video May/Mai 2006, Part 1] -->\nline 2\nline 3\n"
        tags = self.m.ParseFirstLine(source)
        self.assertDictEquals({ "title":  "Video May/Mai 2006, Part 1",
                                "author": "ralf",
                                "date":  datetime(2006, 5, 28, 17, 18, 5),
                                "cat": [] },
                               tags)

    def testAutoLink(self):
        self.assertEquals(
            '<div class="izu"><a href="http://www.example.code">http://www.example.code</a></div>',
            self._Render("http://www.example.code"))

        self.assertEquals(
            '<div class="izu"><a href="http://www.example.code">http://www.example.code</a></div>',
            self._Render("[http://www.example.code]"))

        self.assertEquals(
            '<div class="izu"><a href="http://www.example.code">this is the link\'s description</a></div>',
            self._Render("[this is the link's description|http://www.example.code]"))

    def testAutoLinkImages(self):
        self.assertEquals(
            '<div class="izu"><img src="http://www.example.code/image.gif"></div>',
            self._Render("[http://www.example.code/image.gif]"))

        self.assertEquals(
            '<div class="izu"><img alt="My Image" title="My Image" src="http://www.example.code/image.gif"></div>',
            self._Render("[My Image|http://www.example.code/image.gif]"))

    def testConvertAccents(self):
        self.assertEquals(
              "&ccedil;a, o&ugrave; est le pr&eacute; pr&egrave;s du pr&ecirc;t?",
              self.m._ConvertAccents("ça, où est le pré près du prêt?"))

#------------------------
# Local Variables:
# mode: python
# tab-width: 4
# py-continuation-offset: 4
# py-indent-offset: 4
# sentence-end-double-space: nil
# fill-column: 79
# End:
