#!/usr/bin/python
#-----------------------------------------------------------------------------|
"""
Unit tests for RigTestCase

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

from tests.rig_test_case import RigTestCase
from rig.empty import Empty

#------------------------
class RigTestCaseTest(RigTestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def testAssertSame(self):
        a = []
        b = []
        self.assertEquals(a, b)
        self.assertSame(a, a)
        # a and b are equal but they are not the same
        self.assertRaises(AssertionError, self.assertSame, a, b)
        # Note that atomic objects (integers, True/False) are singletons so
        # for them equality and same are not distinguisable.
        a = 1
        b = 1
        self.assertSame(a, a)
        self.assertSame(a, b)

    def testAssertSearch(self):
        # Search validate substrings into a larger string
        self.assertSearch("foo", "foobar")
        # Using a ^ anchors is equivalent to assertMatches
        self.assertSearch("^foo", "foobar")
        self.assertSearch("ba+", "foobar")
        self.assertRaises(AssertionError, self.assertSearch, "ab+", "foobar")

    def testAssertNotSearch(self):
        self.assertNotSearch("baba", "foobar")
        self.assertNotSearch("a{2,}", "foobar")
        self.assertNotSearch("^bar", "foobar")
        self.assertRaises(AssertionError, self.assertNotSearch, "foo", "foobar")

    def testAssertMatches(self):
        # Match only checks against the *beginning* of the string
        self.assertRaises(AssertionError, self.assertMatches, "bar", "foobar")
        # Using the ^ anchor is not necessary, it is implied
        self.assertMatches("^foo", "foobar")
        self.assertMatches("foo", "foobar")
        # you need the $ anchor if you want to make sure you got the full string
        self.assertMatches("fo+ba+r$", "foobar")

    def testAssertIsInstance(self):
        self.assertIsInstance(str, "string")
        self.assertIsInstance((str, list), "string")
        self.assertIsInstance(list, [ 1, 2 ])
        self.assertIsInstance(dict, { "a":1, "b":2 })
        self.assertRaises(AssertionError, self.assertIsInstance, list, "string")
        self.assertRaises(AssertionError, self.assertIsInstance, dict, [ 1, 2 ])
        self.assertRaises(AssertionError, self.assertIsInstance, str, { "a":1, "b":2 })

    def testAssertDictEquals(self):
        self.assertDictEquals({ "a":1, "b":2 }, {  "b":2, "a":1 })
        self.assertRaises(AssertionError, self.assertDictEquals, { "a":1, "b":2 }, {  "b":2 })
        self.assertRaises(AssertionError, self.assertDictEquals, { "a":1, "b":2 }, "string")
        self.assertRaises(AssertionError, self.assertDictEquals, "string", "string")

    def testAssertListEquals(self):
        self.assertListEquals([ "a", 1, "b", 2 ], [ "a", 1, "b", 2 ])
        self.assertRaises(AssertionError, self.assertListEquals, [ "a", 1, "b", 2 ], [ "a", "b" ])
        self.assertRaises(AssertionError, self.assertListEquals, [ "a", 1, "b", 2 ], "string")
        self.assertRaises(AssertionError, self.assertListEquals, "string", "string")

    def testAssertHtmlEquals(self):
        self.assertHtmlEquals("<html>blah foo bar</html><span />",
                              "  <HTML>\n\r  blah\nfoo   bar </HTML>  <span    /> ")

    def testAssertHtmlMatches(self):
        self.assertHtmlMatches("""<div CLASS="[^"]+">blah foo bar</div><span attr='[^']+' />""",
                               """  <DIV   CLASS=\"entry\">\n\r  blah\nfoo   bar </DIV>  <span attr='foo'   /> """)
        # Using the expression from testAssertHtmlSearch, we check that assertHtmlMatches
        # matches at the beginning and thus fails if there's no match at ^
        self.assertRaises(AssertionError, self.assertHtmlMatches,
                """blah foo bar</div>""",
                """  <DIV   CLASS=\"entry\">\n\r  blah\nfoo   bar </DIV>  <span attr='foo'   /> """)

    def testAssertHtmlSearch(self):
        self.assertHtmlSearch("""blah foo bar</div>""",
                               """  <DIV   CLASS=\"entry\">\n\r  blah\nfoo   bar </DIV>  <span attr='foo'   /> """)

    def testNormalizeHtml(self):
        self.assertEquals("<html>blah foo? bar</html>(?: .*| .+)<span />",
                          self.NormalizeHtml("  <HTML>\n\r  blah\nfoo?   bar </HTML> (?:   .*| .+)  <span    /> "))

    def testHtmlToList(self):
        self.assertListEquals(
            [ '<html>Some test <b>in bold</b>',
              '<a href="foo"><i>italic</i></a>'],
            self.HtmlToList('<html>Some test <b>in bold</b><a href="foo"><i>italic</i></a>'))

#------------------------
# Local Variables:
# mode: python
# tab-width: 4
# py-continuation-offset: 4
# py-indent-offset: 4
# sentence-end-double-space: nil
# fill-column: 79
# End:
