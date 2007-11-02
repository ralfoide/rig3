#!/usr/bin/python
#-----------------------------------------------------------------------------|
"""
Unit tests for IzuParser

Part of Rig3.
License GPL.
"""
__author__ = "ralfoide@gmail.com"

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
        

#------------------------
# Local Variables:
# mode: python
# tab-width: 4
# py-continuation-offset: 4
# py-indent-offset: 4
# sentence-end-double-space: nil
# fill-column: 79
# End:
